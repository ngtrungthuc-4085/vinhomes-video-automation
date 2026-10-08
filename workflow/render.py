import hashlib
import json
import re
import shutil
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from services.audio import audio_inputs, mix_filter
from services.errors import StudioError
from services.subtitles import font_path, write_ass
from services.tools import binary, check_tools, probe, run
from workflow.scenes import validate_scenes

RESOLUTIONS = {("9:16", "preview"): (360, 640), ("16:9", "preview"): (640, 360),
               ("9:16", "full"): (1080, 1920), ("16:9", "full"): (1920, 1080)}


def render_scene(store, project, scene, source, resolution, quality):
    path = store.resolve(source["path"])
    if not path.is_file():
        raise StudioError("Tư liệu bị thiếu trên ổ đĩa. Hãy tải lại file.")
    width, height = resolution
    duration = float(scene["duration"])
    original = project["settings"].get("keep_original_audio", True)
    fade = project["settings"].get("fade", True)
    cache_key = {"version": 1, "source": source["id"], "stat": [path.stat().st_size, path.stat().st_mtime_ns],
                 "start": scene["start"], "duration": duration, "size": resolution,
                 "audio": original, "fade": fade, "quality": quality}
    digest = hashlib.sha256(json.dumps(cache_key, sort_keys=True).encode()).hexdigest()
    cache = store.project_dir(project["id"]) / "cache"
    cache.mkdir(exist_ok=True)
    output = cache / f"{digest}.mp4"
    if output.exists():
        try:
            data = probe(output)
            if data["has_audio"] and data["has_video"]:
                return output, True
        except StudioError:
            pass
        output.unlink()
    temporary = cache / f"{digest}.part.mp4"
    command = [binary("ffmpeg"), "-hide_banner", "-loglevel", "error", "-y", "-threads", "2"]
    if source["kind"] == "image":
        command += ["-loop", "1", "-framerate", "30", "-i", path]
    else:
        command += ["-ss", str(scene["start"]), "-i", path]
    use_audio = source["kind"] == "video" and source["has_audio"] and original
    if not use_audio:
        command += ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    video_filter = (f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2,"
                    f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1,fps=30,"
                    f"tpad=stop_mode=clone:stop_duration={duration},trim=duration={duration},setpts=PTS-STARTPTS,format=yuv420p")
    audio_filter = f"aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={duration},asetpts=PTS-STARTPTS"
    if fade:
        transition = min(0.2, duration / 4)
        video_filter += f",fade=t=in:st=0:d={transition},fade=t=out:st={duration-transition}:d={transition}"
        audio_filter += f",afade=t=in:st=0:d={transition},afade=t=out:st={duration-transition}:d={transition}"
    command += ["-filter_threads", "2", "-map", "0:v:0", "-map", "0:a:0" if use_audio else "1:a:0",
                "-vf", video_filter, "-af", audio_filter, "-t", str(duration),
                "-c:v", "libx264", "-threads", "2", "-preset", "veryfast", "-crf", "28" if quality == "preview" else "20",
                "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2", "-movflags", "+faststart", temporary]
    try:
        run(command)
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    return output, False


def export_project(store, project, quality="preview", progress=None):
    progress = progress or (lambda value, message: None)
    def update(value, message, status="running"):
        project["render"] = {"status": status, "progress": value, "message": message}
        store.save(project)
        progress(value, message)
    try:
        check_tools()
        media = validate_scenes(project)
        resolution = RESOLUTIONS.get((project["settings"].get("aspect"), quality))
        if resolution is None:
            raise StudioError("Tỷ lệ hoặc chất lượng xuất không hợp lệ.")
        audio = audio_inputs(store, project)
        total = sum(float(s["duration"]) for s in project["scenes"])
        # Xuất riêng mỗi lần, không ghi đè tư liệu hay phiên bản trước.
        directory = store.root / "outputs" / project["id"]
        directory.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^\w-]+", "-", project["name"], flags=re.UNICODE).strip("-")[:60] or "video"
        output = directory / f"{slug}_{datetime.now():%Y%m%d_%H%M%S}_{quality}_{uuid.uuid4().hex[:8]}.mp4"
        update(0.02, "Kiểm tra tư liệu và chuẩn bị chữ tiếng Việt…")
        cache_hits = 0
        with tempfile.TemporaryDirectory(prefix="render_", dir=store.project_dir(project["id"])) as temp:
            work = Path(temp)
            fonts = work / "fonts"
            fonts.mkdir()
            font = font_path()
            shutil.copy2(font, fonts / "studio.ttf")
            has_text = write_ass(work / "captions.ass", project, *resolution, total, font)
            segments = []
            for index, item in enumerate(project["scenes"]):
                update(0.05 + 0.65 * index / len(project["scenes"]), f"Đang dựng cảnh {index + 1}/{len(project['scenes'])}…")
                segment, cached = render_scene(store, project, item, media[item["media_id"]], resolution, quality)
                cache_hits += int(cached)
                # Tên tương đối ASCII tránh escaping đường dẫn FFmpeg trên Windows.
                local = work / f"scene_{index:04}.mp4"
                try:
                    local.hardlink_to(segment)
                except OSError:
                    shutil.copy2(segment, local)
                segments.append(f"file '{local.name}'")
            (work / "concat.txt").write_text("\n".join(segments), encoding="utf-8")
            update(0.74, "Ghép cảnh…")
            run([binary("ffmpeg"), "-v", "error", "-y", "-f", "concat", "-safe", "1", "-i", "concat.txt",
                 "-c", "copy", "joined.mp4"], cwd=work)
            update(0.82, "Thêm chữ và xử lý âm thanh…")
            command = [binary("ffmpeg"), "-v", "error", "-y", "-i", "joined.mp4"]
            if "narration" in audio:
                command += ["-i", audio["narration"]]
            if "music" in audio:
                command += ["-stream_loop", "-1", "-i", audio["music"]]
            filters = mix_filter(project, audio, total)
            command += ["-filter_complex_threads", "2", "-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[outa]"]
            if has_text:
                command += ["-vf", "subtitles=filename=captions.ass:fontsdir=fonts", "-filter_threads", "2",
                            "-c:v", "libx264", "-threads", "2", "-preset", "veryfast", "-crf", "28" if quality == "preview" else "20"]
            else:
                command += ["-c:v", "copy"]
            command += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2", "-t", str(total),
                        "-movflags", "+faststart", "final.mp4"]
            run(command, cwd=work, timeout=1800)
            update(0.96, "Kiểm tra file MP4…")
            metadata = probe(work / "final.mp4")
            if not metadata["has_video"] or not metadata["has_audio"] or abs(metadata["duration"] - total) > 0.3:
                raise StudioError("Video xuất không đạt kiểm tra hình/âm thanh/thời lượng.")
            if (metadata["width"], metadata["height"]) != resolution:
                raise StudioError("Kích thước video xuất không đúng cấu hình.")
            shutil.move(str(work / "final.mp4"), output)
        export = {"path": output.relative_to(store.root).as_posix(), "quality": quality,
                  "created_at": datetime.now().isoformat(), "cache_hits": cache_hits, **metadata}
        project["exports"].append(export)
        update(1.0, f"Xuất thành công. Tái sử dụng {cache_hits}/{len(project['scenes'])} cảnh đã dựng.", "done")
        return output
    except Exception as exc:
        project["render"] = {"status": "failed", "progress": project.get("render", {}).get("progress", 0), "message": str(exc)}
        store.save(project)
        if isinstance(exc, StudioError):
            raise
        raise StudioError(f"Không thể xuất video: {exc}") from exc
