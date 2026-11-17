import os
import re
import json
import math
import wave
import struct
from pathlib import Path

import numpy as np
import edge_tts
import uvicorn
from PIL import Image, ImageDraw, ImageFont
from starlette.applications import Starlette
from starlette.responses import FileResponse, JSONResponse
from starlette.routing import Mount, Route
from mcp.server.fastmcp import FastMCP

from scripts.stage.puppet import generate_all_horror_assets

mcp = FastMCP("horror-2d-cartoons-mcp")

IS_RENDER = os.getenv("RENDER", "false").lower() == "true"
QUALITY = os.getenv("RENDER_QUALITY", "720p" if IS_RENDER else "1080p").lower()
TARGET_W, TARGET_H = (720, 1280) if QUALITY == "720p" else (1080, 1920)
FPS = 24 if IS_RENDER else 30
PUBLIC_BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:8000").rstrip("/")


def _slugify(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower()).strip("_")[:50] or "horror_short"


def _project_dir(slug: str) -> Path:
    p = Path("projects") / _slugify(slug)
    p.mkdir(parents=True, exist_ok=True)
    return p


@mcp.tool()
def init_horror_project(topic: str) -> dict:
    """Initialize a workspace folder for a 60-second 2D horror cartoon short."""
    slug = _slugify(topic)
    p = _project_dir(slug)
    (p / "audio").mkdir(exist_ok=True)
    return {"status": "ready", "topic": topic, "project_slug": slug, "workspace": str(p.resolve())}


@mcp.tool()
def build_horror_assets(project_slug: str) -> dict:
    """Generate local 2D horror backgrounds and layered Night Guard & Shadow Stalker sprites."""
    p = _project_dir(project_slug)
    manifest = generate_all_horror_assets(p, TARGET_W, TARGET_H)
    return {"status": "assets_ready", "project_slug": project_slug, "manifest": manifest}


@mcp.tool()
def save_horror_short_json(
    project_slug: str,
    title: str,
    description: str,
    full_voiceover: str,
    beats_json: str,
) -> dict:
    """Save the 60-beat horror timeline (short.json) for stage rendering."""
    p = _project_dir(project_slug)
    beats = json.loads(beats_json)
    if len(beats) < 60:
        while len(beats) < 60:
            c = dict(beats[-1])
            c["second"] = len(beats)
            beats.append(c)
    beats = beats[:60]
    for i, b in enumerate(beats):
        b["second"] = i

    data = {
        "title": title,
        "description": description,
        "full_voiceover": full_voiceover.strip(),
        "beats": beats,
    }
    out = p / "short.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "saved", "beat_count": len(beats), "short_json": str(out)}


@mcp.tool()
async def generate_horror_voiceover(project_slug: str, voice: str = "en-US-ChristopherNeural") -> dict:
    """Generate deep horror voiceover audio (audio/voice.mp3) via free Edge-TTS."""
    p = _project_dir(project_slug)
    short_data = json.loads((p / "short.json").read_text(encoding="utf-8"))
    text = re.sub(r"[\r\n\t]+", " ", short_data["full_voiceover"]).strip()
    out_mp3 = p / "audio" / "voice.mp3"
    out_mp3.parent.mkdir(exist_ok=True)

    for v in list(dict.fromkeys([voice, "en-US-ChristopherNeural", "en-US-AndrewNeural", "en-US-GuyNeural"])):
        try:
            comm = edge_tts.Communicate(text, v, pitch="-6Hz", rate="+4%")
            await comm.save(str(out_mp3))
            if out_mp3.exists() and out_mp3.stat().st_size > 1000:
                return {"status": "generated", "voice": v, "audio_path": str(out_mp3)}
        except Exception:
            out_mp3.unlink(missing_ok=True)
    raise RuntimeError("Edge-TTS failed to synthesize voiceover.")


