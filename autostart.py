import sys
from pathlib import Path
from subprocess import list2cmdline

if sys.platform == "win32":
    import winreg


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_VALUE = "DesktopDiary"
STARTUP_ARG = "--autostart"


def set_autostart(enabled: bool) -> None:
    if enabled:
        executable = Path(sys.executable)
        args = [str(executable), STARTUP_ARG]
        if not getattr(sys, "frozen", False):
            pythonw = executable.with_name("pythonw.exe")
            script = Path(__file__).with_name("main.py").resolve()
            args = [
                str(pythonw if pythonw.is_file() else executable),
                str(script),
                STARTUP_ARG,
            ]
        command = list2cmdline(args)
        if len(command) > 260:
            raise OSError("Windows Run command exceeds 260 characters")
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.SetValueEx(key, APP_VALUE, 0, winreg.REG_SZ, command)
    else:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, APP_VALUE)
        except FileNotFoundError:
            pass
