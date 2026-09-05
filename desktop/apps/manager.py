"""Install GTK imports and CLI styling, and synchronize GTK with theme changes."""
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ASSETS = Path(__file__).resolve().parent
EXTERNAL_FILES = [".config/gtk-3.0/gtk.css", ".config/gtk-4.0/gtk.css", ".bashrc",
                  ".config/foot/foot.ini", ".config/kitty/kitty.conf",
                  ".config/ghostty/config", ".config/alacritty/alacritty.toml"]


def write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o644
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=".funk-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def managed_prefix(original, block, label):
    begin, end = f"/* FUNK MASTER {label} BEGIN */", f"/* FUNK MASTER {label} END */"
    pattern = re.compile(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", re.S)
    return f"{begin}\n{block}\n{end}\n" + pattern.sub("", original)


def set_setting(text, key, value, section=None, separator=" = "):
    """Replace one scalar, preserving the rest of the file and its comments."""
    start, stop = 0, len(text)
    if section:
        marker = re.search(r"(?m)^\[" + re.escape(section) + r"\]\s*$", text)
        if not marker:
            return text.rstrip() + f"\n\n[{section}]\n{key}{separator}{value}\n"
        start = marker.end()
        following = re.search(r"(?m)^\[", text[start:])
        stop = start + following.start() if following else len(text)
    chunk = text[start:stop]
    pattern = re.compile(r"(?m)^" + re.escape(key) + r"(?:\s*=\s*|\s+).*$")
    matches = list(pattern.finditer(chunk))
    if len(matches) > 1:
        raise ValueError(f"Ambiguous {key} setting; review the terminal config before installing.")
    replacement = key + separator + value
    chunk = pattern.sub(lambda _: replacement, chunk) if matches else chunk.rstrip() + "\n" + replacement + "\n"
    return text[:start] + chunk + text[stop:]


def sync(home=None):
    home = home or Path.home()
    assets = home / ".config/omarchy/funk-apps"
    name = home / ".local/state/omarchy/current/theme.name"
    enabled = name.exists() and name.read_text().strip() == "funk-master"
    for version in (3, 4):
        content = (assets / f"gtk{version}.css").read_text() if enabled else "/* Funk Master GTK overrides are inactive. */\n"
        target = assets / f"active-gtk{version}.css"
        if not target.exists() or target.read_text() != content:
            write(target, content)


def install(home=None, run_hook=True):
    home = home or Path.home()
    assets = home / ".config/omarchy/funk-apps"
    # Refuse ambiguous terminal configs before writing any user configuration.
    terminal_updates = {}
    for relative, key, value, section, separator in (
        ("foot/foot.ini", "font", "JetBrainsMono Nerd Font:size=11", "main", "="),
        ("kitty/kitty.conf", "font_size", "11.0", None, " "),
        ("ghostty/config", "font-size", "11", None, " = "),
        ("alacritty/alacritty.toml", "size", "11", "font", " = "),
    ):
        file = home / ".config" / relative
        if file.exists():
            terminal_updates[file] = set_setting(file.read_text(), key, value, section, separator)
    assets.mkdir(parents=True, exist_ok=True)
    for source in ASSETS.iterdir():
        if source.is_file():
            shutil.copy2(source, assets / source.name)
    sync(home)
    for version in (3, 4):
        css = home / ".config" / f"gtk-{version}.0/gtk.css"
        previous = css.read_text() if css.exists() else ""
        block = f'@import url("../omarchy/funk-apps/active-gtk{version}.css");'
        write(css, managed_prefix(previous, block, "GTK"))
    rc = home / ".bashrc"
    previous = rc.read_text() if rc.exists() else ""
    begin, end = "# FUNK MASTER APPS BEGIN", "# FUNK MASTER APPS END"
    previous = re.sub(re.escape(begin) + r".*?" + re.escape(end) + r"\n?", "", previous, flags=re.S)
    source_line = '[[ -r "$HOME/.config/omarchy/funk-apps/shell.bash" ]] && source "$HOME/.config/omarchy/funk-apps/shell.bash"'
    write(rc, previous.rstrip() + f"\n\n{begin}\n{source_line}\n{end}\n")
    for file, content in terminal_updates.items():
        write(file, content)
    if run_hook:
        subprocess.run(["omarchy", "hook", "install", "theme-set", str(assets / "60-funk-apps")], check=True)


if __name__ == "__main__":
    if sys.argv[1:] != ["sync"]:
        raise SystemExit("Usage: manager.py sync (install using the repository installer)")
    sync()
