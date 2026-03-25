# Task 3: Intent-Based Natural Language Routing

## Overview
This PR implements intent-based natural language routing for the SE Toolkit Lab 7 Bot. Users can now ask questions in plain text (e.g., "which lab has the worst results?") and the bot uses LLM-powered intent routing to fetch and summarize data.

## Changes

### New Files
- `bot/handlers/natural_language.py` - Handler for natural language queries

### Modified Files
- `bot/bot.py` - Integrated intent routing for plain text messages
- `bot/services/llm_client.py` - Added tool calling support with 9 backend API tools
- `bot/services/lms_client.py` - Added all required API methods
- `bot/handlers/start.py` - Added inline keyboard buttons

## Features Implemented

### P1.1 Natural Language Intent Routing
- Plain text messages are routed to LLM for intent detection
- LLM decides which tools to call based on user query
- No regex or keyword matching in routing path

### P1.2 All 9 Backend Endpoints as LLM Tools
| Tool | Endpoint | Description |
|------|----------|-------------|
| `get_items` | `GET /items/` | List of labs and tasks |
| `get_learners` | `GET /learners/` | Enrolled students and groups |
| `get_scores` | `GET /analytics/scores?lab=` | Score distribution (4 buckets) |
| `get_pass_rates` | `GET /analytics/pass-rates?lab=` | Per-task averages and attempt counts |
| `get_timeline` | `GET /analytics/timeline?lab=` | Submissions per day |
| `get_groups` | `GET /analytics/groups?lab=` | Per-group scores and student counts |
| `get_top_learners` | `GET /analytics/top-learners?lab=&limit=` | Top N learners by score |
| `get_completion_rate` | `GET /analytics/completion-rate?lab=` | Completion rate percentage |
| `trigger_sync` | `POST /pipeline/sync` | Refresh data from autochecker |

### P1.3 Inline Keyboard Buttons
Added keyboard buttons for common actions:
- 📋 Available Labs
- 💊 Health Check
- ❓ Help
- 📊 Scores (lab-04)
- 🏆 Top Students
- 📈 Lowest Pass Rate

### P1.4 Multi-Step Reasoning
- LLM can chain multiple API calls
- Example: "which lab has the lowest pass rate?" → calls `get_items` → calls `get_pass_rates` for each lab → compares results → summarizes

## How It Works

```
User: "which lab has the worst results?"
  → bot sends message + tool definitions to LLM
  → LLM decides: call get_pass_rates for each lab
  → bot executes the API calls
  → feeds results back to LLM
  → LLM summarizes
  → bot sends response
```

## Testing

### Test Mode (Single-Step Queries)
```bash
uv run bot.py --test "what labs are available"
uv run bot.py --test "show me scores for lab 4"
uv run bot.py --test "who are the top 5 students in lab 4"
```

### Test Mode (Multi-Step Queries)
```bash
uv run bot.py --test "which lab has the lowest pass rate"
uv run bot.py --test "which group is doing best in lab 3"
```

### Test Mode (Fallback Cases)
```bash
uv run bot.py --test "asdfgh"  # gibberish — helpful message
uv run bot.py --test "hello"   # greeting — friendly response
uv run bot.py --test "lab 4"   # ambiguous — clarification
```

## Acceptance Criteria

### On GitHub
- ✅ Git workflow followed (issue, branch, PR, review, merge)
- ✅ Source code contains keyboard/button setup
- ✅ Source code defines at least 9 tool/function schemas
- ✅ LLM decides which tool to call — no regex or keyword matching
- ✅ Tool results are fed back to the LLM for final answer

### On VM (requires LLM API)
- `--test "what labs are available"` returns non-empty answer
- `--test "which lab has the lowest pass rate"` mentions a specific lab
- `--test "asdfgh"` returns a helpful message, no crash

## Notes

### LLM Configuration
The bot requires LLM API configuration in `.env.bot.secret`:
```bash
LLM_API_KEY=your-qwen-api-key
LLM_API_BASE_URL=http://localhost:42005/v1
LLM_API_MODEL=coder-model
```

### Debug Mode
In `--test` mode, tool calls are logged to stderr:
```bash
$ uv run bot.py --test "which lab has the lowest pass rate"
[tool] LLM called: get_items({})
[tool] Result: 44 items
[tool] LLM called: get_pass_rates({"lab":"lab-01"})
[tool] Result: 8 tasks
...
[summary] Feeding 7 tool results back to LLM
Based on the data, Lab 02 has the lowest pass rate...
```

### Known Limitations
- Requires LLM API to be running (Qwen Code API on localhost:42005)
- Requires backend API to be running (localhost:42002)
- Token expiration: Qwen OAuth token expires every few hours
