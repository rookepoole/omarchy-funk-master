import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from desktop.apps import manager


class AppThemeTests(unittest.TestCase):
    def test_font_edit_preserves_sections(self):
        before = '[font]\nsize = 9\n[window]\nsize = 3\n'
        after = manager.set_setting(before, 'size', '11', 'font')
        self.assertEqual(after, '[font]\nsize = 11\n[window]\nsize = 3\n')
        with self.assertRaises(ValueError):
            manager.set_setting('[font]\nsize=9\nsize=10\n', 'size', '11', 'font')

    def test_install_sync_and_preservation(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = Path(temporary)
            (home / '.config/gtk-4.0').mkdir(parents=True)
            css = home / '.config/gtk-4.0/gtk.css'
            css.write_text('/* user-owned */\nbutton { font-weight: bold; }\n')
            (home / '.bashrc').write_text('alias mine="true"\n')
            theme = home / '.local/state/omarchy/current/theme.name'
            theme.parent.mkdir(parents=True)
            theme.write_text('funk-master\n')
            manager.install(home, run_hook=False)
            first = css.read_text()
            rc = (home / '.bashrc').read_text()
            self.assertIn('user-owned', first)
            manager.install(home, run_hook=False)
            self.assertEqual(css.read_text(), first)
            self.assertEqual((home / '.bashrc').read_text(), rc)
            active = home / '.config/omarchy/funk-apps/active-gtk4.css'
            self.assertIn('--view-bg-color: #211329', active.read_text())
            theme.write_text('catppuccin\n')
            manager.sync(home)
            self.assertNotIn('--view-bg-color', active.read_text())
            self.assertIn('user-owned', css.read_text())
            theme.write_text('funk-master\n')
            manager.sync(home)
            self.assertIn('--view-bg-color: #211329', active.read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
