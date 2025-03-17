from pathlib import Path
import yaml

FILE_DIR = Path(__file__).parent.parent.parent
CONFIG = FILE_DIR / 'src' / 'config' / 'game_config.yaml'
with open(CONFIG, 'r') as f:
    config = list(yaml.load_all(f, Loader=yaml.SafeLoader))[0]

AGENT_STRATEGY = config['strategy']

env_params = {
    "piece_generator": config["generator"],
    "random_seed": config["seed"],
    "rows": config["rows"],
    "cols": config["cols"]
}

ui_config = {
    "fps": config["fps"],
    "agent_delay": config["delay"],
    "drop_interval": config["drop_interval"],
    "block_size": config["block_size"],
    "panel_width": 6 * config["block_size"],
    "panel_margin": 12,
    "background_color": config["background"],
    "border_color": config["border"],
    "border_width": config["border_w"],
    "grid_color": config["grid"],
    "grid_width": config["grid_w"],
    "panel_bg_color": config["panel"],
    "text_color": config["text"],
    "button_bg_color": config["button_bg"],
    "button_hover_color": config["button_hover"]
}

BLOCK_SIZE = ui_config["block_size"]
ROWS = env_params["rows"]
COLUMNS = env_params["cols"]
WIDTH = COLUMNS * BLOCK_SIZE
HEIGHT = ROWS * BLOCK_SIZE
PANEL_WIDTH = ui_config["panel_width"]
PANEL_MARGIN = ui_config["panel_margin"]
SCREEN_WIDTH = WIDTH + PANEL_WIDTH + PANEL_MARGIN * 2
SCREEN_HEIGHT = HEIGHT
