# AGENTS.md

This repository is a Windows desktop system monitor application built with Python and PyQt6. The entry point is `main.py`, and the backend logic lives in `backend.py`. UI sections are organized under the `tabs/` package.

## Project purpose

The app provides a dashboard for computer health monitoring, including:

- CPU, GPU, RAM, and process information
- network status and network connections
- speed testing
- history and monitoring views
- microphone-related utilities and system actions

## Key files

- `main.py`: application bootstrap, tab registration, dark theme, splash screen
- `backend.py`: system monitoring helpers and Windows-specific checks
- `tabs/`: one file per UI tab
  - `dashboard.py`
  - `cpu.py`
  - `gpu.py`
  - `processes.py`
  - `network.py`
  - `history.py`
  - `speedtest.py`
  - `mic.py`

## Architecture conventions

- Keep the UI layered: view logic should live in the tab files, while data gathering belongs in `backend.py` when possible.
- Preserve the dark theme and modern desktop styling introduced in `main.py`.
- Avoid breaking the splash screen startup flow unless the change is intentional and tested.
- Prefer small, focused edits that maintain compatibility with existing tabs and timer-based refreshes.
- Keep user-facing strings in Portuguese when the app currently uses Portuguese labels, unless the change explicitly targets an English-only workflow.

## Dependencies

This project relies on:

- PyQt6
- psutil
- requests
- speedtest-cli (when used by the speed test tab)

## Validation

Before finishing a change, validate the code with the smallest relevant check possible.

Typical checks:

- `python -m compileall .`
- `python main.py` for a manual UI smoke test when the environment supports GUI execution

## Working rules for agents

- Do not remove existing tabs or rename core setup logic without updating the app bootstrap code.
- Preserve compatibility with Windows-specific monitoring behavior.
- Keep the code readable and avoid large refactors unless the task explicitly requires them.
- If you add functionality, prefer extending the existing architecture instead of introducing a separate, disconnected system.
- When editing tabs, maintain the current data refresh pattern and avoid hard-blocking the main UI thread.

## Suggested workflow

1. Read the relevant tab file and the relevant backend helper.
2. Make the minimal code change needed to fix or extend the feature.
3. Run a targeted validation command.
4. Summarize the change and any assumptions clearly.

## Notes

This repository is a practical desktop monitoring app rather than a web app. Changes should respect desktop responsiveness, window lifecycle, and Windows-specific system access patterns.
