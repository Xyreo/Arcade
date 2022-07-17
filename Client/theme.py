import os
import sys
import tkinter.ttk as ttk

ASSET = os.path.join("Assets", "Home_Assets")
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

    win.tk.call("source", os.path.join(ASSET, "azure.tcl"))
    st = ttk.Style()

    win.tk.call("set_theme", "light")
    st.map("TButton", foreground=[("disabled", "grey")])
    for i in range(10, 21):
        st.configure(f"{i}.TButton", font=("times", i))

    win.tk.call("set_theme", "dark")
    st.map("TButton", foreground=[("disabled", "grey")])
    for i in range(10, 21):
        st.configure(f"{i}.TButton", font=("times", i))

    win.tk.call("set_theme", theme)


def toggle_theme():
    global win
    t = ""
    if win.tk.call("ttk::style", "theme", "use") == "azure-dark":
        t = "light"
    else:
        t = "dark"

    win.tk.call("set_theme", t)
    with open(THEME_FILE, "w") as f:
        f.write(t)
