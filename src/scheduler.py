import json
from datetime import datetime


def should_run_today(config_path="config/schedule.json") -> bool:
    today = datetime.utcnow().strftime("%Y-%m-%d")

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Schedule config not found. Defaulting to run.")
        return True

    if not config.get("enabled", True):
        print("Pipeline globally disabled.")
        return False

    mode = config.get("mode", "whitelist")
    allowed_dates = config.get("allowed_dates", [])

    if mode == "whitelist":
        return today in allowed_dates

    elif mode == "blacklist":
        return today not in allowed_dates

    else:
        print("Invalid mode. Defaulting to run.")
        return True
