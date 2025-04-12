import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, filedialog

class LayerListDialog(tk.Toplevel):
    def __init__(self, parent, project):
        super().__init__(parent)
        self.title("Layer Manager")
        self.project = project
        self.result = None
        self.geometry("400x300")
        
        # Create the layer list
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollable list of layers
        self.listbox = tk.Listbox(frame, selectmode=tk.SINGLE)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate the list
        self.refresh_list()
        
        # Buttons for layer operations
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Add Layer", command=self.add_layer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Edit", command=self.edit_layer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove", command=self.remove_layer).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Move Up", command=self.move_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Move Down", command=self.move_down).pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_frame = ttk.Frame(self)
        close_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(close_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)
        
    def refresh_list(self):
        self.listbox.delete(0, tk.END)
        for i, layer in enumerate(self.project.layers):
            self.listbox.insert(tk.END, f"{i+1}: {layer.name}")
    
    def add_layer(self):
        tile_folder = filedialog.askdirectory(title="Select Tile Folder")
        if tile_folder:
            layer_name = simpledialog.askstring("Layer Name", "Enter a name for this layer:", 
                                               initialvalue="Raster Layer")
            if layer_name:
                import tiles
                layer = tiles.RasterTileSource(tile_folder, name=layer_name)
                self.project.add_layer(layer)
                if hasattr(layer, 'load_tiles'):
                    layer.load_tiles()
                if hasattr(layer, 'calculate_bounds'):
                    layer.calculate_bounds()
                self.refresh_list()
    
    def edit_layer(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a layer first.")
            return
        
        index = selection[0]
        layer = self.project.layers[index]
        
        # For now we only support renaming
        new_name = simpledialog.askstring("Rename Layer", "New layer name:", 
                                         initialvalue=layer.name)
        if new_name:
            layer.name = new_name
            self.refresh_list()
    
    def remove_layer(self):
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a layer first.")
            return
        
        index = selection[0]
        if messagebox.askyesno("Confirm Deletion", "Are you sure you want to remove this layer?"):
            layer = self.project.layers[index]
            self.project.remove_layer(layer)
            self.refresh_list()
    
    def move_up(self):
        selection = self.listbox.curselection()
        if not selection or selection[0] == 0:
            return
        
        index = selection[0]
        layer = self.project.layers.pop(index)
        self.project.layers.insert(index-1, layer)
        self.refresh_list()
        self.listbox.selection_set(index-1)
    
    def move_down(self):
        selection = self.listbox.curselection()
        if not selection or selection[0] >= len(self.project.layers) - 1:
            return
        
        index = selection[0]
        layer = self.project.layers.pop(index)
        self.project.layers.insert(index+1, layer)
        self.refresh_list()
        self.listbox.selection_set(index+1)