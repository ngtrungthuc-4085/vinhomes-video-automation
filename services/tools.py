import json
import os
import shutil
import subprocess
from pathlib import Path

from services.errors import StudioError


def binary(name):
    candidate = os.environ.get(f"{name.upper()}_BINARY", name)
    found = shutil.which(candidate)
    if not found:
        raise StudioError(f"Không tìm thấy {name}. Cài FFmpeg, thêm thư mục bin vào PATH rồi mở lại ứng dụng.")
    return found


def run(args, cwd=None, timeout=900):
    try:
        result = subprocess.run([str(arg) for arg in args], cwd=cwd, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise StudioError("Xử lý quá thời gian. Hãy dùng bản xem thử hoặc giảm thời lượng cảnh.") from exc
    except OSError as exc:
        raise StudioError("Không chạy được công cụ xử lý. Kiểm tra cài đặt và quyền truy cập file.") from exc
    if result.returncode:
        detail = result.stderr[-3500:]
        raise StudioError(f"Xử lý không thành công. Kiểm tra file đầu vào và cấu hình FFmpeg.\n{detail}")
    return result.stdout


def probe(path):
    path = Path(path)
    if not path.is_file():
        raise StudioError("Không tìm thấy file tư liệu. Hãy tải lại file.")
    data = json.loads(run([binary("ffprobe"), "-v", "error", "-show_streams", "-show_format", "-of", "json", path], timeout=60))
    video = next((s for s in data["streams"] if s["codec_type"] == "video"), None)
    return {"duration": float(data.get("format", {}).get("duration", 0)),
            "width": video.get("width", 0) if video else 0,
            "height": video.get("height", 0) if video else 0,
            "has_video": video is not None,
            "has_audio": any(s["codec_type"] == "audio" for s in data["streams"]),
            "video_codec": video.get("codec_name") if video else None,
            "audio_codec": next((s.get("codec_name") for s in data["streams"] if s["codec_type"] == "audio"), None)}


def check_tools():
    for tool in ("ffmpeg", "ffprobe"):
        run([binary(tool), "-version"], timeout=15)
    encoders = run([binary("ffmpeg"), "-hide_banner", "-encoders"], timeout=15)
    filters = run([binary("ffmpeg"), "-hide_banner", "-filters"], timeout=15)
    if "libx264" not in encoders or " aac " not in encoders:
        raise StudioError("Bản FFmpeg cần bộ mã hóa libx264 và AAC. Hãy cài bản đầy đủ.")
    if " subtitles " not in filters:
        raise StudioError("Bản FFmpeg cần bộ lọc subtitles (libass) để thêm chữ tiếng Việt.")
