import os
import shutil
import tempfile
import unittest

from backend import SystemMonitor


class TestTempCleanup(unittest.TestCase):
    def test_safe_remove_file_handles_locked_file_gracefully(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'locked.tmp')
            with open(path, 'w', encoding='utf-8') as handle:
                handle.write('data')

            result = SystemMonitor.safe_remove_path(path)
            self.assertTrue(result)
            self.assertFalse(os.path.exists(path))


if __name__ == '__main__':
    unittest.main()
