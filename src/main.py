# main.py

import tkinter as tk
import tiles  # For RasterTileSource type checking
from project import Project

class MapViewer(tk.Frame):
    def __init__(self, master, project):
        super().__init__(master)
        self.master = master
        self.project = project

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
        self.bind("<Configure>", lambda e: self.redraw())

        # Initialise layers.
        for layer in self.project.layers:
            if hasattr(layer, 'load_tiles'):
                layer.load_tiles()
            if hasattr(layer, 'calculate_bounds'):
                layer.calculate_bounds()
        self.redraw()

    def redraw(self):
        # Do not call self.canvas.delete("all") so that
        # each layer can manage its own tile items.
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

        # Delegate drawing to the project, which passes the current zoom and pan to its layers.
        self.project.draw(self.canvas, view_left, view_top, view_right, view_bottom)
        self.update_scroll_region()
        # For the window title, locate a RasterTileSource layer if present.
        title = f"{self.project.name} - MCGIS"
        for layer in self.project.layers:
            if isinstance(layer, tiles.RasterTileSource):
                title = f"Zoom ({self.project.zoom:.2f}) - {title}"
                break

        self.master.title(title)

    def update_scroll_region(self):
        # Update scroll region based on a RasterTileSource layer if found.
        for layer in self.project.layers:
            if isinstance(layer, tiles.RasterTileSource):
                w = int(layer.world_width * self.project.zoom)
                h = int(layer.world_height * self.project.zoom)
                self.canvas.config(scrollregion=(0, 0, w, h))
                break

    def scroll_x(self, *args):
        self.canvas.xview(*args)
        frac = float(self.canvas.xview()[0])
        # Adjust the horizontal pan offset.
        for layer in self.project.layers:
            if isinstance(layer, tiles.RasterTileSource):
                self.project.offset_x = -frac * (layer.world_width * self.project.zoom)
                break
        self.redraw()

    def scroll_y(self, *args):
        self.canvas.yview(*args)
        frac = float(self.canvas.yview()[0])
        # Adjust the vertical pan offset.
        for layer in self.project.layers:
            if isinstance(layer, tiles.RasterTileSource):
                self.project.offset_y = -frac * (layer.world_height * self.project.zoom)
                break
        self.redraw()

    def start_pan(self, event):
        self.drag_start = (event.x, event.y)

    def do_pan(self, event):
        if self.drag_start:
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]
            self.project.offset_x += dx
            self.project.offset_y += dy
            self.drag_start = (event.x, event.y)
            self.redraw()

    def zoom_handler(self, event):
        old_zoom = self.project.zoom
        new_zoom = self.project.zoom * (1.1 if event.delta > 0 else 0.9)
        new_zoom = max(0.1, min(8.0, new_zoom))

        # Calculate mouse position in canvas coordinates.
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        # Convert these to world coordinates using the old zoom and pan.
        for layer in self.project.layers:
            if isinstance(layer, tiles.RasterTileSource):
                game_x = (cx - self.project.offset_x) / old_zoom + layer.min_x
                game_z = (cy - self.project.offset_y) / old_zoom + layer.min_z

                # Adjust offsets so that the game coordinate under the mouse remains fixed.
                self.project.offset_x = cx - new_zoom * (game_x - layer.min_x)
                self.project.offset_y = cy - new_zoom * (game_z - layer.min_z)
                break
        self.project.zoom = new_zoom
        self.redraw()

    def update_cursor_position(self, event):
        # Display the cursor's world coordinates based on the first RasterTileSource found.
        for layer in self.project.layers:
            if isinstance(layer, tiles.RasterTileSource):
                cx = self.canvas.canvasx(event.x)
                cy = self.canvas.canvasy(event.y)
                # Add 0.5 so that the result rounds to the block centre
                world_x = int((cx - self.project.offset_x) / self.project.zoom + layer.min_x + 0.5)
                world_z = int((cy - self.project.offset_y) / self.project.zoom + layer.min_z + 0.5)
                self.coord_label.config(text=f"Cursor at: X={world_x}, Z={world_z}")
                break


def main():
    root = tk.Tk()
    # Replace with your actual tile folder path.
    tile_folder = r"D:\users\samro\AppData\Roaming\ModrinthApp\profiles\Miners Online\map exports\2025-04-11_19.16.07"
    # Create the raster tile layer.
    import tiles
    raster_layer = tiles.RasterTileSource(tile_folder)
    
    # Create a project and add layers.
    from project import Project
    project = Project("Map Project")
    project.add_layer(raster_layer)
    
    viewer = MapViewer(root, project)
    viewer.pack(fill=tk.BOTH, expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()
