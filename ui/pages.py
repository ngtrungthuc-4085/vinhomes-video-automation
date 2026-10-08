import json

import streamlit as st

from services.ai_adapter import UnconfiguredAI
from services.errors import StudioError
from services.media import import_media
from services.subtitles import font_path, read_srt
from services.tools import check_tools
from workflow.render import export_project
from workflow.scenes import scene, split_script, suggest_media

PAGES = ["01 · Tổng quan", "02 · Thư viện tư liệu", "03 · Kịch bản", "04 · Biên tập cảnh",
         "05 · Âm thanh & Phụ đề", "06 · Xem trước & Xuất", "07 · Cài đặt"]


def save(store, project, message="Đã lưu."):
    store.save(project)
    st.success(message)


def dashboard(store, project, projects):
    st.subheader("Không gian dự án")
    with st.form("new_project", clear_on_submit=True):
        name = st.text_input("Tên dự án mới", placeholder="Ví dụ: Đảo Ngọc · Hành trình khám phá", max_chars=120)
        if st.form_submit_button("＋ Tạo dự án", type="primary"):
            created = store.create(name)
            st.session_state.project_to_open = created["id"]
            st.rerun()
    if not project:
        st.info("Tạo dự án, tải tư liệu rồi nhập kịch bản. Mọi thay đổi đã lưu có thể mở lại sau khi đóng ứng dụng.")
        return
    cols = st.columns(4)
    cols[0].metric("Dự án", len(projects))
    cols[1].metric("Tư liệu", len(project["media"]))
    cols[2].metric("Cảnh", len(project["scenes"]))
    cols[3].metric("Thời lượng", f"{sum(s['duration'] for s in project['scenes']):.1f} giây")
    st.subheader(project["name"])
    st.write("**1.** Tải video/ảnh → **2.** Nhập kịch bản → **3.** Chia cảnh, chọn và xác nhận tư liệu → **4.** Chọn âm thanh/chữ → **5.** Xuất bản xem thử, sau đó bản Full HD.")
    st.info("Không tự suy diễn giá bán, pháp lý, tiến độ hoặc chính sách. Hãy kiểm tra nội dung và quyền sử dụng tư liệu trước khi đăng.")
    render = project.get("render", {})
    if render.get("status") == "running":
        st.warning("Lần dựng trước chưa hoàn tất. Bạn có thể xuất lại; các cảnh đã dựng được giữ trong bộ nhớ đệm.")
    elif render.get("message"):
        st.caption(f"Lần xử lý gần nhất: {render['message']}")
    st.download_button("Sao lưu cấu hình dự án JSON", json.dumps(project, ensure_ascii=False, indent=2),
                       file_name=f"project_{project['id']}.json", mime="application/json")
    st.caption("File JSON chỉ chứa cấu hình, không chứa tư liệu. Sao lưu đầy đủ bằng cách chép cả projects, inputs và outputs.")


def media_library(store, project):
    st.subheader("Thư viện tư liệu thực địa")
    st.caption("MP4, MOV, JPG, PNG · tối đa 200 MB/file. File được sao chép vào thư viện; không sửa video gốc.")
    files = st.file_uploader("Chọn nhiều video hoặc ảnh", type=["mp4", "mov", "jpg", "jpeg", "png"],
                             accept_multiple_files=True, key=f"media_upload_{project['id']}")
    if st.button("Nhập tư liệu", type="primary", disabled=not files):
        count = 0
        with st.spinner("Đọc metadata và tạo ảnh xem trước…"):
            for uploaded in files:
                try:
                    item = import_media(store, project, uploaded.name, uploaded.getvalue())
                    if item["id"] not in {m["id"] for m in project["media"]}:
                        project["media"].append(item)
                        store.save(project)
                        count += 1
                except (StudioError, OSError, ValueError) as exc:
                    st.error(f"Không nhập được {uploaded.name}: {exc}")
        st.success(f"Đã nhập {count} tư liệu mới. Các file trùng nội dung được bỏ qua.")
    for item in project["media"]:
        with st.expander(f"{item['name']} · {item['width']} × {item['height']} · {item['duration']:.1f}s"):
            left, right = st.columns([1, 2])
            thumb = store.resolve(item["thumbnail"])
            if thumb.exists():
                left.image(str(thumb))
            if item["kind"] == "video" and left.checkbox("Xem video", key=f"watch_{item['id']}_{project['id']}"):
                path = store.resolve(item["path"])
                if path.exists():
                    left.video(str(path))
            with right.form(f"metadata_{project['id']}_{item['id']}"):
                name = st.text_input("Tên tư liệu", item["name"])
                description = st.text_area("Mô tả", item["description"])
                location = st.text_input("Địa điểm do bạn xác nhận", item["location"])
                tags = st.text_input("Thẻ nội dung (cách nhau bằng dấu phẩy)", item["tags"])
                if st.form_submit_button("Lưu thông tin tư liệu"):
                    item.update(name=name, description=description, location=location, tags=tags)
                    save(store, project)
    if not project["media"]:
        st.info("Chưa có tư liệu. Bạn có thể dùng bộ mẫu tổng hợp theo hướng dẫn README; mẫu không phải hình ảnh dự án thật.")


