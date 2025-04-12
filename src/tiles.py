# tiles.py

import re
import os
from PIL import Image, ImageTk
from layers import Layer

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

class RasterTileSource(Layer):
    def __init__(self, tile_folder, name="Raster Tile Layer"):
        super().__init__(name)
        self.tile_folder = tile_folder
        self.tiles = []
        # Bounds values in game/world coordinates.
        self.world_width = 0
        self.world_height = 0
        self.min_x = 0
        self.min_z = 0

    def load_tiles(self):
        for fname in os.listdir(self.tile_folder):
            match = TILE_PATTERN.match(fname)
            if match:
                tile_x, tile_z, game_x, game_z = match.groups()
                path = os.path.join(self.tile_folder, fname)
                tile = Tile(path, tile_x, tile_z, game_x, game_z)
                # No zoom here; the update_image call will be done in draw() using the
                # project-level zoom value.
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

    def draw(self, canvas, view_left, view_top, view_right, view_bottom, zoom, offset_x, offset_y):
        """
        Draw each tile that falls within the visible region, using the project-level
        zoom and pan (offset) parameters.
        """
        for tile in self.tiles:
            # Calculate canvas coordinates for the tile.
            canvas_x1 = (tile.game_x - self.min_x) * zoom + offset_x
            canvas_y1 = (tile.game_z - self.min_z) * zoom + offset_y
            tile_width = tile.image.width * zoom
            tile_height = tile.image.height * zoom
            canvas_x2 = canvas_x1 + tile_width
            canvas_y2 = canvas_y1 + tile_height

            is_visible = (
                canvas_x1 < view_right and
                canvas_x2 > view_left and
                canvas_y1 < view_bottom and
                canvas_y2 > view_top
            )

            if is_visible:
                tile.update_image(zoom)
                if tile.canvas_id is None:
                    tile.canvas_id = canvas.create_image(
                        canvas_x1, canvas_y1, anchor="nw", image=tile.tk_image
                    )
                else:
                    canvas.coords(tile.canvas_id, canvas_x1, canvas_y1)
                    canvas.itemconfig(tile.canvas_id, image=tile.tk_image)
            else:
                if tile.canvas_id is not None:
                    canvas.delete(tile.canvas_id)
                    tile.canvas_id = None

    def update(self):
        """
        Update internal states (for example, recalc bounds).
        """
        self.calculate_bounds()
