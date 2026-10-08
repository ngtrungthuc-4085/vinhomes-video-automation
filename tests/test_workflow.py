import pytest

from services.ai_adapter import UnconfiguredAI
from services.errors import StudioError
from services.storage import ProjectStore
from services.subtitles import ass_escape, read_srt
from services.tools import binary
from workflow.scenes import scene, split_script, suggest_media, validate_scenes


def test_script_split_and_manual_edit_persist(store):
    project = store.create("Đảo Ngọc")
    project["script"] = "Khám phá Đảo Ngọc.\nGhé thăm Vịnh Mây! Không thêm thông tin giá bán."
    project["scenes"] = split_script(project["script"], 60)
    assert len(project["scenes"]) == 3
    assert sum(s["duration"] for s in project["scenes"]) == pytest.approx(60)
    assert " ".join(s["text"] for s in project["scenes"]) == project["script"].replace("\n", " ")
    project["scenes"][0].update(text="Nội dung đã chỉnh", duration=8, start=1)
    store.save(project)
    reopened = ProjectStore(store.root).load(project["id"])
    assert reopened["scenes"][0]["text"] == "Nội dung đã chỉnh"
    assert reopened["scenes"][0]["duration"] == 8
    assert len(store.list_projects()[0]) == 1


def test_invalid_script_and_scene_checks(store):
    with pytest.raises(StudioError, match="nhập kịch bản"):
        split_script(" ")
    with pytest.raises(StudioError, match="thời lượng"):
        split_script("Một câu", float("nan"))
    project = store.create("Test")
    with pytest.raises(StudioError, match="Chưa có cảnh"):
        validate_scenes(project)
    project["scenes"] = [scene("Nội dung")]
    with pytest.raises(StudioError, match="chưa chọn"):
        validate_scenes(project)


def test_confirmation_and_metadata_only(demo):
    item = demo["media"][0]
    item["tags"] = "Đảo Ngọc, cây xanh"
    assert suggest_media("Đảo Ngọc", demo["media"])[0] == item["id"]
    demo["scenes"][0]["confirmed"] = False
    with pytest.raises(StudioError, match="xác nhận"):
        validate_scenes(demo)
    demo["scenes"][0]["confirmed"] = True
    demo["scenes"][0]["start"] = 999
    with pytest.raises(StudioError, match="ngoài video"):
        validate_scenes(demo)


def test_srt_utf8_timing_and_ass_escaping():
    text = "\ufeff1\r\n00:00:00,200 --> 00:00:01,500\r\nĐảo Ngọc – Vịnh Mây\r\n\r\n2\r\n00:00:02,000 --> 00:00:03,000\r\nBạch Vân"
    captions = read_srt(text)
    assert captions[0] == {"start": 0.2, "end": 1.5, "text": "Đảo Ngọc – Vịnh Mây"}
    for bad in ("", "không phải SRT", "1\n00:00:01,000 --> 00:00:00,200\nLỗi",
                "1\n00:99:00,000 --> 00:99:01,000\nLỗi"):
        with pytest.raises(StudioError):
            read_srt(bad)
    assert "{" not in ass_escape(r"{\an8} Giá bán")


def test_missing_tools_api_and_path_escape(monkeypatch, store):
    monkeypatch.setenv("FFMPEG_BINARY", "missing-ffmpeg-for-test")
    with pytest.raises(StudioError, match="Không tìm thấy ffmpeg"):
        binary("ffmpeg")
    with pytest.raises(StudioError, match="chưa được triển khai"):
        UnconfiguredAI().analyze("Kịch bản", 60)
    with pytest.raises(StudioError, match="ngoài thư mục"):
        store.resolve("../../outside.mp4")
    with pytest.raises(StudioError, match="Mã dự án"):
        store.project_dir("../../evil")


def test_corrupt_project_is_reported_without_overwrite(store):
    project = store.create("Project")
    path = store.project_dir(project["id"]) / "project.json"
    path.write_text("invalid", encoding="utf-8")
    assert store.list_projects() == ([], [project["id"]])
    assert path.read_text() == "invalid"