def script_editor(store, project):
    st.subheader("Kịch bản tiếng Việt")
    uploaded = st.file_uploader("Nhập từ file TXT UTF-8 (tùy chọn)", type=["txt"], key=f"script_file_{project['id']}")
    if st.button("Đọc file vào bản nháp", disabled=uploaded is None):
        try:
            st.session_state[f"script_{project['id']}"] = uploaded.getvalue().decode("utf-8-sig")
        except UnicodeDecodeError:
            raise StudioError("Hãy lưu file kịch bản dưới định dạng UTF-8.")
    with st.form(f"script_form_{project['id']}"):
        script = st.text_area("Nội dung kịch bản", project["script"], height=300, key=f"script_{project['id']}")
        if st.form_submit_button("Lưu kịch bản", type="primary"):
            project["script"] = script
            save(store, project, "Đã lưu kịch bản. Cảnh hiện có được giữ lại; chia lại ở Biên tập cảnh nếu cần.")
    st.caption("Chỉ sử dụng thông tin bạn đã kiểm chứng. Chia cảnh theo quy tắc giữ nguyên nội dung, không bổ sung thông tin dự án.")


def scene_editor(store, project):
    st.subheader("Biên tập cảnh")
    st.caption("Gợi ý dựa trên tên, mô tả và thẻ bạn nhập; không nhận diện địa điểm trong hình ảnh.")
    with st.form(f"split_{project['id']}"):
        target = st.number_input("Tổng thời lượng mong muốn (giây)", 1.0, 3600.0,
                                 float(project["settings"]["target_duration"]), step=5.0)
        confirm_replace = st.checkbox("Tôi đồng ý thay danh sách cảnh hiện có", value=not project["scenes"])
        if st.form_submit_button("Chia kịch bản theo quy tắc", type="primary"):
            if project["scenes"] and not confirm_replace:
                st.warning("Hãy xác nhận thay danh sách cảnh trước khi chia lại.")
            else:
                project["scenes"] = split_script(project["script"], target)
                project["settings"]["target_duration"] = target
                store.save(project)
                st.rerun()
    a, b = st.columns(2)
    if a.button("＋ Thêm cảnh thủ công"):
        project["scenes"].append(scene(duration=project["settings"]["scene_duration"]))
        store.save(project)
        st.rerun()
    if b.button("Phân tích bằng API AI (giai đoạn 2)"):
        UnconfiguredAI().analyze(project["script"], target)
    media = {m["id"]: m for m in project["media"]}
    for index, item in enumerate(project["scenes"]):
        with st.expander(f"Cảnh {index + 1} · {item['duration']:.1f}s · {'✓ đã xác nhận' if item['confirmed'] else 'chưa xác nhận'}", expanded=True):
            ranked = suggest_media(item["text"], project["media"])
            if ranked:
                st.caption("Gợi ý theo metadata: " + ", ".join(media[mid]["name"] for mid in ranked[:3]))
            options = [None] + list(media)
            selected_index = options.index(item["media_id"]) if item["media_id"] in options else 0
            with st.form(f"scene_{project['id']}_{item['id']}"):
                text = st.text_area("Nội dung cảnh", item["text"])
                selected = st.selectbox("Tư liệu", options, index=selected_index,
                                        format_func=lambda mid: "— Chọn tư liệu —" if mid is None else media[mid]["name"])
                cols = st.columns(2)
                duration = cols[0].number_input("Thời lượng (giây)", 0.2, 600.0, max(0.2, min(600.0, float(item["duration"]))), step=0.1)
                start = cols[1].number_input("Cắt từ giây (video)", 0.0, 86400.0, float(item["start"]), step=0.1)
                confirmed = st.checkbox("Tôi xác nhận tư liệu phù hợp với nội dung cảnh", item["confirmed"])
                st.caption("Khi đổi tư liệu, hãy lưu lựa chọn mới rồi xác nhận lại cảnh.")
                if st.form_submit_button("Lưu cảnh"):
                    if selected != item["media_id"]:
                        confirmed = False
                    item.update(text=text, media_id=selected, duration=duration, start=start, confirmed=confirmed)
                    store.save(project)
                    st.rerun()
            if item["media_id"] in media:
                source = media[item["media_id"]]
                if source["kind"] == "video" and item["start"] + item["duration"] > source["duration"]:
                    st.info("Cảnh dài hơn phần video còn lại: khung hình cuối sẽ được giữ, tiếng gốc được bù im lặng.")
            cols = st.columns(3)
            if cols[0].button("↑ Lên", key=f"up_{item['id']}", disabled=index == 0):
                project["scenes"][index - 1], project["scenes"][index] = item, project["scenes"][index - 1]
                store.save(project)
                st.rerun()
            if cols[1].button("↓ Xuống", key=f"down_{item['id']}", disabled=index == len(project["scenes"]) - 1):
                project["scenes"][index + 1], project["scenes"][index] = item, project["scenes"][index + 1]
                store.save(project)
                st.rerun()
            if cols[2].button("Bỏ cảnh", key=f"remove_{item['id']}"):
                project["scenes"].pop(index)
                store.save(project)
                st.rerun()
    st.caption(f"Tổng thời lượng: {sum(s['duration'] for s in project['scenes']):.2f} giây. Các thay đổi cần bấm Lưu cảnh.")


