import unittest

from backend import SystemMonitor


class TestChocolateyAdmin(unittest.TestCase):
    def test_admin_command_uses_uac_runas(self):
        command = SystemMonitor.build_admin_powershell_command('Write-Output "installing"')

        self.assertIn('Start-Process', command)
        self.assertIn('-Verb RunAs', command)
        self.assertIn('Write-Output "installing"', command)


if __name__ == '__main__':
    unittest.main()
