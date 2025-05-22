import os
import json

def ensure_config():
    config_path = os.path.expanduser("~/.emma_config.json")
        if not os.path.exists(config_path):
                config = {
                                "api_key": "sk-XXXX-XXXX",  # placeholder, not hardcoded!
                                            "user": "default"
                }
                        with open(config_path, "w") as f:
                                    json.dump(config, f)

                                    def get_api_key():
                                        config_path = os.path.expanduser("~/.emma_config.json")
                                            with open(config_path, "r") as f:
                                                    return json.load(f).get("api_key")
                }