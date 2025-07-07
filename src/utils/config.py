import pygame
pygame.init()
DEFAULT_SCREEN_WIDTH = 1920
DEFAULT_SCREEN_HEIGHT = 1080
display_info = pygame.display.Info()
INITIAL_WIDTH = min(int(display_info.current_w), DEFAULT_SCREEN_WIDTH)
INITIAL_HEIGHT = min(int(display_info.current_h), DEFAULT_SCREEN_HEIGHT)

scale_x = INITIAL_WIDTH / DEFAULT_SCREEN_WIDTH
scale_y = INITIAL_HEIGHT / DEFAULT_SCREEN_HEIGHT
scale_factor = min(scale_x, scale_y)

standard_font_size = int(24 * scale_factor)
font = pygame.font.SysFont("Arial", max(standard_font_size, 16))

large_font_size = int(45 * scale_factor)
font_large = pygame.font.SysFont("Arial", max(large_font_size, 20), bold=True)

stamp_color = (255, 0, 0)  # Màu đỏ cho con dấu
background_color = (255, 255, 255)  # Màu nền (trắng)


mode_weights = {
    "easy": {
        "weights": [-0.5, 0.5, -0.5, -0.5],
        "strategy": 'normal',
        "delay": 400,
        "level": 0
    },
    "medium": {
        "weights": [-0.48601, 0.01529343, -0.73499765, -0.47258739],
        "strategy": 'normal',
        "delay": 300,
        "level": 4
    },
    "hard": {
        "weights": [-0.51192248, 0.76122771, -0.35380663, -0.18245166],
        "strategy": 'normal',
        "delay": 200,
        "level": 6
    },
    "asian":{
        "weights": [-0.50981325,  0.76085042, -0.35653814, -0.18460132],
        "strategy": 'promax',
        "delay": 100,
        "level": 18
    },
}

env_params = {
    "piece_generator": "classic",
    "random_seed": 123,
    "rows": 22,
    "cols": 10
}

ui_config = {
    "fps": 60,
    "block_size": 45,
    "panel_width": 6 * 45,
    "panel_margin": 18,
    "background_color": [245, 245, 245],
    "border_color": [50, 50, 50],
    "border_width": 3,
    "grid_color": [220, 220, 220],
    "grid_width": 2,
    "panel_bg_color": [200, 200, 200],
    "text_color": [50, 50, 50],
    "button_bg_color": [200, 200, 200],
    "button_hover_color": [100, 100, 100],
}

gravity_rate = {
    0: 48,
    1: 43,
    2: 38,
    3: 33,
    4: 28,
    5: 23,
    6: 18,
    7: 13,
    8: 8,
    9: 6,
    10: 5,
    11: 5,
    12: 5,
    13: 4,
    14: 4,
    15: 4,
    16: 3,
    17: 3,
    18: 3,
    19: 2,
    29: 1
}

BLOCK_SIZE = ui_config["block_size"] * scale_factor
ROWS = env_params["rows"]
COLUMNS = env_params["cols"]
BOARD_WIDTH = COLUMNS * BLOCK_SIZE
BOARD_HEIGHT = ROWS * BLOCK_SIZE
PANEL_WIDTH = ui_config["panel_width"] * scale_factor
PANEL_MARGIN = ui_config["panel_margin"] * scale_factor
CENTER_X = INITIAL_WIDTH // 2
CENTER_Y = INITIAL_HEIGHT // 2
GRID_WIDTH = int(ui_config["grid_width"] * scale_factor)
BORDER_WIDTH = int(ui_config["border_width"] * scale_factor)
