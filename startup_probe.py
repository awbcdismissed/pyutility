import sys
import traceback

print('SCRIPT_START', flush=True)
try:
    from PyQt6.QtWidgets import QApplication
    print('QAPP_IMPORT_OK', flush=True)
    app = QApplication([])
    print('QAPP_OK', flush=True)
    import main
    print('MAIN_IMPORT_OK', flush=True)
    print('SETTINGS_PATH', main.Settings.resolve_settings_path(), flush=True)
    print('BEFORE_PRELOAD', flush=True)
    data = main.preload_initial_data()
    print('PRELOAD_OK', sorted(data.keys()), flush=True)
    print('BEFORE_WINDOW', flush=True)
    win = main.ModernMonitorApp({})
    print('WINDOW_OK', flush=True)
except Exception as exc:
    print('EXCEPTION', type(exc).__name__, str(exc), flush=True)
    traceback.print_exc(file=sys.stdout)
    raise
