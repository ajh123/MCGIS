import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import json
import tiles  # For RasterTileSource type checking
from project import Project
from layer_editor import LayerListDialog

class ProjectManager:
    def __init__(self):
        self.current_project = None
    
    def new_project(self):
        name = simpledialog.askstring("New Project", "Project Name:", initialvalue="New Project")
        if name:
            return Project(name)
        return None
    
    def save_project(self, project, path=None):
        if not path:
            path = filedialog.asksaveasfilename(
                defaultextension=".mcgis",
                filetypes=[("MCGIS Project", "*.mcgis"), ("All Files", "*.*")]
            )
        if not path:
            return False
        
        project_data = {
            "name": project.name,
            "zoom": project.zoom,
            "offset_x": project.offset_x,
            "offset_y": project.offset_y,
            "layers": []
        }
        
        for layer in project.layers:
            if isinstance(layer, tiles.RasterTileSource):
                layer_data = {
                    "type": "RasterTileSource",
                    "name": layer.name,
                    "tile_folder": layer.tile_folder
                }
                project_data["layers"].append(layer_data)
        
        with open(path, 'w') as f:
            json.dump(project_data, f, indent=2)
        
        return True
    
    def load_project(self, path=None):
        if not path:
            path = filedialog.askopenfilename(
                filetypes=[("MCGIS Project", "*.mcgis"), ("All Files", "*.*")]
            )
        if not path:
            return None
        
        try:
            with open(path, 'r') as f:
                project_data = json.load(f)
            
            project = Project(project_data["name"])
            project.zoom = project_data["zoom"]
            project.offset_x = project_data["offset_x"]
            project.offset_y = project_data["offset_y"]
            
            for layer_data in project_data["layers"]:
                if layer_data["type"] == "RasterTileSource":
                    layer = tiles.RasterTileSource(
                        layer_data["tile_folder"],
                        name=layer_data["name"]
                    )
                    project.add_layer(layer)
            
            return project
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load project: {str(e)}")
            return None

class MapViewer(tk.Frame):
    def __init__(self, master, project=None):
        super().__init__(master)
        self.master = master
        self.project = project
        self.project_manager = ProjectManager()

        self.drag_start = None

        # Create menu
        self.menu_bar = tk.Menu(master)
        self.master.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project", command=self.new_project)
        file_menu.add_command(label="Open Project", command=self.open_project)
        file_menu.add_command(label="Save Project", command=self.save_project)
        file_menu.add_command(label="Save Project As", command=self.save_project_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)

        # Project menu
        project_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Project", menu=project_menu)
        project_menu.add_command(label="Properties", command=self.edit_project_properties)
        project_menu.add_command(label="Add Tile Layer", command=self.add_tile_layer)
        project_menu.add_command(label="Manage Layers", command=self.manage_layers)
        
        # Set up the canvas and UI elements
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

        # Initialize with empty project if none provided
        if self.project is None:
            self.project = Project("Untitled Project")
        else:
            # Initialise layers
            for layer in self.project.layers:
                if hasattr(layer, 'load_tiles'):
                    layer.load_tiles()
                if hasattr(layer, 'calculate_bounds'):
                    layer.calculate_bounds()
            self.redraw()
    
    def new_project(self):
        project = self.project_manager.new_project()
        if project:
            self.project = project
            self.redraw()
    
    def open_project(self):
        project = self.project_manager.load_project()
        if project:
            self.project = project
            # Initialize layers
            for layer in self.project.layers:
                if hasattr(layer, 'load_tiles'):
                    layer.load_tiles()
                if hasattr(layer, 'calculate_bounds'):
                    layer.calculate_bounds()
            self.redraw()
    
    def save_project(self):
        self.project_manager.save_project(self.project)
    
    def save_project_as(self):
        self.project_manager.save_project(self.project, path=None)
    
    def edit_project_properties(self):
        name = simpledialog.askstring("Project Properties", "Project Name:", initialvalue=self.project.name)
        if name:
            self.project.name = name
            self.redraw()
    
    def add_tile_layer(self):
        tile_folder = filedialog.askdirectory(title="Select Tile Folder")
        if tile_folder:
            layer_name = simpledialog.askstring("Layer Name", "Enter a name for this layer:", initialvalue="Raster Layer")
            if layer_name:
                layer = tiles.RasterTileSource(tile_folder, name=layer_name)
                self.project.add_layer(layer)
                if hasattr(layer, 'load_tiles'):
                    layer.load_tiles()
                if hasattr(layer, 'calculate_bounds'):
                    layer.calculate_bounds()
                self.redraw()

    def manage_layers(self):
        dialog = LayerListDialog(self.master, self.project)
        self.master.wait_window(dialog)
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
    root.geometry("800x600")
    viewer = MapViewer(root)
    viewer.pack(fill=tk.BOTH, expand=True)
    root.mainloop()

if __name__ == "__main__":
    main()