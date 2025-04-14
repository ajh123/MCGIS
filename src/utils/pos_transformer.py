from pyproj import Transformer

# Anchor at Null Island
origin_lat = 0.0
origin_lon = 0.0

# Define a custom Transverse Mercator projection centred on the anchor.
# Note: We set x_0 and y_0 to 0.
# Here we define the local coordinate system such that:
#   x_local = Minecraft x (east positive)
#   y_local = -Minecraft z (north positive)
#
# The projection string below defines a Transverse Mercator projection with
# the centre at (origin_lat, origin_lon) and a scale factor of 1 (since 1 block = 1 metre).
local_proj = f"+proj=tmerc +lat_0={origin_lat} +lon_0={origin_lon} +k=1 +x_0=0 +y_0=0 +ellps=WGS84"

# Create a transformer from the local projection to WGS84 (EPSG:4326).
# The parameter always_xy=True enforces (x, y) order.
transformer = Transformer.from_crs(local_proj, "EPSG:4326", always_xy=True)

def minecraft_to_wgs84_via_proj(x, z):
    """
    Convert Minecraft (x, z) to latitude/longitude using a local projection.
    
    Assumptions:
      - 1 block = 1 metre.
      - Minecraft x is east (positive) / west (negative).
      - Minecraft z is south (positive) / north (negative).
      - The local coordinates are defined as:
            x_local = x
            y_local = -z   (so that north becomes positive northing)
      - (0, 0) maps to Null Island.
    """
    # Adjust z: invert it for the y value in our local projection.
    y_local = -z
    # The transform returns (lon, lat) since always_xy=True.
    lon, lat = transformer.transform(x, y_local)
    return lat, lon

