import os
import sys

ASSET = os.path.join("Assets", "Home_Assets", "theme")
ASSET = ASSET if os.path.exists(ASSET) else os.path.join("Client", ASSET)


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


ASSET = resource_path(ASSET)
THEME_FILE = (
    os.path.join(
        os.environ["USERPROFILE"],
        "AppData",
        "Local",
        "Arcade",
        "theme.txt",
    )
    if os.name == "nt"
    else os.path.join(
        os.environ["HOME"],
        "Applications",
        "Arcade",
        "theme.txt",
    )
)


def init(root, theme="dark"):
    global win
    win = root
    win.tk.call("source", os.path.join(ASSET, "void.tcl"))

    for i in ["dark", "light"]:
        win.tk.call("init", i, os.path.join(ASSET, i))

    win.tk.call("set_theme", theme)


def toggle_theme():
    global win

    if win.tk.call("ttk::style", "theme", "use") == "void-dark":
        t = "light"
    else:
        t = "dark"

    win.tk.call("set_theme", t)
    with open(THEME_FILE, "w") as f:
        f.write(t)
