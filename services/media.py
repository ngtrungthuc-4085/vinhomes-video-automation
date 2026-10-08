import hashlib
from pathlib import Path

from PIL import Image, ImageOps

from services.errors import StudioError
from services.tools import binary, probe, run

VISUAL_EXTENSIONS = {".mp4", ".mov", ".jpg", ".jpeg", ".png"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}


def import_media(store, project, name, data, audio=False):
    extension = Path(name).suffix.lower()
    if extension not in (AUDIO_EXTENSIONS if audio else VISUAL_EXTENSIONS):
        raise StudioError("Định dạng không hỗ trợ. Dùng MP4, MOV, JPG, PNG hoặc file âm thanh MP3/WAV/M4A/AAC/OGG.")
    if not data:
        raise StudioError("File rỗng, hãy chọn file khác.")
    digest = hashlib.sha256(data).hexdigest()
    directory = store.root / "inputs/media" / project["id"]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{digest}{extension}"
    created = not path.exists()
    if created:
        path.write_bytes(data)
    thumbnail = directory / f"{digest}.jpg"
    try:
        if extension in {".jpg", ".jpeg", ".png"}:
            with Image.open(path) as source:
                image = ImageOps.exif_transpose(source).convert("RGB")
                metadata = {"duration": 0, "width": image.width, "height": image.height,
                            "has_audio": False, "has_video": True}
                image.thumbnail((480, 480))
                image.save(thumbnail, "JPEG")
            kind = "image"
        else:
            metadata = probe(path)
            if audio:
                if not metadata["has_audio"]:
                    raise StudioError("File không có luồng âm thanh.")
                kind = "audio"
            else:
                if not metadata["has_video"] or metadata["duration"] <= 0:
                    raise StudioError("File không chứa video có thời lượng hợp lệ.")
                run([binary("ffmpeg"), "-v", "error", "-y", "-i", path, "-frames:v", "1",
                     "-vf", "scale=480:480:force_original_aspect_ratio=decrease", thumbnail], timeout=60)
                kind = "video"
    except Exception:
        if created:
            path.unlink(missing_ok=True)
            thumbnail.unlink(missing_ok=True)
        raise
    return {"id": digest, "name": Path(name).name, "path": path.relative_to(store.root).as_posix(),
            "thumbnail": thumbnail.relative_to(store.root).as_posix() if kind != "audio" else None,
            "kind": kind, "description": "", "location": "", "tags": "", **metadata}
