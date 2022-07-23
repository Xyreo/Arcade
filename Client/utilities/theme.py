import os
import pickle
import sys


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


ASSET = resource_path(
    os.path.join("assets", "home_assets", "theme")
    if os.path.exists(os.path.join("assets", "home_assets", "theme"))
    else os.path.join("Client", os.path.join("assets", "home_assets", "theme"))
)
SETTINGS_FILE = (
    os.path.join(
        os.environ["USERPROFILE"],
        "AppData",
        "Local",
        "Arcade",
        "settings.dat",
    )
    if os.name == "nt"
    else os.path.join(
        os.environ["HOME"],
        "Applications",
        "Arcade",
        "settings.dat",
    )
)


class Theme:
    def __init__(self, root, theme="dark"):
        self.root = root
        self.root.tk.call("source", os.path.join(ASSET, "void.tcl"))

        for i in ["dark", "light"]:
            self.root.tk.call("init", i, os.path.join(ASSET, i))

        self.root.tk.call("set_theme", theme)

    def toggle_theme(self):
        if self.root.tk.call("ttk::style", "theme", "use") == "void-dark":
            t = "light"
        else:
            t = "dark"

        self.root.tk.call("set_theme", t)

        with open(SETTINGS_FILE, "rb+") as f:
            d = pickle.load(f)
            d["THEME"] = t
            f.seek(0)
            pickle.dump(d, f)

    def curr_theme(self):
        return self.root.tk.call("ttk::style", "theme", "use")[5:]