def audio_subtitle(store, project):
    st.subheader("Âm thanh & Phụ đề")
    st.info("MVP dùng giọng đọc bạn ghi sẵn và SRT bạn cung cấp. Chưa tự nhận dạng giọng nói hoặc tạo giọng đọc AI.")
    for key, label in (("narration", "Giọng đọc"), ("music", "Nhạc nền")):
        uploaded = st.file_uploader(f"Tải {label.lower()}", type=["wav", "mp3", "m4a", "aac", "ogg"], key=f"{key}_{project['id']}")
        if st.button(f"Lưu {label.lower()}", key=f"save_{key}", disabled=uploaded is None):
            item = import_media(store, project, uploaded.name, uploaded.getvalue(), audio=True)
            project["audio"][key] = item
            if key == "music":
                project["audio"]["music_rights_confirmed"] = False
            save(store, project)
        current = project["audio"].get(key)
        if current:
            st.caption(f"{label}: {current['name']} · {current['duration']:.1f}s")
            path = store.resolve(current["path"])
            if path.exists():
                st.audio(str(path))
            if st.button(f"Bỏ {label.lower()}", key=f"clear_{key}"):
                project["audio"].pop(key, None)
                store.save(project)
                st.rerun()
    uploaded_srt = st.file_uploader("Nhập phụ đề SRT UTF-8", type=["srt"], key=f"srt_{project['id']}")
    if st.button("Đọc SRT vào bản nháp", disabled=uploaded_srt is None):
        try:
            content = uploaded_srt.getvalue().decode("utf-8-sig")
        except UnicodeDecodeError:
            raise StudioError("File SRT cần mã hóa UTF-8 để hiển thị tiếng Việt.")
        read_srt(content)
        st.session_state[f"subtitles_{project['id']}"] = content
    with st.form(f"audio_options_{project['id']}"):
        keep = st.checkbox("Giữ âm thanh gốc (khi không có giọng đọc)", project["settings"]["keep_original_audio"])
        volume = st.slider("Âm lượng nhạc nền", 0.0, 1.0, float(project["settings"]["music_volume"]), step=0.05)
        rights = st.checkbox("Tôi có quyền sử dụng nhạc nền đã chọn", project["audio"].get("music_rights_confirmed", False))
        captions = st.checkbox("Hiển thị chữ kịch bản theo cảnh khi không có SRT", project["settings"]["script_captions"])
        st.caption("Chữ theo cảnh không tự đồng bộ với lời nói. SRT được ưu tiên nếu có; hãy kiểm tra thời gian bằng bản xem thử.")
        srt = st.text_area("Nội dung SRT (để trống nếu không dùng)", project["audio"].get("subtitles", ""), height=180,
                           key=f"subtitles_{project['id']}")
        if st.form_submit_button("Lưu âm thanh và phụ đề", type="primary"):
            if srt.strip():
                read_srt(srt)
            project["settings"].update(keep_original_audio=keep, music_volume=volume, script_captions=captions)
            project["audio"].update(subtitles=srt.strip(), music_rights_confirmed=rights)
            save(store, project)
    st.caption("Giọng đọc thay tiếng gốc, không tự kéo giãn: file ngắn được bù im lặng, file dài bị cắt theo thời lượng video. Nhạc nền được lặp đến hết video.")


