from PyQt6.QtCore import QObject, QThread, pyqtSignal


class TaskWorker(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, task):
        super().__init__()
        self.task = task

    def run(self):
        try:
            self.finished.emit(self.task())
        except Exception as exc:
            self.failed.emit(str(exc))


def start_background(owner, task, on_finished, on_failed=None):
    thread = getattr(owner, "_async_thread", None)
    if thread is not None and thread.isRunning():
        return False

    thread = QThread(owner)
    worker = TaskWorker(task)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(on_finished)
    if on_failed is not None:
        worker.failed.connect(on_failed)
    worker.finished.connect(thread.quit)
    worker.failed.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    worker.failed.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)
    thread.finished.connect(lambda: setattr(owner, "_async_thread", None))
    owner._async_thread = thread
    owner._async_worker = worker
    thread.start()
    return True