def _synth_horror_sfx(kind: str, out_wav: Path, duration: float = 0.6):
    sr = 44100
    n = int(sr * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    if kind == "heartbeat":
        env = np.exp(-t * 14.0) + 0.7 * np.exp(-np.maximum(0, t - 0.22) * 14.0)
        sig = 0.85 * np.sin(2 * np.pi * 52.0 * t) * env
    elif kind == "stinger":
        env = np.exp(-t * 3.5)
        sig = 0.5 * np.sin(2 * np.pi * (440.0 + 900.0 * t) * t) * env + 0.4 * np.sin(2 * np.pi * 65.0 * t) * env
    else:
        sig = 0.35 * np.sin(2 * np.pi * 48.0 * t) + 0.2 * np.sin(2 * np.pi * 72.0 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.4 * t))
    pcm = np.int16(np.clip(sig, -1.0, 1.0) * 32767)
    with wave.open(str(out_wav), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def _compose_beat_frame(p: Path, beat: dict) -> Image.Image:
    bg_name = beat.get("bg", "corridor")
    bg_path = p / "bg" / f"{bg_name}.png"
    if not bg_path.exists():
        bg_path = p / "bg" / "corridor.png"
    canvas = Image.open(bg_path).convert("RGBA").resize((TARGET_W, TARGET_H))

    pose = beat.get("stalker_pose", "hidden")
    stalker_path = p / "puppets" / "shadow_stalker" / f"{pose}.png"
    if stalker_path.exists():
        st = Image.open(stalker_path).convert("RGBA")
        sw = int(TARGET_W * 0.55)
        sh = int(st.height * (sw / st.width))
        st = st.resize((sw, sh), Image.Resampling.LANCZOS)
        canvas.alpha_composite(st, (int(TARGET_W * 0.42), int(TARGET_H * 0.18)))

    body = Image.open(p / "puppets" / "night_guard" / "body.png").convert("RGBA")
    head = Image.open(p / "puppets" / "night_guard" / "head.png").convert("RGBA")
    face_name = beat.get("guard_face", "nervous")
    face_path = p / "puppets" / "night_guard" / "faces" / f"{face_name}.png"
    if not face_path.exists():
        face_path = p / "puppets" / "night_guard" / "faces" / "nervous.png"
    face = Image.open(face_path).convert("RGBA")

    scale = TARGET_W / 1080.0
    bw, bh = int(body.width * scale), int(body.height * scale)
    hw, hh = int(head.width * scale), int(head.height * scale)
    gx = int(TARGET_W * 0.12)
    gy = int(TARGET_H * 0.46)
    canvas.alpha_composite(body.resize((bw, bh)), (gx, gy))
    canvas.alpha_composite(head.resize((hw, hh)), (gx + int(45 * scale), gy - int(225 * scale)))
    canvas.alpha_composite(face.resize((hw, hh)), (gx + int(45 * scale), gy - int(225 * scale)))

    cap = (beat.get("caption") or "").strip().upper()
    if cap:
        draw = ImageDraw.Draw(canvas)
        font = ImageFont.load_default()
        for fp in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "C:/Windows/Fonts/impact.ttf"]:
            if os.path.exists(fp):
                font = ImageFont.truetype(fp, int(62 * scale))
                break
        bbox = draw.textbbox((0, 0), cap, font=font)
        tw = bbox[2] - bbox[0]
        tx = (TARGET_W - tw) // 2
        ty = int(TARGET_H * 0.78)
        draw.text((tx + 4, ty + 4), cap, font=font, fill=(0, 0, 0, 240))
        draw.text((tx, ty), cap, font=font, fill=(235, 35, 45, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255))

    return canvas.convert("RGB")


