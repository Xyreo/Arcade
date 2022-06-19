import pickle
import base64
from PIL import Image
import os

ASSET = "Assets/Home_Assets"
ASSET = ASSET if os.path.exists(ASSET) else "Client/" + ASSET

x = Image.open(ASSET+'default.png').resize((64, 64))
x.save("temp.png", quality=50, optimize=True)
