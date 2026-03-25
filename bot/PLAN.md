# SE Toolkit Lab 7 - Development Plan

## Overview

This document outlines the development plan for the Telegram bot that provides analytics and tracking for the Software Engineering course. The bot integrates with the LMS backend to fetch lab data, scores, and submissions, and uses LLM-powered intent routing for natural language queries.

## Architecture

The bot follows a layered architecture with clear separation of concerns:

1. **Entry Point (bot.py)**: Handles both Telegram bot startup and CLI test mode. The `--test` flag allows offline verification without Telegram connection.

2. **Handlers Layer (handlers/)**: Pure functions that take user input and return text responses. They have no dependency on Telegram, making them easily testable. Each command (`/start`, `/help`, `/health`, `/labs`, `/scores`) has its own handler module.

3. **Services Layer (services/)**: Contains API clients for external services:
   - `LMSClient`: Communicates with the backend API to fetch labs, scores, and submissions
   - `LLMClient`: Handles intent detection and natural language query answering via Qwen Code API

4. **Configuration (config.py)**: Loads environment variables from `.env.bot.secret`, providing a clean interface for accessing configuration.

## Task Breakdown



### Task 1: Scaffold (Current)
- Create project structure with handlers, services, and config
- Implement `--test` mode for offline verification
- Set up `pyproject.toml` with dependencies
- Write development plan (this document)

### Task 2: Backend Integration
- Implement actual API calls in `LMSClient`
- Connect handlers to real data from the backend
- Add error handling for network failures
- Implement health check that actually pings the backend
- Add score fetching and formatting

### Task 3: Intent Routing with LLM
- Implement natural language intent detection using `LLMClient.detect_intent()`
- Map natural language queries to appropriate handlers
- Add context-aware responses using `LLMClient.answer_query()`
- Handle edge cases (unclear intent, out-of-scope questions)

### Task 4: Deployment & Polish
- Ensure bot runs reliably on VM
- Add logging and monitoring
- Handle bot restarts gracefully
- Add comprehensive error messages
- Test all commands in both test mode and Telegram

## Testing Strategy

1. **Unit Tests**: Test handlers in isolation with mock data
2. **Test Mode**: Verify each command via `uv run bot.py --test "/command"`
3. **Integration Tests**: Test API clients against running backend
4. **Manual Testing**: Verify bot responses in Telegram

## Deployment

The bot runs on the university VM alongside the backend services:
- Environment: `.env.bot.secret` with bot token and API credentials
- Process management: `nohup` with log file for now
- LLM proxy: Qwen Code API on port 42005
- Backend: LMS API on port 42002

## Future Improvements

- Add database for user preferences
- Implement subscription notifications for score updates
- Add admin commands for instructors
- Create inline keyboard interfaces for common actions
- Add rate limiting for API calls
