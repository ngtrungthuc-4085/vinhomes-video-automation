from pathlib import Path

from streamlit.testing.v1 import AppTest

import services.storage as storage
from ui.pages import PAGES


def test_streamlit_create_resume_edit_and_all_pages(monkeypatch, store):
    monkeypatch.setattr(storage, "ProjectStore", lambda: store)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=20).run()
    assert not app.exception
    app.text_input[0].set_value("Dự án giao diện")
    app.button[0].click().run()
    assert not app.exception
    assert len(store.list_projects()[0]) == 1
    project_id = store.list_projects()[0][0]["id"]
    for page in PAGES[1:]:
        app.sidebar.radio[0].set_value(page).run()
        assert not app.exception, page
    app.sidebar.radio[0].set_value(PAGES[2]).run()
    app.text_area[0].set_value("Khám phá Đảo Ngọc. Ghé thăm Vịnh Mây.")
    app.button[-1].click().run()
    assert store.load(project_id)["script"].startswith("Khám phá")
    app.sidebar.radio[0].set_value(PAGES[3]).run()
    app.button[0].click().run()
    assert len(store.load(project_id)["scenes"]) == 2
    assert not app.exception
    app.sidebar.radio[0].set_value(PAGES[0]).run()
    app.text_input[0].set_value("Dự án thứ hai")
    app.button[0].click().run()
    assert not app.exception
    assert len(store.list_projects()[0]) == 2
    assert store.load(app.session_state["active_project"])["name"] == "Dự án thứ hai"


def test_ui_edit_reconfirm_and_export(monkeypatch, store, demo):
    monkeypatch.setattr(storage, "ProjectStore", lambda: store)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30).run()
    app.sidebar.radio[0].set_value(PAGES[3]).run()
    # Đổi tư liệu của cảnh đầu tiên và chỉnh thời lượng bằng form thật.
    picker = next(s for s in app.selectbox if s.label == "Tư liệu")
    picker.set_value(demo["media"][2]["id"])
    duration = next(n for n in app.number_input if n.label == "Thời lượng (giây)")
    duration.set_value(2.5)
    next(b for b in app.button if b.label == "Lưu cảnh").click().run()
    saved = store.load(demo["id"])
    assert saved["scenes"][0]["media_id"] == demo["media"][2]["id"]
    assert saved["scenes"][0]["duration"] == 2.5
    assert not saved["scenes"][0]["confirmed"]
    next(c for c in app.checkbox if c.label.startswith("Tôi xác nhận tư liệu")).check()
    next(b for b in app.button if b.label == "Lưu cảnh").click().run()
    assert store.load(demo["id"])["scenes"][0]["confirmed"]
    app.sidebar.radio[0].set_value(PAGES[5]).run()
    next(b for b in app.button if b.label == "Dựng và xuất video").click().run()
    assert not app.exception
    assert not app.error
    saved = store.load(demo["id"])
    assert saved["render"]["status"] == "done"
    assert store.resolve(saved["exports"][-1]["path"]).is_file()
