import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"
from pygame import mixer

mixer.init()


def play(filepath, loops=0):
    mixer.music.load(filepath)
    mixer.music.play(loops=loops)
