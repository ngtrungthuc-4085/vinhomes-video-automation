import os
import re
from pathlib import Path

from PIL import ImageFont

from services.errors import StudioError


def font_path():
    override = os.environ.get("VIDEO_STUDIO_FONT")
    candidates = [override] if override else []
    candidates += [str(Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts/arial.ttf"),
                   "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                   "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                   "/System/Library/Fonts/Supplemental/Arial.ttf"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return Path(candidate)
    raise StudioError("Không tìm thấy font hỗ trợ tiếng Việt. Cài Arial/Noto Sans hoặc đặt VIDEO_STUDIO_FONT đến file .ttf.")


def ass_escape(text):
    # Không cho nội dung người dùng chèn mã định dạng ASS.
    return text.replace("\\", "＼").replace("{", "(").replace("}", ")").replace("\r", "").replace("\n", r"\N")


def ass_time(seconds):
    centiseconds = round(seconds * 100)
    return f"{centiseconds // 360000}:{centiseconds // 6000 % 60:02}:{centiseconds // 100 % 60:02}.{centiseconds % 100:02}"


def wrap_text(text, width, font):
    lines = []
    for paragraph in text.splitlines() or [""]:
        current = ""
        for word in paragraph.split():
            candidate = f"{current} {word}".strip()
            if current and font.getlength(candidate) > width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
    return "\n".join(lines)


def read_srt(text):
    text = text.lstrip("\ufeff").replace("\r\n", "\n").strip()
    result = []
    pattern = re.compile(r"^(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2,}):(\d{2}):(\d{2})[,.](\d{3})$")
    for block in re.split(r"\n\s*\n", text):
        lines = block.strip().splitlines()
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        match = pattern.fullmatch(lines[0].strip()) if lines else None
        if not match or len(lines) < 2:
            raise StudioError("File SRT không hợp lệ. Cần mốc HH:MM:SS,mmm --> HH:MM:SS,mmm và nội dung.")
        parts = list(map(int, match.groups()))
        if any(parts[i] >= 60 for i in (1, 2, 5, 6)):
            raise StudioError("Phút và giây trong SRT phải nhỏ hơn 60.")
        start = parts[0] * 3600 + parts[1] * 60 + parts[2] + parts[3] / 1000
        end = parts[4] * 3600 + parts[5] * 60 + parts[6] + parts[7] / 1000
        if end <= start or (result and start < result[-1]["end"]):
            raise StudioError("Mốc SRT phải tăng dần, không chồng lấn và có thời lượng dương.")
        caption = "\n".join(lines[1:]).strip()
        if not caption:
            raise StudioError("Một đoạn phụ đề trong SRT không có nội dung.")
        result.append({"start": start, "end": end, "text": caption})
    if not result:
        raise StudioError("File SRT không có phụ đề.")
    return result


def write_ass(path, project, width, height, total, font_file):
    size = max(16, round(min(width, height) * 0.044))
    font = ImageFont.truetype(str(font_file), size)
    family = font.getname()[0]
    margin = round(width * 0.07)
    vertical = round(height * 0.08)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,{family},{size},&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,{margin},{margin},{vertical},1
Style: Title,{family},{size + 4},&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,8,{margin},{margin},{vertical},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    def add(start, end, text, style="Caption"):
        if text.strip() and end > start:
            wrapped = wrap_text(text, width - 2 * margin, font)
            events.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},{style},,0,0,0,,{ass_escape(wrapped)}")
    settings = project["settings"]
    if settings.get("title"):
        add(0, min(4, total), settings["title"], "Title")
    if settings.get("cta"):
        add(max(0, total - 4), total, settings["cta"], "Title")
    srt = project.get("audio", {}).get("subtitles", "")
    if srt:
        for caption in read_srt(srt):
            if caption["start"] >= total or caption["end"] > total + 0.05:
                raise StudioError("Mốc SRT vượt thời lượng video. Hãy sửa SRT hoặc tăng thời lượng cảnh.")
            add(caption["start"], min(total, caption["end"]), caption["text"])
    elif settings.get("script_captions"):
        cursor = 0
        for item in project["scenes"]:
            add(cursor, cursor + float(item["duration"]), item["text"])
            cursor += float(item["duration"])
    Path(path).write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return bool(events)
