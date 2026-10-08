import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from services.errors import StudioError

ROOT = Path(__file__).resolve().parents[1]


def now():
    return datetime.now(timezone.utc).isoformat()


def defaults():
    return json.loads((ROOT / "config/defaults.json").read_text(encoding="utf-8"))


class ProjectStore:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()
        for folder in ("projects", "inputs/media", "inputs/scripts", "outputs"):
            (self.root / folder).mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_id):
        if not re.fullmatch(r"[a-f0-9]{32}", project_id):
            raise StudioError("Mã dự án không hợp lệ.")
        return self.root / "projects" / project_id

    def resolve(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise StudioError("Đường dẫn nằm ngoài thư mục ứng dụng.")
        return path

    def create(self, name):
        name = name.strip()
        if not name:
            raise StudioError("Hãy nhập tên dự án.")
        project = {
            "schema_version": 1, "id": uuid.uuid4().hex, "name": name[:120],
            "created_at": now(), "updated_at": now(), "script": "", "media": [],
            "scenes": [], "settings": defaults(), "audio": {}, "exports": [],
            "render": {"status": "idle", "progress": 0},
        }
        self.save(project)
        return project

    def save(self, project):
        directory = self.project_dir(project["id"])
        directory.mkdir(parents=True, exist_ok=True)
        project["updated_at"] = now()
        temporary = directory / "project.json.tmp"
        temporary.write_text(json.dumps(project, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        temporary.replace(directory / "project.json")

    def load(self, project_id):
        try:
            project = json.loads((self.project_dir(project_id) / "project.json").read_text(encoding="utf-8"))
            if project["id"] != project_id or project.get("schema_version") != 1:
                raise ValueError("schema")
            return project
        except (OSError, ValueError, KeyError) as exc:
            raise StudioError("Không đọc được dự án. Hãy kiểm tra file project.json hoặc bản sao lưu.") from exc

    def list_projects(self):
        items, errors = [], []
        for path in (self.root / "projects").glob("*/project.json"):
            try:
                items.append(self.load(path.parent.name))
            except StudioError:
                errors.append(path.parent.name)
        return sorted(items, key=lambda p: p["updated_at"], reverse=True), errors
