from services.errors import StudioError
from services.tools import probe


def audio_inputs(store, project):
    result = {}
    for key in ("narration", "music"):
        item = project.get("audio", {}).get(key)
        if item:
            path = store.resolve(item["path"])
            if not probe(path)["has_audio"]:
                raise StudioError("File giọng đọc/nhạc không có âm thanh. Hãy tải file khác.")
            result[key] = path
    if "music" in result and not project["audio"].get("music_rights_confirmed"):
        raise StudioError("Hãy xác nhận quyền sử dụng nhạc nền trước khi xuất.")
    return result


def mix_filter(project, inputs, total):
    """Giọng đọc thay tiếng gốc. Nhạc nền trộn ở âm lượng người dùng chọn."""
    filters, labels, next_index = [], [], 1
    if "narration" in inputs:
        filters.append(f"[{next_index}:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={total}[voice]")
        labels.append("[voice]")
        next_index += 1
    else:
        filters.append(f"[0:a]atrim=duration={total}[base]")
        labels.append("[base]")
    if "music" in inputs:
        volume = float(project["settings"].get("music_volume", 0.15))
        if not 0 <= volume <= 1:
            raise StudioError("Âm lượng nhạc nền phải từ 0 đến 1.")
        filters.append(f"[{next_index}:a]aresample=48000,aformat=channel_layouts=stereo,volume={volume},atrim=duration={total}[music]")
        labels.append("[music]")
    filters.append("".join(labels) + f"amix=inputs={len(labels)}:duration=longest:normalize=0,alimiter=limit=0.95:latency=1,atrim=duration={total}[outa]")
    return filters
