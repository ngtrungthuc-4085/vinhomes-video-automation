import math
import re
import uuid

from services.errors import StudioError


def scene(text="", duration=6):
    return {"id": uuid.uuid4().hex, "text": text.strip(), "duration": duration,
            "media_id": None, "start": 0.0, "confirmed": False}


def split_script(script, target_duration=60):
    script = script.strip()
    if not script:
        raise StudioError("Hãy nhập kịch bản trước khi chia cảnh.")
    if not math.isfinite(target_duration) or not 1 <= target_duration <= 3600:
        raise StudioError("Tổng thời lượng phải từ 1 đến 3600 giây.")
    sentences = [s.strip() for s in re.split(r"(?<=[.!?…])\s+|\n+", script) if s.strip()]
    # Giữ nguyên nội dung; chỉ chia câu dài thành cụm từ, không thêm thông tin.
    chunks = []
    for sentence in sentences:
        words = sentence.split()
        chunks.extend(" ".join(words[i:i + 28]) for i in range(0, len(words), 28))
    total_words = sum(len(c.split()) for c in chunks)
    return [scene(c, target_duration * len(c.split()) / total_words) for c in chunks]


def suggest_media(text, media):
    words = set(re.findall(r"\w+", text.casefold()))
    ranked = []
    for item in media:
        if item["kind"] == "audio":
            continue
        labels = " ".join(str(item.get(k, "")) for k in ("name", "description", "location", "tags"))
        score = len(words & set(re.findall(r"\w+", labels.casefold())))
        if score:
            ranked.append((score, item["id"]))
    return [item_id for _, item_id in sorted(ranked, reverse=True)]


def validate_scenes(project):
    if not project["scenes"]:
        raise StudioError("Chưa có cảnh. Hãy chia kịch bản hoặc thêm cảnh thủ công.")
    media = {item["id"]: item for item in project["media"] if item["kind"] != "audio"}
    total = 0
    for index, item in enumerate(project["scenes"], 1):
        if item["media_id"] not in media:
            raise StudioError(f"Cảnh {index} chưa chọn tư liệu.")
        if not item.get("confirmed"):
            raise StudioError(f"Hãy xác nhận tư liệu cho cảnh {index} trước khi xuất.")
        duration, start = float(item["duration"]), float(item["start"])
        if not math.isfinite(duration) or not 0.2 <= duration <= 600:
            raise StudioError(f"Thời lượng cảnh {index} phải từ 0,2 đến 600 giây.")
        if not math.isfinite(start) or start < 0:
            raise StudioError(f"Điểm bắt đầu cảnh {index} không hợp lệ.")
        source = media[item["media_id"]]
        if source["kind"] == "video" and start >= source["duration"]:
            raise StudioError(f"Điểm bắt đầu cảnh {index} nằm ngoài video.")
        total += duration
    if total > 3600:
        raise StudioError("MVP hỗ trợ video tối đa 60 phút.")
    return media
