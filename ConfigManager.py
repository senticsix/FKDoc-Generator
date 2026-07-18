import json
import os
import platform
import sys
from pathlib import Path


def _bundle_dir():
    """Folder containing bundled resources (template).

    Normal run: the script folder. PyInstaller build: the unpacked
    bundle folder (sys._MEIPASS).
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))

    return Path(__file__).resolve().parent


def _data_dir():
    """Writable folder for the config file.

    Normal run: the script folder (as before). PyInstaller build: the
    platform's standard location for application data.
    """
    if not getattr(sys, "frozen", False):
        return Path(__file__).resolve().parent

    system = platform.system()

    if system == "Windows":
        return Path(os.environ.get("APPDATA", str(Path.home()))) / "FKscript"

    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "FKscript"

    return Path.home() / ".fkscript"


BUNDLE_DIR = _bundle_dir()
DATA_DIR = _data_dir()

CONFIG_FILE = DATA_DIR / "config.json"
TEMPLATE_FILE = BUNDLE_DIR / "Fahrtkostenerstattung_Familienheimfahrt.docx"

DEFAULT_CONFIG = {
    "name": "",
    "kilometers": "",
    "output_path": "",
    "date-init": "",
    "date-ausb-anf": "",
    "date-ausb-ende": "",
}


REQUIRED_CONFIG_FIELDS = [
    "name",
    "kilometers",
    "output_path",
    "date-init",
    "date-ausb-anf",
    "date-ausb-ende",
]


def config_exists():
    return CONFIG_FILE.exists()


def is_config_complete(config):
    return all(str(config.get(field, "")).strip() for field in REQUIRED_CONFIG_FIELDS)


def load_config():
    if not config_exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            config = json.load(file)
    except (json.JSONDecodeError, OSError):
        return DEFAULT_CONFIG.copy()

    merged_config = DEFAULT_CONFIG.copy()
    merged_config.update(config)

    return merged_config


def save_config(config):
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4, ensure_ascii=False)
