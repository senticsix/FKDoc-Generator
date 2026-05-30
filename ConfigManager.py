import json
import os


CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "name": "",
    "kilometers": "",
    "output_path": "",
    "date-init": "",
}


REQUIRED_CONFIG_FIELDS = [
    "name",
    "kilometers",
    "output_path",
    "date-init",
]


def config_exists():
    return os.path.exists(CONFIG_FILE)


def is_config_complete(config):
    return all(str(config.get(field, "")).strip() for field in REQUIRED_CONFIG_FIELDS)


def load_config():
    if not config_exists():
        return DEFAULT_CONFIG.copy()

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = json.load(file)

    merged_config = DEFAULT_CONFIG.copy()
    merged_config.update(config)

    return merged_config


def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, indent=4, ensure_ascii=False)
