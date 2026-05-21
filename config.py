import os
import sys
from dotenv import load_dotenv


def _resource_dir() -> str:
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


def _data_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.expanduser("~/Library/Application Support/AFlow")
    return os.path.dirname(os.path.abspath(__file__))


RESOURCE_DIR = _resource_dir()
DATA_DIR = _data_dir()

if getattr(sys, "frozen", False):
    os.makedirs(DATA_DIR, exist_ok=True)

load_dotenv(os.path.join(DATA_DIR, ".env"))

# Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "whisper-large-v3-turbo"
WHISPER_LANGUAGE = "es"

# Audio
SAMPLE_RATE = 16000
CHANNELS = 1
AUDIO_DTYPE = "int16"
BLOCK_SIZE = 1024

# UI dimensions
PILL_WIDTH_IDLE = 34
PILL_WIDTH_RECORDING = 100
PILL_WIDTH_STATUS = 52
PILL_HEIGHT = 34
PILL_OPACITY = 0.90
PILL_CORNER_RADIUS = 17
PILL_MARGIN_BOTTOM = 14
LOGO_SIZE = 22

# Visualizer
NUM_BARS = 20
VIZ_FPS = 60
BAR_DECAY = 0.85
BAR_GAIN = 8.0

# Hotkey
DOUBLE_TAP_INTERVAL = 0.4

# Paths
LOGO_PATH = os.path.join(RESOURCE_DIR, "logo_small.png")
DB_PATH = os.path.join(DATA_DIR, "transcriptions.db")
APP_DATA_DIR = DATA_DIR
