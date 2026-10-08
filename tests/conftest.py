import pytest

from services.storage import ProjectStore
from workflow.demo import create_demo


@pytest.fixture
def store(tmp_path):
    return ProjectStore(tmp_path)


@pytest.fixture
def demo(store):
    return create_demo(store)