@mcp.tool()
def render_horror_stage_video(project_slug: str) -> dict:
    """Render the 60-second horror cartoon short to render.mp4 and return a download URL."""
    try:
        from moviepy import AudioFileClip, CompositeAudioClip, VideoClip, concatenate_videoclips
    except ImportError:
        from moviepy.editor import AudioFileClip, CompositeAudioClip, VideoClip, concatenate_videoclips

    p = _project_dir(project_slug)
    short_data = json.loads((p / "short.json").read_text(encoding="utf-8"))
    audio_dir = p / "audio"
    audio_dir.mkdir(exist_ok=True)

    hb_wav = audio_dir / "heartbeat.wav"
    st_wav = audio_dir / "stinger.wav"
    dr_wav = audio_dir / "drone.wav"
    _synth_horror_sfx("heartbeat", hb_wav, 0.55)
    _synth_horror_sfx("stinger", st_wav, 0.85)

    voice_clip = AudioFileClip(str(audio_dir / "voice.mp3"))
    total_dur = max(voice_clip.duration, 20.0)
    _synth_horror_sfx("drone", dr_wav, total_dur + 1.0)

    beats = short_data["beats"]
    sec_dur = total_dur / len(beats)
    clips = []
    audio_tracks = [voice_clip, AudioFileClip(str(dr_wav)).subclipped(0, total_dur).with_volume_scaled(0.22)]

    for i, beat in enumerate(beats):
        frame_img = _compose_beat_frame(p, beat)
        cam = beat.get("camera_move", "zoom_in" if i % 2 == 0 else "zoom_out")
        fx = beat.get("fx", "none")

        def make_fn(img=frame_img, move=cam, effect=fx, dur=sec_dur):
            def get_frame(t):
                prog = min(max(t / max(dur, 1e-4), 0.0), 1.0)
                zoom = 1.0 + 0.07 * prog if move == "zoom_in" else 1.07 - 0.07 * prog
                dx = math.sin(t * 70.0) * 14.0 if effect == "shake" else 0.0
                cw, ch = TARGET_W / zoom, TARGET_H / zoom
                left = max(0.0, min(TARGET_W - cw, (TARGET_W - cw) / 2.0 + dx))
                top = max(0.0, min(TARGET_H - ch, (TARGET_H - ch) / 2.0))
                arr = np.array(img.crop((left, top, left + cw, top + ch)).resize((TARGET_W, TARGET_H)), dtype=np.float32)
                if effect == "flash_red" and prog < 0.3:
                    a = (1.0 - prog / 0.3) * 0.55
                    arr[..., 0] = arr[..., 0] * (1.0 - a) + 255.0 * a
                    arr[..., 1] *= (1.0 - a)
                    arr[..., 2] *= (1.0 - a)
                return np.uint8(np.clip(arr, 0, 255))

            return get_frame

        clips.append(VideoClip(make_fn(), duration=sec_dur))
        sfx = beat.get("sfx", "none")
        if sfx == "heartbeat":
            audio_tracks.append(AudioFileClip(str(hb_wav)).with_start(i * sec_dur).with_volume_scaled(0.55))
        elif sfx == "stinger":
            audio_tracks.append(AudioFileClip(str(st_wav)).with_start(i * sec_dur).with_volume_scaled(0.65))

    final_vid = concatenate_videoclips(clips, method="compose").with_audio(CompositeAudioClip(audio_tracks))
    out_mp4 = p / "render.mp4"
    final_vid.write_videofile(str(out_mp4), fps=FPS, codec="libx264", audio_codec="aac", preset="ultrafast", threads=2)

    slug = _slugify(project_slug)
    return {
        "status": "completed",
        "video_path": str(out_mp4.resolve()),
        "download_url": f"{PUBLIC_BASE_URL}/download/{slug}/render.mp4",
    }


async def health(_request):
    return JSONResponse({"status": "ok", "service": "horror-2d-cartoons-mcp"})


async def download_video(request):
    slug = _slugify(request.path_params["slug"])
    mp4_path = Path("projects") / slug / "render.mp4"
    if not mp4_path.exists():
        return JSONResponse({"error": "render.mp4 not found"}, status_code=404)
    return FileResponse(str(mp4_path), media_type="video/mp4", filename=f"{slug}.mp4")


app = Starlette(
    routes=[
        Route("/health", health),
        Route("/download/{slug}/render.mp4", download_video),
        Mount("/", app=mcp.sse_app()),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
