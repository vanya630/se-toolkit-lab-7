"""LMS API client for fetching lab data and scores."""

import httpx


class LMSClientError(Exception):
    """Base exception for LMS client errors."""
    pass


class LMSConnectionError(LMSClientError):
    """Raised when backend is unreachable."""
    pass


class LMSAPIError(LMSClientError):
    """Raised when API returns an error response."""
    pass


class LMSClient:
    """Client for the Learning Management Service API."""

    def __init__(self, base_url: str, api_key: str):
        """Initialize the LMS client.

        Args:
            base_url: Base URL of the LMS API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=10.0,
        )

    def _handle_request_error(self, e: httpx.RequestError) -> None:
        """Convert httpx errors to user-friendly exceptions.
        
        Args:
            e: The httpx exception
            
        Raises:
            LMSConnectionError: For connection issues
            LMSAPIError: For HTTP error responses
        """
        if isinstance(e, httpx.ConnectError):
            raise LMSConnectionError(f"connection refused ({self.base_url}). Check that the services are running.")
        elif isinstance(e, httpx.TimeoutException):
            raise LMSConnectionError(f"timeout connecting to backend ({self.base_url})")
        elif isinstance(e, httpx.HTTPStatusError):
            raise LMSAPIError(f"HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down.")
        else:
            raise LMSConnectionError(f"{str(e)}. Check backend configuration.")

    def health_check(self) -> tuple[bool, str]:
        """Check if the backend is accessible.

        Returns:
            Tuple of (is_healthy, message)
        """
        try:
            response = self._client.get("/items/")
            response.raise_for_status()
            items = response.json()
            count = len(items) if isinstance(items, list) else 0
            return True, f"Backend is healthy. {count} items available."
        except httpx.RequestError as e:
            error_msg = str(e)
            if "connection refused" in error_msg.lower() or "connect" in error_msg.lower():
                return False, f"Backend error: connection refused ({self.base_url}). Check that the services are running."
            elif "timeout" in error_msg.lower():
                return False, f"Backend error: timeout connecting to {self.base_url}"
            else:
                return False, f"Backend error: {error_msg}"
        except httpx.HTTPStatusError as e:
            return False, f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down."
        except Exception as e:
            return False, f"Backend error: {str(e)}"

    def get_items(self) -> list[dict]:
        """Get all items (labs, tasks, etc.).

        Returns:
            List of items from the API
            
        Raises:
            LMSConnectionError: If backend is unreachable
            LMSAPIError: If API returns error
        """
        try:
            response = self._client.get("/items/")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return []  # Never reached, but satisfies type checker
        except httpx.HTTPStatusError as e:
            self._handle_request_error(e)
            return []

    def get_labs(self) -> list[dict]:
        """Get all labs.

        Returns:
            List of lab items
            
        Raises:
            LMSConnectionError: If backend is unreachable
            LMSAPIError: If API returns error
        """
        items = self.get_items()
        return [item for item in items if item.get("type") == "lab"]

    def get_pass_rates(self, lab: str) -> list[dict]:
        """Get pass rates for a specific lab.

        Args:
            lab: Lab identifier (e.g., "lab-04")
            
        Returns:
            List of pass rate records with task names and percentages
            
        Raises:
            LMSConnectionError: If backend is unreachable
            LMSAPIError: If API returns error
        """
        try:
            response = self._client.get(
                "/analytics/pass-rates",
                params={"lab": lab}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []  # Lab not found
            self._handle_request_error(e)
            return []

    def get_lab_by_title(self, title: str) -> dict | None:
        """Find a lab by its title or ID.

        Args:
            title: Lab title or ID to search for
            
        Returns:
            Lab dict if found, None otherwise
        """
        items = self.get_items()
        title_lower = title.lower()
        
        for item in items:
            if item.get("type") != "lab":
                continue
            
            # Check ID
            item_id = str(item.get("id", ""))
            if item_id == title_lower or f"lab-{item_id}" == title_lower:
                return item
            
            # Check title
            item_title = item.get("title", "").lower()
            if title_lower in item_title or item_title in title_lower:
                return item
        
        return None

    def get_scores(self, user_id: int, lab_id: int | None = None) -> list[dict]:
        """Get scores for a user.

        Args:
            user_id: User ID (Telegram chat ID for now)
            lab_id: Optional specific lab ID

        Returns:
            List of score records
        """
        # TODO: Implement actual scores endpoint
        return []
