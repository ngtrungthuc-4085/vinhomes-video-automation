import hashlib
import wave

import numpy as np
import pytest
from PIL import Image

from services.errors import StudioError
from services.media import import_media
from services.tools import binary, probe, run
from workflow.render import RESOLUTIONS, export_project


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decode_audio(path, destination):
    run([binary("ffmpeg"), "-v", "error", "-y", "-i", path, "-vn", "-c:a", "pcm_s16le", destination])
    with wave.open(str(destination)) as source:
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype=np.int16).astype(float)
        return np.sqrt(np.mean(samples ** 2))


@pytest.mark.parametrize("aspect,quality", [("9:16", "preview"), ("16:9", "preview"), ("9:16", "full"), ("16:9", "full")])
def test_mp4_video_audio_subtitles_and_sources_unchanged(store, demo, aspect, quality):
    demo["settings"]["aspect"] = aspect
    demo["audio"]["subtitles"] = "1\n00:00:00,200 --> 00:00:01,800\nĐảo Ngọc – Vịnh Mây – Bạch Vân"
    originals = {item["path"]: digest(store.resolve(item["path"])) for item in demo["media"]}
    progress = []
    output = export_project(store, demo, quality, lambda value, text: progress.append(value))
    metadata = probe(output)
    assert (metadata["width"], metadata["height"]) == RESOLUTIONS[(aspect, quality)]
    assert metadata["video_codec"] == "h264"
    assert metadata["audio_codec"] == "aac"
    assert metadata["duration"] == pytest.approx(6, abs=0.12)
    # Giải mã toàn bộ để phát hiện file bị hỏng, không chỉ kiểm tra metadata.
    run([binary("ffmpeg"), "-v", "error", "-xerror", "-i", output, "-f", "null", "-"])
    assert decode_audio(output, store.root / "sound.wav") > 100
    assert progress[-1] == 1
    assert store.load(demo["id"])["render"]["status"] == "done"
    for path, before in originals.items():
        assert digest(store.resolve(path)) == before
    # Cảnh video không tiếng (dài hơn tư liệu), và cảnh ảnh đều xuất được.
    assert len(list((store.project_dir(demo["id"]) / "cache").glob("*.mp4"))) == 3
    if aspect == "9:16" and quality == "preview":
        snapshot = store.root / "frame.png"
        run([binary("ffmpeg"), "-v", "error", "-y", "-ss", "1", "-i", output, "-frames:v", "1", snapshot])
        with Image.open(snapshot) as frame:
            # Phụ đề trắng nằm trong viền đen phía dưới, không phải nội dung nguồn.
            lower = np.array(frame)[530:605]
            assert (lower.min(axis=2) > 190).sum() > 100


def test_scene_cache_reuse_and_single_scene_edit(store, demo):
    first = export_project(store, demo)
    before = {p.name: p.stat().st_mtime_ns for p in (store.project_dir(demo["id"]) / "cache").glob("*.mp4")}
    second = export_project(store, demo)
    assert second != first and first.exists()
    assert demo["exports"][-1]["cache_hits"] == 3
    demo["scenes"][1]["duration"] = 2.4
    third = export_project(store, demo)
    assert probe(third)["duration"] == pytest.approx(6.4, abs=0.12)
    assert demo["exports"][-1]["cache_hits"] == 2
    for name, timestamp in before.items():
        assert (store.project_dir(demo["id"]) / "cache" / name).stat().st_mtime_ns == timestamp


def test_narration_music_rights_and_silence(store, demo):
    source = store.root / "voice.wav"
    run([binary("ffmpeg"), "-v", "error", "-y", "-f", "lavfi", "-i", "sine=frequency=660:sample_rate=48000", "-t", "1", source])
    item = import_media(store, demo, source.name, source.read_bytes(), audio=True)
    demo["audio"].update(narration=item, music=item, music_rights_confirmed=False)
    with pytest.raises(StudioError, match="quyền sử dụng"):
        export_project(store, demo)
    assert store.load(demo["id"])["render"]["status"] == "failed"
    demo["audio"]["music_rights_confirmed"] = True
    output = export_project(store, demo)
    assert decode_audio(output, store.root / "music.wav") > 100
    demo["audio"] = {}
    demo["settings"]["keep_original_audio"] = False
    demo["settings"]["fade"] = True
    silent = export_project(store, demo)
    assert decode_audio(silent, store.root / "silent.wav") < 1


def test_invalid_media_and_subtitle_timing(store, demo):
    with pytest.raises(StudioError):
        import_media(store, demo, "broken.mp4", b"not a video")
    with pytest.raises(StudioError):
        import_media(store, demo, "unsupported.exe", b"bad")
    demo["audio"]["subtitles"] = "1\n00:00:00,000 --> 00:00:09,000\nQuá dài"
    with pytest.raises(StudioError, match="vượt thời lượng"):
        export_project(store, demo)
