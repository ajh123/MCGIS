import json
import math
from layers import Layer

class GeoJSONLayer(Layer):
    def __init__(self, geojson_file, name="GeoJSON Layer", project=None):
        super().__init__(name, project)
        self.geojson_file = geojson_file
        self.geojson_data = None
        self.canvas_items = []
        self.load_geojson()
        
    def load_geojson(self):
        try:
            with open(self.geojson_file, 'r') as f:
                content = f.read().strip()
                if content:
                    self.geojson_data = json.loads(content)
                else:
                    self.geojson_data = {"type": "FeatureCollection", "features": []}
        except json.JSONDecodeError:
            self.geojson_data = {"type": "FeatureCollection", "features": []}
            print(f"Warning: Empty or invalid JSON in {self.geojson_file}")
    
    def draw(self, canvas, view_left, view_top, view_right, view_bottom, zoom, offset_x, offset_y):
        # Clear previous drawings
        for item_id in self.canvas_items:
            canvas.delete(item_id)
        self.canvas_items = []
        
        if not self.geojson_data:
            return
            
        # Process features
        for feature in self.geojson_data.get('features', []):
            geometry = feature.get('geometry', {})
            geometry_type = geometry.get('type')
            coordinates = geometry.get('coordinates', [])
            
            if geometry_type == 'Point':
                self._draw_point(canvas, coordinates, zoom, offset_x, offset_y)
            elif geometry_type == 'LineString':
                self._draw_linestring(canvas, coordinates, zoom, offset_x, offset_y)
            elif geometry_type == 'Polygon':
                self._draw_polygon(canvas, coordinates, zoom, offset_x, offset_y)
            elif geometry_type == 'MultiPoint':
                for point in coordinates:
                    self._draw_point(canvas, point, zoom, offset_x, offset_y)
            elif geometry_type == 'MultiLineString':
                for line in coordinates:
                    self._draw_linestring(canvas, line, zoom, offset_x, offset_y)
            elif geometry_type == 'MultiPolygon':
                for polygon in coordinates:
                    self._draw_polygon(canvas, polygon, zoom, offset_x, offset_y)
    
    def _draw_point(self, canvas, coordinates, zoom, offset_x, offset_y):
        x, z = coordinates
        # Convert from world to canvas coordinates using project's min_x and min_z
        canvas_x = (x - self.project.min_x) * zoom + offset_x
        canvas_z = (z - self.project.min_z) * zoom + offset_y
        
        # Draw a circle for points
        radius = 5
        item_id = canvas.create_oval(
            canvas_x - radius, canvas_z - radius,
            canvas_x + radius, canvas_z + radius,
            fill='red', outline='black'
        )
        self.canvas_items.append(item_id)

    def _draw_linestring(self, canvas, coordinates, zoom, offset_x, offset_y):
        points = []
        for x, z in coordinates:
            # Convert from world to canvas coordinates using project's min_x and min_z
            canvas_x = (x - self.project.min_x) * zoom + offset_x
            canvas_z = (z - self.project.min_z) * zoom + offset_y
            points.extend([canvas_x, canvas_z])
        
        if points:
            item_id = canvas.create_line(points, fill='blue', width=2)
            self.canvas_items.append(item_id)

    def _draw_polygon(self, canvas, coordinates, zoom, offset_x, offset_y):
        # For polygons, the first element is the outer ring
        outer_ring = coordinates[0]
        
        points = []
        for x, z in outer_ring:
            # Convert from world to canvas coordinates using project's min_x and min_z
            canvas_x = (x - self.project.min_x) * zoom + offset_x
            canvas_z = (z - self.project.min_z) * zoom + offset_y
            points.extend([canvas_x, canvas_z])
        
        if points:
            item_id = canvas.create_polygon(points, outline='green', fill='', width=2)
            self.canvas_items.append(item_id)
            
            # Process holes (inner rings) if any
            for inner_ring in coordinates[1:]:
                hole_points = []
                for x, z in inner_ring:
                    # Convert from world to canvas coordinates using project's min_x and min_z
                    canvas_x = (x - self.project.min_x) * zoom + offset_x
                    canvas_z = (z - self.project.min_z) * zoom + offset_y
                    hole_points.extend([canvas_x, canvas_z])
                
                if hole_points:
                    hole_id = canvas.create_polygon(hole_points, outline='green', fill='', width=2)
                    self.canvas_items.append(hole_id)