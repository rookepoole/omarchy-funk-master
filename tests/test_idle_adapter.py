import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop.adapt_idle import adapted


class IdleAdapterTests(unittest.TestCase):
    def test_supported_upstream_and_idempotence(self):
        source = Path('/usr/share/omarchy/shell/plugins/services/idle/Service.qml').read_text()
        result = adapted(source)
        self.assertEqual(adapted(result), result)
        self.assertIn('respectInhibitors: true', result)
        self.assertIn('runProcess(lockProcess, "lock", "omarchy-system-lock")', result)
        self.assertIn('if (saver) saver.dismiss("lock")', result)
        self.assertIn('funkSaverActive()', result)
        # All native timeout definitions and timer objects remain byte-identical.
        self.assertEqual(source[source.index('  Timer {'):], result[result.index('  Timer {'):].replace(' && !funkSaverActive()', ''))

    def test_refuse_incompatible_source(self):
        with self.assertRaises(ValueError):
            adapted('import QtQuick\nItem {}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