def preview_export(store, project):
    st.subheader("Xem trước & Xuất MP4")
    total = sum(s["duration"] for s in project["scenes"])
    st.write(f"**{project['settings']['aspect']}** · {len(project['scenes'])} cảnh · {total:.2f} giây · H.264 / AAC")
    quality = st.radio("Chất lượng", ["preview", "full"], horizontal=True,
                       format_func=lambda value: "Xem thử · 360p" if value == "preview" else "Xuất chính thức · Full HD")
    st.caption("Giữ tỷ lệ tư liệu bằng viền đen, không kéo giãn hoặc tự cắt khuôn mặt. Chuyển cảnh là fade nhẹ qua nền đen.")
    if st.button("Dựng và xuất video", type="primary"):
        bar = st.progress(0, text="Chuẩn bị…")
        with st.spinner("Đang xử lý trên CPU. Vui lòng giữ cửa sổ này mở…"):
            export_project(store, project, quality, lambda value, message: bar.progress(value, text=message))
        st.success(project["render"]["message"])
    exports = project["exports"]
    if exports:
        labels = list(range(len(exports) - 1, -1, -1))
        selected = st.selectbox("Phiên bản đã xuất", labels,
                                format_func=lambda i: f"{exports[i]['created_at']} · {exports[i]['quality']} · {exports[i]['width']}×{exports[i]['height']}")
        item = exports[selected]
        path = store.resolve(item["path"])
        if path.exists():
            st.video(str(path))
            st.download_button("Tải MP4 về máy", path.read_bytes(), file_name=path.name, mime="video/mp4")
            st.caption(f"File lưu: {item['path']}")
        else:
            st.warning("File xuất không còn trên ổ đĩa. Hãy dựng lại.")
    else:
        st.info("Chưa có bản xuất. Hãy chọn và xác nhận tư liệu cho từng cảnh trước.")


def settings(store, project):
    st.subheader("Cài đặt dự án")
    options = project["settings"]
    with st.form(f"settings_{project['id']}"):
        title = st.text_input("Tiêu đề mở đầu (tối đa 160 ký tự)", options.get("title", ""), max_chars=160)
        cta = st.text_area("Lời kêu gọi hành động (CTA)", options["cta"], max_chars=240)
        aspect = st.selectbox("Tỷ lệ xuất", ["9:16", "16:9"], index=0 if options["aspect"] == "9:16" else 1)
        fade = st.checkbox("Chuyển cảnh nhẹ qua nền đen", options["fade"])
        duration = st.number_input("Thời lượng mặc định của cảnh thủ công", 0.2, 600.0, float(options["scene_duration"]), step=0.5)
        if st.form_submit_button("Lưu cài đặt", type="primary"):
            options.update(title=title, cta=cta, aspect=aspect, fade=fade, scene_duration=duration)
            save(store, project)
    st.caption("Ngôn ngữ: tiếng Việt · Ưu tiên nội dung: " + " → ".join(options["content_priority"]))
    st.write("**API:** MVP không gọi nhà cung cấp AI và không cần khóa API. Adapter mở rộng nằm trong services/ai_adapter.py.")
    if st.button("Kiểm tra FFmpeg và font"):
        check_tools()
        font_path()
        st.success("FFmpeg, ffprobe, H.264, AAC, bộ lọc phụ đề và font đã có.")


def render_page(page, store, project):
    functions = dict(zip(PAGES[1:], [media_library, script_editor, scene_editor, audio_subtitle, preview_export, settings]))
    functions[page](store, project)
