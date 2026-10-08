import streamlit as st

from services.errors import StudioError
from services.storage import ProjectStore
from ui.pages import PAGES, dashboard, render_page

st.set_page_config(page_title="Vinhomes AI Video Studio", page_icon="🎬", layout="wide")
st.markdown("""<style>
.stApp { background: #f6f8fb; }
[data-testid="stSidebar"] { background: #102c3c; }
[data-testid="stSidebar"] * { color: #f8fafc; }
[data-testid="stSidebar"] input { color: #102c3c; }
.block-container { padding-top: 2rem; max-width: 1280px; }
h1, h2, h3 { color: #143848; }
div.stButton > button[kind="primary"] { background: #136f63; border-color: #136f63; }
</style>""", unsafe_allow_html=True)


def main():
    store = ProjectStore()
    st.sidebar.title("🎬 Vinhomes")
    st.sidebar.caption("AI VIDEO STUDIO · MVP 1")
    projects, errors = store.list_projects()
    if errors:
        st.sidebar.warning(f"Có {len(errors)} dự án không đọc được; dữ liệu được giữ nguyên.")
    ids = [p["id"] for p in projects]
    names = {p["id"]: p["name"] for p in projects}
    pending = st.session_state.pop("project_to_open", None)
    if pending in ids:
        st.session_state.active_project = pending
    current = st.session_state.get("active_project")
    if ids:
        if current not in ids:
            st.session_state.active_project = ids[0]
        selected = st.sidebar.selectbox("Dự án đang mở", ids, format_func=lambda value: names[value],
                                        key="active_project")
        project = store.load(selected)
    else:
        project = None
    page = st.sidebar.radio("Quy trình làm video", PAGES, key="navigation")
    st.sidebar.divider()
    st.sidebar.caption("Dữ liệu lưu trên máy. Không cần API trả phí. Tư liệu do bạn cung cấp và xác nhận.")
    st.title("Vinhomes AI Video Studio")
    st.caption("Từ tư liệu thực địa đến một câu chuyện bất động sản rõ ràng, có thể kiểm chứng.")
    if page == PAGES[0]:
        dashboard(store, project, projects)
    elif project:
        render_page(page, store, project)
    else:
        st.info("Hãy tạo dự án tại mục Tổng quan để bắt đầu.")


try:
    main()
except StudioError as exc:
    st.error(str(exc))
except (OSError, ValueError, KeyError) as exc:
    st.error("Không đọc hoặc lưu được dữ liệu. Kiểm tra quyền ghi, dung lượng ổ đĩa và file dự án.")
    st.caption(f"Chi tiết: {type(exc).__name__}")
