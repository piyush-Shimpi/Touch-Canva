"""Stylised US outbreak map textures (Natural Earth, public domain) -> assets/
  map_base.png   land/ocean/state lines + population light-dots (sRGB)
  map_time.png   16-bit "infection arrival time" 0..1 (cities ~0, northern Rockies last), illustrative only
  map_land.png   land mask
The arrival-time field is a visual stand-in for the Cornell result (dense cities fall first, the remote
northern Rockies last). It is NOT the study's data.
Run with system python3 (numpy + PIL)."""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, "..", "assets")
LON0, LON1, LAT0, LAT1 = -126.0, -66.0, 23.5, 50.0
W = 2400
COSL = math.cos(math.radians(38))
H = int(W * (LAT1 - LAT0) / ((LON1 - LON0) * COSL))


def px(lon, lat):
    return ((lon - LON0) / (LON1 - LON0) * W, (LAT1 - lat) / (LAT1 - LAT0) * H)


def rings(geom):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    for poly in polys:
        for k, ring in enumerate(poly):
            yield k, ring


countries = json.load(open(os.path.join(A, "ne_50m_admin_0_countries.geojson")))
usa = next(f for f in countries["features"] if f["properties"]["ADM0_A3"] == "USA")
land = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(land)
for k, ring in rings(usa["geometry"]):
    lons = [p[0] for p in ring]
    if min(lons) < -130 or max(p[1] for p in ring) > 50.5:      # skip Alaska/Hawaii/far islands
        continue
    d.polygon([px(*p) for p in ring], fill=0 if k else 255)
# neighbours drawn dim so the US floats in context
ctx = Image.new("L", (W, H), 0)
dc = ImageDraw.Draw(ctx)
for f in countries["features"]:
    if f["properties"]["ADM0_A3"] in ("CAN", "MEX"):
        for k, ring in rings(f["geometry"]):
            dc.polygon([px(*p) for p in ring], fill=0 if k else 255)
states = json.load(open(os.path.join(A, "ne_50m_admin_1_states_provinces_lakes.geojson")))
lines = Image.new("L", (W, H), 0)
dl = ImageDraw.Draw(lines)
for f in states["features"]:
    if f["properties"].get("adm0_a3") != "USA":
        continue
    for k, ring in rings(f["geometry"]):
        dl.line([px(*p) for p in ring], fill=255, width=2)
L = np.asarray(land, np.float32) / 255
C = np.asarray(ctx, np.float32) / 255 * (1 - L)
S = np.asarray(lines, np.float32) / 255 * L

CITIES = [(-74.0, 40.7, 19.5), (-118.2, 34.05, 13), (-87.6, 41.9, 9.4), (-96.8, 32.8, 7.6), (-95.4, 29.8, 7.1),
          (-77.0, 38.9, 6.3), (-80.2, 25.8, 6.1), (-75.2, 39.95, 6.2), (-84.4, 33.75, 6.1), (-112.07, 33.45, 4.9),
          (-71.06, 42.36, 4.9), (-122.4, 37.77, 4.7), (-83.05, 42.33, 4.3), (-122.33, 47.6, 4.0), (-93.27, 44.98, 3.7),
          (-117.16, 32.7, 3.3), (-82.46, 27.95, 3.2), (-104.99, 39.74, 3.0), (-90.2, 38.63, 2.8), (-76.6, 39.3, 2.8),
          (-80.84, 35.23, 2.7), (-81.38, 28.54, 2.7), (-98.49, 29.42, 2.6), (-122.68, 45.52, 2.5), (-121.49, 38.58, 2.4),
          (-80.0, 40.44, 2.4), (-115.14, 36.17, 2.3), (-84.5, 39.1, 2.3), (-94.58, 39.1, 2.2), (-83.0, 39.96, 2.1),
          (-86.16, 39.77, 2.1), (-86.78, 36.16, 2.0), (-111.89, 40.76, 1.3), (-106.65, 35.08, 0.9), (-116.2, 43.6, 0.8),
          (-108.5, 45.78, 0.2), (-117.4, 47.66, 0.6), (-95.94, 41.26, 1.0), (-97.5, 35.47, 1.4), (-90.07, 29.95, 1.3),
          (-90.05, 35.15, 1.3), (-85.76, 38.25, 1.3), (-78.64, 35.78, 1.4), (-81.66, 30.33, 1.6), (-87.9, 43.04, 1.6),
          (-81.69, 41.5, 2.1), (-78.88, 42.89, 1.1), (-106.44, 31.76, 0.9), (-110.97, 32.22, 1.0), (-96.79, 46.88, 0.25),
          (-96.73, 43.54, 0.3), (-104.82, 41.14, 0.1), (-100.78, 46.81, 0.1)]
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
lon = LON0 + xx / W * (LON1 - LON0)
lat = LAT1 - yy / H * (LAT1 - LAT0)
D = np.zeros((H, W), np.float32)
T = np.full((H, W), 9.0, np.float32)
for clon, clat, pop in CITIES:
    dd = np.hypot((lon - clon) * COSL, lat - clat)
    D += pop * np.exp(-dd ** 2 / (2 * 1.1 ** 2))
    T = np.minimum(T, 0.6 / pop ** 0.7 + dd / 9.0)        # big cities seed first, then it spreads outward
rock = np.exp(-(((lon + 112.5) / 4.2) ** 2 + ((lat - 45.8) / 2.6) ** 2))   # remote northern Rockies
T = T * (1 + 2.2 * rock) - 0.25 * np.clip(D / D.max(), 0, 1)
T = (T - T[L > 0.5].min()) / (np.percentile(T[L > 0.5], 99.7) - T[L > 0.5].min())
T = np.clip(T, 0, 1)
Image.fromarray((T * 65535).astype(np.uint16)).save(os.path.join(A, "map_time.png"))
Image.fromarray((L * 255).astype(np.uint8)).save(os.path.join(A, "map_land.png"))

# base colours
rng = np.random.default_rng(4)
ocean = np.array([200, 222, 238], np.float32) / 255
landc = np.array([46, 86, 120], np.float32) / 255
ctxc = np.array([170, 194, 212], np.float32) / 255
linec = np.array([150, 190, 222], np.float32) / 255
img = ocean[None, None] * (1 - L - C)[..., None] + landc[None, None] * L[..., None] + ctxc[None, None] * C[..., None]
img = img * (1 - 0.8 * S[..., None]) + linec[None, None] * (0.8 * S[..., None])
# 307M people -> light dots, denser around cities
dots = np.zeros((H, W), np.float32)
prob = (0.02 + D / D.max()) * L
prob = prob / prob.sum()
idx = rng.choice(H * W, size=26000, p=prob.ravel())
dots.ravel()[idx] = 1.0
dots = np.asarray(Image.fromarray((dots * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.1)), np.float32) / 255
dots = np.clip(dots * 5, 0, 1)
img = img * (1 - dots[..., None]) + np.array([0.85, 0.95, 1.0])[None, None] * dots[..., None]
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(os.path.join(A, "map_base.png"))
print("map", W, H, "rockies T", float(T[np.unravel_index(np.argmax(rock * L), rock.shape)]))
# map projection constants for the 3D scene
json.dump({"lon0": LON0, "lon1": LON1, "lat0": LAT0, "lat1": LAT1, "W": W, "H": H, "cosl": COSL},
          open(os.path.join(A, "map_meta.json"), "w"))
