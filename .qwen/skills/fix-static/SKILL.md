---
name: fix-static
description: Fix Python static analysis errors (lint, type checking, formatting). Use when the user wants to resolve type errors, lint violations, or formatting issues found by `uv run poe check`.
argument-hint: "[files...]"
---

Fix Python static analysis errors by running the project's full check pipeline and resolving each reported diagnostic.

## Steps

1. Run `uv run poe check` and capture the full output. This runs formatting, linting, and type checking in sequence.
2. Parse the diagnostics. Each diagnostic includes a rule name, file path, line number, and explanation. Diagnostics may come from the formatter (ruff format), linter (ruff check), or type checkers (ty, pyright).
3. If `$ARGUMENTS` specifies one or more file paths, filter the diagnostics to only those files. Otherwise, fix all reported errors.
4. Group diagnostics by file. Process one file at a time, reading the file before applying fixes.
5. For each diagnostic, apply the minimal code change that resolves it. Common fixes include:
   - **Formatting**: apply the formatting change the formatter expects.
   - **Lint**: fix the code pattern flagged by the rule (e.g., missing return, unused import).
   - **Type errors**: add or correct type annotations, narrow types with `isinstance` checks or `cast()`, fix wrong signatures or return types.
   - Adding `type: ignore` comments with the specific rule (e.g., `# type: ignore[arg-type]`) only when the code is correct but the checker cannot prove it.
6. After all fixes are applied, run `uv run poe check` again to verify the errors are resolved.
7. If new errors were introduced by the fixes, resolve them. Repeat until the fixed files are clean or only pre-existing errors in other files remain.

## Rules

- Prefer fixing the actual issue over silencing it. Use `type: ignore` or `noqa` only as a last resort when the code is correct but the checker cannot prove it.
- Do not change runtime behavior. Fixes must be limited to type annotations, type narrowing, casts, and code style.
- Do not add unnecessary imports. Only import typing constructs (e.g., `cast`, `TYPE_CHECKING`) when needed by a fix.
- Never introduce `Any` (from `typing`) to silence an error. `Any` disables type checking and hides the real problem. Use a concrete type, a `Union`, a `TypeVar`, or a protocol instead.
- When a diagnostic stems from a third-party library's incomplete stubs, a targeted `type: ignore[rule-name]` comment is acceptable.

## Output

Print a summary listing each fixed diagnostic: file path, line number, rule name, and a one-line description of the fix applied. End with the final check result.
