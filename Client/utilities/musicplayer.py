import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
from pygame import mixer

try:
    mixer.init()
except:
    print("No Output Devices Found")

def play(filepath, loops=0):
    mixer.music.load(filepath)
    mixer.music.play(loops=loops)
