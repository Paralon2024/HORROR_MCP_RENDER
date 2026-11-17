import json
from pathlib import Path
from PIL import Image, ImageDraw


def _draw_corridor(w: int, h: int, out_path: Path):
    img = Image.new("RGB", (w, h), (10, 12, 18))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        shade = int(10 + 18 * (y / h))
        draw.line([(0, y), (w, y)], fill=(shade, shade + 2, shade + 8))
    draw.polygon([(0, 0), (w // 3, h // 3), (w // 3, int(h * 0.72)), (0, h)], fill=(16, 18, 26))
    draw.polygon([(w, 0), (w * 2 // 3, h // 3), (w * 2 // 3, int(h * 0.72)), (w, h)], fill=(16, 18, 26))
    draw.rectangle([w // 3, h // 3, w * 2 // 3, int(h * 0.72)], fill=(6, 7, 12), outline=(45, 50, 65), width=4)
    draw.ellipse([w // 2 - 90, int(h * 0.24), w // 2 + 90, int(h * 0.29)], fill=(180, 210, 230))
    img.save(out_path, "PNG")


def _draw_security_room(w: int, h: int, out_path: Path):
    img = Image.new("RGB", (w, h), (8, 16, 14))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, int(h * 0.65), w, h], fill=(18, 22, 26))
    for mx in (int(w * 0.14), int(w * 0.52)):
        draw.rectangle([mx, int(h * 0.35), mx + int(w * 0.34), int(h * 0.58)], fill=(12, 42, 32), outline=(60, 80, 75), width=6)
        for scan in range(int(h * 0.36), int(h * 0.57), 8):
            draw.line([(mx + 4, scan), (mx + int(w * 0.34) - 4, scan)], fill=(25, 85, 60))
    img.save(out_path, "PNG")


def _draw_woods(w: int, h: int, out_path: Path):
    img = Image.new("RGB", (w, h), (8, 10, 16))
    draw = ImageDraw.Draw(img)
    draw.ellipse([w // 2 - 140, int(h * 0.12), w // 2 + 140, int(h * 0.12) + 280], fill=(215, 220, 235))
    for tx in range(40, w, 150):
        draw.rectangle([tx, int(h * 0.15), tx + 38, h], fill=(5, 6, 10))
    img.save(out_path, "PNG")


def _build_night_guard(puppet_dir: Path):
    puppet_dir.mkdir(parents=True, exist_ok=True)
    faces_dir = puppet_dir / "faces"
    faces_dir.mkdir(exist_ok=True)

    body = Image.new("RGBA", (420, 520), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([60, 20, 360, 500], radius=45, fill=(28, 42, 68, 255), outline=(10, 14, 22, 255), width=8)
    bd.rectangle([185, 20, 235, 320], fill=(18, 26, 44, 255))
    bd.polygon([(245, 95), (295, 95), (285, 145), (255, 145)], fill=(230, 195, 65, 255))
    body.save(puppet_dir / "body.png", "PNG")

    head = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
    hd = ImageDraw.Draw(head)
    hd.ellipse([45, 45, 275, 295], fill=(232, 192, 162, 255), outline=(15, 15, 20, 255), width=8)
    hd.chord([38, 20, 282, 165], start=180, end=360, fill=(24, 36, 58, 255), outline=(10, 12, 18, 255), width=7)
    hd.rectangle([30, 92, 290, 112], fill=(15, 20, 32, 255))
    head.save(puppet_dir / "head.png", "PNG")

    for expr in ("neutral", "nervous", "confused", "shocked", "shouting", "possessed"):
        fimg = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fimg)
        eye_color = (220, 20, 30, 255) if expr == "possessed" else (255, 255, 255, 255)
        pupil_r = 6 if expr in ("nervous", "shocked") else 11
        for ex in (122, 198):
            fd.ellipse([ex - 22, 132, ex + 22, 176], fill=eye_color, outline=(15, 15, 20, 255), width=5)
            fd.ellipse([ex - pupil_r, 154 - pupil_r, ex + pupil_r, 154 + pupil_r], fill=(15, 15, 20, 255))
        if expr in ("shocked", "shouting"):
            fd.ellipse([132, 205, 188, 260], fill=(45, 12, 18, 255), outline=(15, 15, 20, 255), width=5)
        elif expr == "nervous":
            fd.arc([125, 215, 195, 250], start=190, end=350, fill=(15, 15, 20, 255), width=6)
            fd.ellipse([235, 130, 252, 162], fill=(110, 200, 255, 220))
        else:
            fd.line([(130, 225), (190, 225)], fill=(15, 15, 20, 255), width=6)
        fimg.save(faces_dir / f"{expr}.png", "PNG")


def _build_shadow_stalker(puppet_dir: Path):
    puppet_dir.mkdir(parents=True, exist_ok=True)
    for pose in ("hidden", "lurking", "peeking", "lunging"):
        simg = Image.new("RGBA", (480, 760), (0, 0, 0, 0))
        if pose != "hidden":
            sd = ImageDraw.Draw(simg)
            scale = 1.25 if pose == "lunging" else 1.0
            cx = 240
            sd.polygon(
                [(cx, 40), (cx - int(110 * scale), 720), (cx + int(110 * scale), 720)],
                fill=(8, 8, 12, 235),
            )
            sd.ellipse([cx - 65, 35, cx + 65, 175], fill=(5, 5, 8, 245))
            sd.ellipse([cx - 34, 92, cx - 12, 108], fill=(255, 35, 35, 255))
            sd.ellipse([cx + 12, 92, cx + 34, 108], fill=(255, 35, 35, 255))
        simg.save(puppet_dir / f"{pose}.png", "PNG")


def generate_all_horror_assets(project_dir: Path, width: int = 720, height: int = 1280) -> dict:
    bg_dir = project_dir / "bg"
    puppets_dir = project_dir / "puppets"
    bg_dir.mkdir(parents=True, exist_ok=True)
    puppets_dir.mkdir(parents=True, exist_ok=True)

    _draw_corridor(width, height, bg_dir / "corridor.png")
    _draw_security_room(width, height, bg_dir / "security_room.png")
    _draw_woods(width, height, bg_dir / "woods.png")

    _build_night_guard(puppets_dir / "night_guard")
    _build_shadow_stalker(puppets_dir / "shadow_stalker")

    manifest = {
        "backgrounds": ["corridor", "security_room", "woods"],
        "puppets": ["night_guard", "shadow_stalker"],
    }
    (puppets_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
