from pathlib import Path

try:
    import tomli as toml
except ImportError:
    import tomllib as toml


CONFIG_DIR = Path.home() / ".spendsentry"
CONFIG_FILE = CONFIG_DIR / "config.toml"


def get_config():
    if not CONFIG_FILE.exists():
        return {}
    with open(CONFIG_FILE, "rb") as f:
        return toml.load(f)


def save_config(config_data):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Simple formatting for writing
    lines = []
    for section, values in config_data.items():
        lines.append(f"[{section}]")
        for k, v in values.items():
            if isinstance(v, str):
                lines.append(f'{k} = "{v}"')
            else:
                lines.append(f"{k} = {v}")
        lines.append("")

    with open(CONFIG_FILE, "w") as f:
        f.write("\n".join(lines))
