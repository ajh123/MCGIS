class Layer:
    def __init__(self, name="Layer", project=None):
        self.name = name
        self.project = project

    def draw(self, canvas, view_left, view_top, view_right, view_bottom, zoom, offset_x, offset_y):
        """
        Draw the layer on the given canvas using the visible region and project-level
        pan/zoom parameters.
        Subclasses must implement this method.
        """
        raise NotImplementedError

    def update(self):
        """
        Update the layer's internal state if needed.
        Subclasses can implement this method.
        """
        pass
