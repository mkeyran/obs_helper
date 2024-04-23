from pathlib import Path
import toml

# Load configuration from TOML file
config_path = Path(__file__).parent / "config.toml"
config = toml.load(str(config_path))
dbus_serice_name = "org.keyran.obsidianhelper"