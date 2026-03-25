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
            # Extract host:port from base_url for cleaner error messages
            host_port = self.base_url.replace("http://", "").replace("https://", "")
            if "connection refused" in error_msg.lower() or "connect" in error_msg.lower():
                return False, f"Backend error: connection refused ({host_port}). Check that the services are running."
            elif "timeout" in error_msg.lower():
                return False, f"Backend error: timeout connecting to {host_port}"
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

    def get_scores(self, lab: str) -> list[dict]:
        """Get score distribution for a lab (4 buckets).

        Args:
            lab: Lab identifier (e.g., "lab-04")

        Returns:
            List of score bucket records
        """
        try:
            response = self._client.get(
                "/analytics/scores",
                params={"lab": lab}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            self._handle_request_error(e)
            return []

    def get_learners(self) -> list[dict]:
        """Get all enrolled learners.

        Returns:
            List of learner records
        """
        try:
            response = self._client.get("/learners/")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            self._handle_request_error(e)
            return []

    def get_timeline(self, lab: str) -> list[dict]:
        """Get submissions per day for a lab.

        Args:
            lab: Lab identifier (e.g., "lab-04")

        Returns:
            List of timeline records with date and submissions count
        """
        try:
            response = self._client.get(
                "/analytics/timeline",
                params={"lab": lab}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            self._handle_request_error(e)
            return []

    def get_groups(self, lab: str) -> list[dict]:
        """Get per-group scores and student counts for a lab.

        Args:
            lab: Lab identifier (e.g., "lab-04")

        Returns:
            List of group records with avg_score and students count
        """
        try:
            response = self._client.get(
                "/analytics/groups",
                params={"lab": lab}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            self._handle_request_error(e)
            return []

    def get_top_learners(self, lab: str, limit: int = 10) -> list[dict]:
        """Get top N learners by score for a lab.

        Args:
            lab: Lab identifier (e.g., "lab-04")
            limit: Number of top learners to return

        Returns:
            List of top learner records with avg_score and attempts
        """
        try:
            response = self._client.get(
                "/analytics/top-learners",
                params={"lab": lab, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return []
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return []
            self._handle_request_error(e)
            return []

    def get_completion_rate(self, lab: str) -> dict:
        """Get completion rate percentage for a lab.

        Args:
            lab: Lab identifier (e.g., "lab-04")

        Returns:
            Dict with completion_rate, passed, and total counts
        """
        try:
            response = self._client.get(
                "/analytics/completion-rate",
                params={"lab": lab}
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return {"completion_rate": 0.0, "passed": 0, "total": 0}
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {"completion_rate": 0.0, "passed": 0, "total": 0}
            self._handle_request_error(e)
            return {"completion_rate": 0.0, "passed": 0, "total": 0}

    def trigger_sync(self) -> dict:
        """Trigger a data sync from autochecker.

        Returns:
            Dict with sync status
        """
        try:
            response = self._client.post("/pipeline/sync")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            self._handle_request_error(e)
            return {"status": "error", "message": str(e)}
        except httpx.HTTPStatusError as e:
            self._handle_request_error(e)
            return {"status": "error", "message": str(e)}

    def get_scores_for_user(self, user_id: int, lab_id: int | None = None) -> list[dict]:
        """Get scores for a specific user.

        Args:
            user_id: User ID (Telegram chat ID for now)
            lab_id: Optional specific lab ID

        Returns:
            List of score records
        """
        # TODO: Implement actual scores endpoint
        return []
