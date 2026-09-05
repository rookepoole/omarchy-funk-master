#!/usr/bin/env python3
"""Install the Funk Master desktop pack, or restore a saved installation."""
import argparse
import datetime
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

REPO = Path(__file__).resolve().parent
SLUG = "funk-master"
PLUGIN = "local.funk-master"
OLD_PLUGIN = "rookepoole.oligarchy-tax-department"
FILES = [f"themes/{SLUG}", f"plugins/{PLUGIN}", "shell.json",
         "branding/about.txt", "branding/screensaver.txt"]


def run(*args):
    result = subprocess.run(args, text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(f"{args!r} failed ({result.returncode}):\n{result.stdout}\n{result.stderr}")
    return result.stdout.strip()


def atomic_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".funk-")
    try:
        with os.fdopen(fd, "w") as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_symlink():
        destination.symlink_to(os.readlink(source))
    elif source.is_dir():
        shutil.copytree(source, destination, symlinks=True)
    else:
        shutil.copy2(source, destination)


def transformed_shell(original):
    # Work on a copy and preserve unrelated widgets, notifications, and idle settings.
    config = json.loads(json.dumps(original))
    layout = config.setdefault("bar", {}).setdefault("layout", {})
    for section in ("left", "center", "right"):
        layout[section] = [entry for entry in layout.get(section, [])
                           if entry.get("id") not in (PLUGIN, OLD_PLUGIN)]
    layout["left"].insert(1 if layout["left"] else 0, {"id": PLUGIN})
    for entries in layout.values():
        for entry in entries:
            if entry.get("id") == "omarchy.clock":
                entry["format"] = "'ON AIR' · ddd HH:mm"
    # Disable the old theme's service as well as its bar entry; retain its files.
    config["plugins"] = [p for p in config.get("plugins", []) if p.get("id") != OLD_PLUGIN]
    disabled = config.setdefault("disabledPlugins", [])
    if OLD_PLUGIN not in disabled:
        disabled.append(OLD_PLUGIN)
    config["disabledPlugins"] = [p for p in disabled if p != PLUGIN]
    return config


def snapshot(config, state, backups):
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = backups / stamp
    backup.mkdir(parents=True, mode=0o700)
    present = []
    for relative in FILES:
        source = config / relative
        if source.exists() or source.is_symlink():
            copy(source, backup / "config" / relative)
            present.append(relative)
    theme_name = (state / "current/theme.name").read_text().strip()
    background = state / "current/background"
    saver_flag = state / "toggles/screensaver-off"
    if saver_flag.exists():
        copy(saver_flag, backup / "screensaver-off")
    metadata = {"present": present, "theme": theme_name,
                "background": os.readlink(background) if background.is_symlink() else None}
    atomic_text(backup / "snapshot.json", json.dumps(metadata, indent=2) + "\n")
    return backup


def validate_session():
    run("hyprctl", "reload")
    errors = run("hyprctl", "configerrors")
    if errors:
        raise RuntimeError("Hyprland rejected the configuration:\n" + errors)


def restore(backup, config, state):
    metadata = json.loads((backup / "snapshot.json").read_text())
    # Restore files before reactivating the saved theme. No config resets.
    for relative in FILES:
        destination = config / relative
        remove(destination)
        if relative in metadata["present"]:
            copy(backup / "config" / relative, destination)
    saver_flag = state / "toggles/screensaver-off"
    remove(saver_flag)
    if (backup / "screensaver-off").exists():
        copy(backup / "screensaver-off", saver_flag)
    run("omarchy", "theme", "set", metadata["theme"])
    background = metadata.get("background")
    if background and Path(background).is_file():
        target = state / "current/background"
        remove(target)
        target.symlink_to(background)
    run("omarchy-shell", "shell", "rescanPlugins")
    validate_session()
    print(f"Restored {metadata['theme']} from {backup}")


def install(config, state, backups):
    validate_session()
    original = json.loads((config / "shell.json").read_text())
    backup = snapshot(config, state, backups)
    atomic_text(backups.parent / "latest", str(backup) + "\n")
    try:
        destination = config / "themes" / SLUG
        remove(destination)
        destination.mkdir(parents=True)
        for source in REPO.iterdir():
            if source.name == "backgrounds" or source.suffix in (".toml", ".lua", ".theme", ".rgb"):
                copy(source, destination / source.name)
        plugin = config / "plugins" / PLUGIN
        remove(plugin)
        copy(REPO / "desktop/plugin", plugin)
        for name in ("about.txt", "screensaver.txt"):
            atomic_text(config / "branding" / name, (REPO / "desktop" / name).read_text())
        # Retire the prior theme's custom saver while honoring its saved preference.
        old_saver = state.parent / "oligarchy"
        prior = old_saver / "screensaver-prior"
        if (old_saver / "screensaver-managed").exists() and prior.exists() and prior.read_text().strip() == "enabled":
            remove(state / "toggles/screensaver-off")
        atomic_text(config / "shell.json", json.dumps(transformed_shell(original), indent=2) + "\n")
        run("omarchy", "theme", "set", SLUG)
        run("omarchy-shell", "shell", "rescanPlugins")
        validate_session()
    except Exception:
        print(f"Install failed. Restoring snapshot: {backup}")
        restore(backup, config, state)
        raise
    print(f"Funk Master applied. Backup: {backup}")
    print(f"Restore: python3 {REPO / 'install.py'} restore")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "restore"))
    parser.add_argument("--backup", type=Path, help="Restore a specific snapshot instead of latest")
    args = parser.parse_args()
    config = Path.home() / ".config/omarchy"
    state = Path.home() / ".local/state/omarchy"
    if not (Path.home() / ".config/hypr/hyprland.lua").is_file():
        parser.error("This pack requires Omarchy's Lua/Quickshell generation.")
    backups = state / "funk-master/backups"
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (backups.parent / "install.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.action == "install":
            install(config, state, backups)
        else:
            latest = backups.parent / "latest"
            backup = args.backup or (Path(latest.read_text().strip()) if latest.exists() else None)
            if backup is None or backup.resolve().parent != backups.resolve():
                parser.error("No valid local Funk Master backup selected.")
            restore(backup, config, state)


if __name__ == "__main__":
    main()
