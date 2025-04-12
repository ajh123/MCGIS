import tkinter as tk
import tiles


class MapViewer(tk.Frame):
    def __init__(self, master, tile_folder):
        super().__init__(master)
        self.master = master
        self.tileSource = tiles.RasterTileSource(tile_folder)
        self.drag_start = None

        self.canvas = tk.Canvas(
            self,
            bg="black",
            cursor="crosshair",
            scrollregion=(0, 0, 10000, 10000)
        )
        self.hbar = tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.scroll_x)
        self.vbar = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.scroll_y)
        self.coord_label = tk.Label(self, text="", anchor="w")

        self.canvas.config(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.hbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.vbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.coord_label.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.zoom_handler)
        self.canvas.bind("<Motion>", self.update_cursor_position)
        self.bind("<Configure>", lambda e: self.draw_tiles())

        self.tileSource.load_tiles()
        self.tileSource.calculate_bounds()
        self.draw_tiles()


    def draw_tiles(self):
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        if canvas_width <= 0 or canvas_height <= 0:
            return

        # Determine the visible region in canvas coordinates.
        view_left = self.canvas.canvasx(0)
        view_top = self.canvas.canvasy(0)
        view_right = view_left + canvas_width
        view_bottom = view_top + canvas_height

        # Update or remove each tile based on its visible position.
        for tile in self.tileSource.tiles:
            canvas_x1 = (tile.game_x - self.tileSource.min_x) * self.tileSource.zoom + self.tileSource.offset_x
            canvas_y1 = (tile.game_z - self.tileSource.min_z) * self.tileSource.zoom + self.tileSource.offset_y
            tile_width = tile.image.width * self.tileSource.zoom
            tile_height = tile.image.height * self.tileSource.zoom
            canvas_x2 = canvas_x1 + tile_width
            canvas_y2 = canvas_y1 + tile_height

            is_visible = (
                canvas_x1 < view_right and
                canvas_x2 > view_left and
                canvas_y1 < view_bottom and
                canvas_y2 > view_top
            )

            if is_visible:
                tile.update_image(self.tileSource.zoom)
                if tile.canvas_id is None:
                    tile.canvas_id = self.canvas.create_image(
                        canvas_x1, canvas_y1, anchor="nw", image=tile.tk_image
                    )
                else:
                    self.canvas.coords(tile.canvas_id, canvas_x1, canvas_y1)
                    self.canvas.itemconfig(tile.canvas_id, image=tile.tk_image)
            else:
                if tile.canvas_id is not None:
                    self.canvas.delete(tile.canvas_id)
                    tile.canvas_id = None

        self.update_scroll_region()
        self.master.title(f"Map Viewer – Zoom: {self.tileSource.zoom:.2f}")

    def update_scroll_region(self):
        w = int(self.tileSource.world_width * self.tileSource.zoom)
        h = int(self.tileSource.world_height * self.tileSource.zoom)
        self.canvas.config(scrollregion=(0, 0, w, h))

    def scroll_x(self, *args):
        self.canvas.xview(*args)
        frac = float(self.canvas.xview()[0])
        self.tileSource.offset_x = -frac * (self.tileSource.world_width * self.tileSource.zoom)
        self.draw_tiles()

    def scroll_y(self, *args):
        self.canvas.yview(*args)
        frac = float(self.canvas.yview()[0])
        self.tileSource.offset_y = -frac * (self.tileSource.world_height * self.tileSource.zoom)
        self.draw_tiles()

    def start_pan(self, event):
        self.drag_start = (event.x, event.y)

    def do_pan(self, event):
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.tileSource.offset_x += dx
            self.tileSource.offset_y += dy
            self.drag_start = (event.x, event.y)
            self.draw_tiles()

    def zoom_handler(self, event):
        old_zoom = self.tileSource.zoom
        new_zoom = self.tileSource.zoom * (1.1 if event.delta > 0 else 0.9)
        new_zoom = max(0.1, min(8.0, new_zoom))

        # Calculate mouse position in canvas coordinates.
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        # Convert these to game coordinates (world coordinates).
        game_x = (cx - self.tileSource.offset_x) / old_zoom + self.tileSource.min_x
        game_z = (cy - self.tileSource.offset_y) / old_zoom + self.tileSource.min_z

        # Adjust offsets so the game coordinate under the mouse stays fixed.
        self.tileSource.offset_x = cx - new_zoom * (game_x - self.tileSource.min_x)
        self.tileSource.offset_y = cy - new_zoom * (game_z - self.tileSource.min_z)
        self.tileSource.zoom = new_zoom
        self.draw_tiles()

    def update_cursor_position(self, event):
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        world_x = int((cx - self.tileSource.offset_x) / self.tileSource.zoom + self.tileSource.min_x)
        world_z = int((cy - self.tileSource.offset_y) / self.tileSource.zoom + self.tileSource.min_z)
        self.coord_label.config(text=f"Cursor at: X={world_x}, Z={world_z}")

def main():
    root = tk.Tk()
    folder = r"abc"  # Replace with your actual tile folder path.
    viewer = MapViewer(root, folder)
    viewer.pack(fill=tk.BOTH, expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
