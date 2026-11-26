"""Equirectangular Earth color map from Natural Earth 1:50m land polygons (public domain)."""
import json, os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
H = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(H, "..", "assets")
W, HH = 8192, 4096
geo = json.load(open(os.path.join(A, "ne_50m_land.geojson")))
mask = Image.new("L", (W, HH), 0)
d = ImageDraw.Draw(mask)
def px(lon, lat):
    return ((lon + 180) / 360 * W, (90 - lat) / 180 * HH)
for f in geo["features"]:
    g = f["geometry"]
    polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
    for poly in polys:
        d.polygon([px(*c[:2]) for c in poly[0]], fill=255)
        for hole in poly[1:]:
            d.polygon([px(*c[:2]) for c in hole], fill=0)
m = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
lat = np.linspace(90, -90, HH)[:, None] * np.ones((1, W))
rng = np.random.default_rng(1)
def fbm(scale, octaves=5):
    out = np.zeros((HH // 8, W // 8), np.float32)
    amp = 1.0
    for o in range(octaves):
        n = rng.standard_normal((max(2, int(HH / (scale * 2 ** -o * 8))), max(2, int(W / (scale * 2 ** -o * 8))))).astype(np.float32)
        out += amp * np.asarray(Image.fromarray(n).resize((W // 8, HH // 8), Image.BICUBIC))
        amp *= 0.5
    return np.asarray(Image.fromarray(out).resize((W, HH), Image.BICUBIC))
nz = fbm(64)
nz = (nz - nz.min()) / (nz.max() - nz.min())
al = np.abs(lat)
green = np.array([0.20, 0.42, 0.16]); dgreen = np.array([0.10, 0.28, 0.10])
desert = np.array([0.78, 0.66, 0.42]); tundra = np.array([0.55, 0.55, 0.42]); ice = np.array([0.95, 0.97, 1.0])
dry = np.clip(1 - np.abs(al - 24) / 12, 0, 1) * np.clip(nz * 1.8 - 0.3, 0, 1)
land = green[None, None] * (1 - nz[..., None]) + dgreen[None, None] * nz[..., None]
land = land * (1 - dry[..., None]) + desert[None, None] * dry[..., None]
tun = np.clip((al - 55) / 12, 0, 1)
land = land * (1 - tun[..., None]) + tundra[None, None] * tun[..., None]
icef = np.maximum(np.clip((al - 66 - nz * 10) / 4, 0, 1), np.clip((-lat - 60) / 3, 0, 1))
land = land * (1 - icef[..., None]) + ice[None, None] * icef[..., None]
deep = np.array([0.02, 0.10, 0.30]); shallow = np.array([0.05, 0.32, 0.55])
coast = np.asarray(mask.filter(ImageFilter.GaussianBlur(18)), np.float32) / 255
ocean = deep[None, None] * (1 - coast[..., None]) + shallow[None, None] * np.clip(coast * 2.5, 0, 1)[..., None] + deep * 0
sea_ice = np.clip((al - 76) / 4, 0, 1)
ocean = ocean * (1 - sea_ice[..., None]) + ice[None, None] * sea_ice[..., None]
img = ocean * (1 - m[..., None]) + land * m[..., None]
os.makedirs(os.path.join(A, "textures"), exist_ok=True)
Image.fromarray((np.clip(img, 0, 1) ** (1 / 1.0) * 255).astype(np.uint8)).save(os.path.join(A, "textures", "earth.png"))
Image.fromarray((m * 255).astype(np.uint8)).save(os.path.join(A, "textures", "landmask.png"))
Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).resize((1024, 512)).save(os.path.join(H, "earth_preview.png"))
print("ok")
