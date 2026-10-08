from typing import Protocol

from services.errors import StudioError


class ScriptAnalyzer(Protocol):
    """Điểm mở rộng cho nhà cung cấp AI ở Giai đoạn 2."""
    def analyze(self, script: str, target_duration: float) -> list[dict]: ...


class UnconfiguredAI:
    def analyze(self, script, target_duration):
        raise StudioError("Phân tích bằng API AI chưa được triển khai trong MVP. Hãy dùng chia cảnh theo quy tắc hoặc thủ công; không cần khóa API.")
