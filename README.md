# PyUtility

PyUtility is a Windows desktop utility and monitoring application built with Python and PyQt6. It provides an overview of system health, performance, hardware state, network status, installation tools, and maintenance actions in a modern dark-themed dashboard.

## Features

- CPU, GPU, RAM, and process monitoring
- System diagnostics and health overview
- Network status, Wi‑Fi information, and connection details
- Speed test and connection monitoring support
- Backup, startup, logs, drivers, and device tools
- Security and maintenance views
- AI-assisted diagnosis panel and history tracking
- Windows administration utilities and installer support

## Project status

This project is designed primarily for Windows systems and uses Windows-specific APIs and PowerShell-based actions where needed.

## Requirements

- Python 3.10+
- PyQt6
- psutil
- requests
- GPUtil

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running the application

From the project root:

```bash
python main.py
```

If the app needs elevated privileges for some Windows operations, it can request administrator rights automatically when launched on Windows.

## Project structure

```text
pyutility/
├── main.py                  # Application entry point
├── backend.py               # System monitoring and Windows helpers
├── diagnostics.py           # Diagnostic engine and history collection
├── requirements.txt         # Python dependencies
├── setup.py                 # cx_Freeze packaging configuration
├── gui/                     # UI themes, widgets, and shared helpers
├── tabs/                    # Individual application tabs
├── tests/                   # Automated tests
├── build/                   # Build artifacts
├── compiled/                # Frozen app assets
└── README.md                # Project documentation
```

## Main tabs

- Dashboard
- CPU
- GPU
- Processes
- System
- Network
- Wi‑Fi
- Startup
- Security
- Backup
- Logs
- Drivers
- Devices
- Diagnosis
- AI Assistant
- Install
- Maintenance

## Testing

Run the project tests with:

```bash
python -m unittest discover -s tests
```

If you want a quick validation of syntax across the codebase:

```bash
python -m compileall .
```

## Notes

- The app is optimized for the Windows desktop environment.
- Some actions may require administrator permissions.
- The interface is intentionally styled as a dark desktop monitor dashboard.

## License

This project is provided as-is for local use and development. If you plan to distribute or package it, review the licensing of any bundled libraries and assets before publication.
