import pytest

from app.tasks import TaskValidationError, normalize_task_title


def test_normalize_task_title_trims_surrounding_spaces():
    assert normalize_task_title(" Regar las plantas ") == "Regar las plantas"


@pytest.mark.parametrize("title", ["", "   ", "​"])
def test_normalize_task_title_rejects_titles_without_visible_characters(title):
    with pytest.raises(TaskValidationError):
        normalize_task_title(title)


def test_normalize_task_title_accepts_visible_characters_surrounded_by_invisible_ones():
    assert normalize_task_title("​Hola​") == "​Hola​"
