# Validation report

Validated September 5, 2026 on the user's live Omarchy desktop.

## Automated checks

`python3 validate.py`: **4 tests passed**.

- All source TOML files parse; primary foreground, focus, muted text and ANSI accent colors meet 4.5:1 against the main dark surface.
- Main cream text on aubergine measures **15.65:1**. This is a token-level check, not a claim of full interface accessibility certification.
- Shell configuration transformation is idempotent and preserves unrelated settings.
- A temporary-directory restore test recovers original contents, existing symlinks, wallpaper linkage and screensaver flag, and removes newly installed files. Theme/session commands are mocked in this test.
- Lua compiles with `luac -p`; QML parses using Qt's `qmlformat`; plugin manifest and entry point agree.

## Live session checks

- `omarchy theme current`: Funk Master.
- `hyprctl reload` succeeded and `hyprctl configerrors` returned no errors.
- Effective window rounding: **20 px**; border size: **3 px**.
- Shell geometry reports the Funk Master badge at **160 × 38 px** and a **38 px** bar on the active 1920 × 1080 monitor.
- Plugin registry reports `local.funk-master` enabled and the old Oligarchy plugin disabled.
- All **15 generated TOML files** parse; no unresolved template placeholders remain in generated text configs.
- Native screensaver is enabled, matching the preference saved before Oligarchy took control.
- Screenshot inspection confirmed the wallpaper, badge, bar layout, readable clock and gradient window frame.
- The preview was captured on a temporary empty workspace, then the user's original workspace was restored. `preview.png` is an actual desktop screenshot.
- No Funk Master QML loading/type errors appeared in the inspected user journal interval.

## Practical limits

Every app was not opened individually. Terminals/editors receive Omarchy-generated theme files and its normal refresh hooks; some applications may display changes only after opening a new window. The native wallpaper is 1672 × 941, scaled by the shell for this 1920 × 1080 screen. Lock input tokens were generated and parsed without forcing a session lock. The badge rendered correctly; its theme-picker click action was not exercised through a physical pointer event. Full live restoration was not performed after the successful install; its file restoration logic was tested in isolation.

No packaged Omarchy source, keybindings or monitor configuration was modified during the initial desktop overhaul. The repository had no configured remote at that validation point; it was subsequently connected to `rookepoole/omarchy-funk-master` on GitHub.
