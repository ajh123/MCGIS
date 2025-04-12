class Project:
    def __init__(self, name="Untitled Project"):
        self.name = name
        self.layers = []
        # Properties controlling pan and zoom.
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.min_x = 0
        self.min_z = 0
        self.world_width = 0
        self.world_height = 0

    def add_layer(self, layer):
        self.layers.append(layer)
        layer.project = self

    def remove_layer(self, layer):
        if layer in self.layers:
            self.layers.remove(layer)

    def draw(self, canvas, view_left, view_top, view_right, view_bottom):
        """
        Delegate drawing to each layer, passing the current pan/zoom parameters.
        """
        for layer in self.layers:
            layer.draw(canvas, view_left, view_top, view_right, view_bottom,
                       self.zoom, self.offset_x, self.offset_y)

    def update(self):
        """
        Delegate update to each layer.
        """
        for layer in self.layers:
            layer.update()
