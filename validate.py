#!/usr/bin/env python3
"""Validate palette contrast, syntax, and reversible desktop transformations."""
import json
from pathlib import Path
import re
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch
import install

ROOT = Path(__file__).resolve().parent


def luminance(color):
    channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return sum(a*b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


class DesktopChecks(unittest.TestCase):
    def test_palette_and_surfaces(self):
        colors = tomllib.loads((ROOT / 'colors.toml').read_text())
        for key in ('foreground', 'accent', 'muted', 'dark_foreground', 'red', 'yellow', 'green', 'blue', 'magenta', 'cyan'):
            self.assertGreaterEqual(contrast(colors[key], colors['background']), 4.5, key)
        for path in ROOT.glob('*.toml'):
            self.assertNotIn('{{', path.read_text())
            tomllib.loads(path.read_text())
        self.assertGreaterEqual(contrast('#D6FF62', '#57335F'), 4.5)
        print(f"Body contrast: {contrast(colors['foreground'], colors['background']):.2f}:1")

    def test_shell_merge_idempotent(self):
        original = {'idle': {'lock': 300}, 'plugins': [{'id': 'rook.notifications'}],
                    'disabledPlugins': ['omarchy.notifications'],
                    'bar': {'position': 'top', 'layout': {
                        'left': [{'id': 'omarchy.menu'}, {'id': 'market', 'watchlist': 'TEST'}],
                        'center': [{'id': install.OLD_PLUGIN}, {'id': 'omarchy.clock'}],
                        'right': [{'id': 'omarchy.network'}]}}}
        result = install.transformed_shell(original)
        self.assertEqual(result, install.transformed_shell(result))
        self.assertEqual(result['idle'], original['idle'])
        self.assertEqual(result['plugins'], original['plugins'])
        self.assertEqual(result['bar']['layout']['left'][-1], original['bar']['layout']['left'][-1])
        self.assertEqual(original['bar']['layout']['center'][0]['id'], install.OLD_PLUGIN)

    def test_snapshot_restore_files_and_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            config, state = base / 'config', base / 'state'
            install.atomic_text(config / 'shell.json', '{"old": true}\n')
            install.atomic_text(config / 'branding/about.txt', 'Old branding\n')
            install.atomic_text(state / 'current/theme.name', 'old-theme\n')
            install.atomic_text(state / 'toggles/screensaver-off', 'saved\n')
            old_wallpaper = base / 'old.png'
            old_wallpaper.write_bytes(b'original')
            (state / 'current/background').symlink_to(old_wallpaper)
            theme = config / 'themes/funk-master'
            theme.parent.mkdir(parents=True)
            theme.symlink_to(base / 'external-theme', target_is_directory=True)
            backup = install.snapshot(config, state, state / 'funk-master/backups')
            install.atomic_text(config / 'shell.json', '{"new": true}\n')
            install.remove(theme)
            install.atomic_text(theme / 'colors.toml', 'changed')
            install.atomic_text(config / 'plugins/local.funk-master/extra', 'new')
            install.remove(state / 'toggles/screensaver-off')
            with patch.object(install, 'run', return_value='') as command:
                install.restore(backup, config, state)
                self.assertIn(unittest.mock.call('omarchy', 'theme', 'set', 'old-theme'), command.call_args_list)
            self.assertEqual((config / 'shell.json').read_text(), '{"old": true}\n')
            self.assertEqual((config / 'branding/about.txt').read_text(), 'Old branding\n')
            self.assertTrue(theme.is_symlink())
            self.assertFalse((config / 'plugins/local.funk-master').exists())
            self.assertEqual((state / 'toggles/screensaver-off').read_text(), 'saved\n')
            self.assertEqual((state / 'current/background').resolve(), old_wallpaper)

    def test_syntax_and_plugin_manifest(self):
        subprocess.run(['luac', '-p', str(ROOT / 'hyprland.lua')], check=True)
        manifest = json.loads((ROOT / 'desktop/plugin/manifest.json').read_text())
        self.assertEqual(manifest['id'], install.PLUGIN)
        self.assertTrue((ROOT / 'desktop/plugin' / manifest['entryPoints']['barWidget']).is_file())
        subprocess.run(['/usr/lib/qt6/bin/qmlformat', str(ROOT / 'desktop/plugin/FunkMaster.qml')],
                       check=True, stdout=subprocess.DEVNULL)


if __name__ == '__main__':
    unittest.main(verbosity=2)
