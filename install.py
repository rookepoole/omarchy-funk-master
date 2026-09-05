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
import getpass
import time
from desktop.adapt_idle import adapted
from desktop.apps import manager as app_theme

REPO = Path(__file__).resolve().parent
SLUG = "funk-master"
PLUGIN = "local.funk-master"
OLD_PLUGIN = "rookepoole.oligarchy-tax-department"
SAVER = "local.funk-screensavers"
IDLE_CLONE = (os.environ.get("USER") or getpass.getuser()) + ".idle"
FILES = [f"themes/{SLUG}", f"plugins/{PLUGIN}", "shell.json",
         "branding/about.txt", "branding/screensaver.txt",
         f"plugins/{SAVER}", f"plugins/{IDLE_CLONE}",
         "funk-apps", "hooks/theme-set.d/60-funk-apps"]


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
    external_present = []
    for relative in app_theme.EXTERNAL_FILES:
        source = config.parent.parent / relative
        if source.exists() or source.is_symlink():
            copy(source, backup / "external" / relative)
            external_present.append(relative)
    theme_name = (state / "current/theme.name").read_text().strip()
    background = state / "current/background"
    saver_flag = state / "toggles/screensaver-off"
    if saver_flag.exists():
        copy(saver_flag, backup / "screensaver-off")
    metadata = {"present": present, "external_present": external_present, "theme": theme_name,
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
    external_backup, external_metadata = backup, metadata
    # Older desktop snapshots predate app styling. Recover its original files
    # from the first snapshot that captured them, before removing the imports.
    if "external_present" not in metadata and (config / "funk-apps").exists():
        for candidate in sorted(backup.parent.glob("*/snapshot.json")):
            saved = json.loads(candidate.read_text())
            if "external_present" in saved:
                external_backup, external_metadata = candidate.parent, saved
                break
    # Restore files before reactivating the saved theme. No config resets.
    for relative in FILES:
        destination = config / relative
        remove(destination)
        if relative in metadata["present"]:
            copy(backup / "config" / relative, destination)
    if "external_present" in external_metadata:
        for relative in app_theme.EXTERNAL_FILES:
            destination = config.parent.parent / relative
            remove(destination)
            if relative in external_metadata["external_present"]:
                copy(external_backup / "external" / relative, destination)
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
    run("omarchy", "restart", "shell")
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
            if source.name == "backgrounds" or source.suffix in (".toml", ".lua", ".theme", ".rgb", ".conf", ".ini"):
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
        install_saver_files(config)
        app_theme.install()
        run("omarchy", "theme", "set", SLUG)
        run("omarchy", "restart", "shell")
        verify_saver_loaded()
        validate_session()
    except Exception:
        print(f"Install failed. Restoring snapshot: {backup}")
        restore(backup, config, state)
        raise
    print(f"Funk Master applied. Backup: {backup}")
    print(f"Restore: python3 {REPO / 'install.py'} restore")


def install_saver_files(config):
    upstream = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy")) / "shell/plugins/services/idle/Service.qml"
    clone = config / "plugins" / IDLE_CLONE
    # Validate compatibility before asking Omarchy to create and activate a clone.
    source = (clone / "Service.qml").read_text() if clone.exists() else upstream.read_text()
    updated = adapted(source)
    if not clone.exists():
        run("omarchy", "plugin", "clone", "omarchy.idle")
    else:
        manifest = json.loads((clone / "manifest.json").read_text())
        if manifest.get("omarchy", {}).get("clonedFrom") != "omarchy.idle":
            raise RuntimeError("Existing idle plugin is not an Omarchy clone; refusing to overwrite it.")
    destination = config / "plugins" / SAVER
    remove(destination)
    copy(REPO / "desktop/screensavers", destination)
    atomic_text(clone / "Service.qml", updated)
    shell = json.loads((config / "shell.json").read_text())
    plugins = shell.setdefault("plugins", [])
    for plugin_id in (SAVER, IDLE_CLONE):
        if not any(p.get("id") == plugin_id for p in plugins):
            plugins.append({"id": plugin_id})
    disabled = [p for p in shell.get("disabledPlugins", []) if p not in (SAVER, IDLE_CLONE)]
    if "omarchy.idle" not in disabled:
        disabled.append("omarchy.idle")
    shell["disabledPlugins"] = disabled
    restores = shell.setdefault("cloneSourceRestores", [])
    if IDLE_CLONE not in restores:
        restores.append(IDLE_CLONE)
    atomic_text(config / "shell.json", json.dumps(shell, indent=2) + "\n")
    # Upgrade the badge to expose previews without changing existing bar settings.
    badge = config / "plugins" / PLUGIN
    if badge.is_dir():
        atomic_text(badge / "FunkMaster.qml", (REPO / "desktop/plugin/FunkMaster.qml").read_text())


def install_screensavers(config, state, backups):
    backup = snapshot(config, state, backups)
    atomic_text(backups.parent / "latest", str(backup) + "\n")
    try:
        install_saver_files(config)
        run("omarchy", "restart", "shell")
        verify_saver_loaded()
        validate_session()
    except Exception:
        print(f"Screensaver installation failed; restoring {backup}")
        restore(backup, config, state)
        raise
    print(f"Animated OMARCHY screensavers installed. Backup: {backup}")
    print("Preview: omarchy-shell funk-saver preview")


def verify_saver_loaded():
    # A shell reload can answer ping before service plugins finish initializing.
    for _ in range(40):
        try:
            result = json.loads(run("omarchy-shell", "funk-saver", "status"))
            if "screensaverEnabled" in result:
                return
        except (RuntimeError, json.JSONDecodeError):
            pass
        time.sleep(0.15)
    raise RuntimeError("Funk Master screensaver service did not finish loading.")


def install_apps(config, state, backups):
    backup = snapshot(config, state, backups)
    atomic_text(backups.parent / "latest", str(backup) + "\n")
    try:
        destination = config / "themes" / SLUG
        if not destination.is_dir():
            raise RuntimeError("Install the Funk Master theme before applying the app styling upgrade.")
        for name in ("colors.toml", "alacritty.toml", "ghostty.conf", "kitty.conf", "foot.ini"):
            remove(destination / name)
            copy(REPO / name, destination / name)
        app_theme.install()
        run("omarchy", "theme", "set", SLUG)
        validate_session()
    except Exception:
        print(f"App styling installation failed; restoring {backup}")
        restore(backup, config, state)
        raise
    print(f"GTK and CLI styling installed. Backup: {backup}")
    print("Open a new terminal and new GTK app process to see all changes.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "screensavers", "apps", "restore"))
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
        elif args.action == "screensavers":
            install_screensavers(config, state, backups)
        elif args.action == "apps":
            install_apps(config, state, backups)
        else:
            latest = backups.parent / "latest"
            backup = args.backup or (Path(latest.read_text().strip()) if latest.exists() else None)
            if backup is None or backup.resolve().parent != backups.resolve():
                parser.error("No valid local Funk Master backup selected.")
            restore(backup, config, state)


if __name__ == "__main__":
    main()
