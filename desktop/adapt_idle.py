"""Apply a narrow adapter to the user's officially cloned Omarchy idle plugin.

Existing lock timers, inhibitors, stay-awake and wake behavior remain upstream.
Exact source anchors make incompatible upstream revisions fail before writing.
"""
MARKER = "// FUNK MASTER ASCII ADAPTER v1"


def adapted(source):
    if MARKER in source:
        return source
    replacements = [
        ('  function launchScreensaver() {', '''  // FUNK MASTER ASCII ADAPTER v1
  function funkSaver() {
    return shell ? shell.serviceFor("local.funk-screensavers") : null
  }

  function funkSaverActive() {
    var saver = funkSaver()
    return !!(saver && saver.active)
  }

  function launchScreensaver() {'''),
        ('    runProcess(screensaverProcess, "screensaver", "[[ $(omarchy-shell lock isLocked 2>/dev/null) == \\"true\\" ]] || omarchy-launch-screensaver")', '''    var saver = funkSaver()
    if (saver) saver.start(Math.floor(Date.now() / 18000) % 4, false)
    else runProcess(screensaverProcess, "screensaver", "[[ $(omarchy-shell lock isLocked 2>/dev/null) == \\"true\\" ]] || omarchy-launch-screensaver")'''),
        ('    runProcess(lockProcess, "lock", "omarchy-system-lock")', '''    var saver = funkSaver()
    if (saver) saver.dismiss("lock")
    runProcess(lockProcess, "lock", "omarchy-system-lock")'''),
        ('(root.screensaverWindowCount > 0 || screensaverLaunchGraceTimer.running)',
         '(root.screensaverWindowCount > 0 || funkSaverActive() || screensaverLaunchGraceTimer.running)'),
        ('root.screensaverWindowCount === 0 && !idleMonitor.isIdle',
         'root.screensaverWindowCount === 0 && !funkSaverActive() && !idleMonitor.isIdle')
    ]
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError("Omarchy idle source has changed; adapter anchor missing or ambiguous: " + before)
        source = source.replace(before, after, 1)
    return source


if __name__ == "__main__":
    import sys
    from pathlib import Path
    print(adapted(Path(sys.argv[1]).read_text()))
