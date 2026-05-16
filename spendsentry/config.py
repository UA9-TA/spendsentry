from pathlib import Path

# Try to use tomllib for 3.11+, fallback to tomli for 3.10
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def get_config_dir() -> Path:
    config_dir = Path.home() / ".spendsentry"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    return get_config_dir() / "config.toml"


def load_config() -> dict:
    config_path = get_config_path()
    if not config_path.exists():
        return {}
    with open(config_path, "rb") as f:
        return tomllib.load(f)


def save_config(config: dict):
    config_path = get_config_path()
    # Write using simple toml format since we don't have a toml writer in stdlib
    with open(config_path, "w") as f:
        for section, values in config.items():
            f.write(f"[{section}]\n")
            for k, v in values.items():
                if isinstance(v, str):
                    f.write(f'{k} = "{v}"\n')
                else:
                    f.write(f"{k} = {v}\n")
            f.write("\n")
