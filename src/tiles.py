import re
import os
from PIL import Image, ImageTk

TILE_PATTERN = re.compile(r'^(\d+)_(\d+)_x(-?\d+)_z(-?\d+)\.png$')

class Tile:
    def __init__(self, path, tile_x, tile_z, game_x, game_z):
        self.path = path
        self.tile_x = int(tile_x)
        self.tile_z = int(tile_z)
        self.game_x = int(game_x)
        self.game_z = int(game_z)
        self.image = Image.open(path)
        self.tk_image = None
        self.canvas_id = None
        self.last_zoom = None  # Last zoom factor used to generate tk_image

    def update_image(self, zoom):
        # Only update if no cached image exists or if the zoom has changed
        # significantly (more than 5% difference).
        if self.last_zoom is not None:
            change = abs(zoom - self.last_zoom) / zoom
            if change < 0.05 and self.tk_image is not None:
                return
        self.last_zoom = zoom
        new_size = (int(self.image.width * zoom), int(self.image.height * zoom))
        self.tk_image = ImageTk.PhotoImage(self.image.resize(new_size, Image.NEAREST))

class RasterTileSource:
    def __init__(self, tile_folder, zoom=1.0):
        self.tile_folder = tile_folder
        self.zoom = zoom
        self.tiles = []
        self.world_width = 0
        self.world_height = 0
        self.min_x = 0
        self.min_z = 0
        self.offset_x = 0
        self.offset_y = 0

    def load_tiles(self):
        for fname in os.listdir(self.tile_folder):
            match = TILE_PATTERN.match(fname)
            if match:
                tile_x, tile_z, game_x, game_z = match.groups()
                path = os.path.join(self.tile_folder, fname)
                tile = Tile(path, tile_x, tile_z, game_x, game_z)
                tile.update_image(self.zoom)
                self.tiles.append(tile)

    def calculate_bounds(self):
        if not self.tiles:
            return
        min_x = min(tile.game_x for tile in self.tiles)
        max_x = max(tile.game_x + tile.image.width for tile in self.tiles)
        min_z = min(tile.game_z for tile in self.tiles)
        max_z = max(tile.game_z + tile.image.height for tile in self.tiles)
        self.world_width = max_x - min_x
        self.world_height = max_z - min_z
        self.min_x = min_x
        self.min_z = min_z