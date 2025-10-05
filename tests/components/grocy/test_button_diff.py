from custom_components.grocy.button import _compute_chore_diff


def make_chore(id: int, name: str = None):
    return {"chore_id": id, "chore_name": name or f"Chore {id}"}


def test_compute_chore_diff_add_and_remove():
    existing = {1, 2, 3}
    chores = [make_chore(2), make_chore(3), make_chore(4), make_chore(5)]

    to_add, to_remove = _compute_chore_diff(existing, chores)

    assert to_add == {4, 5}
    assert to_remove == {1}


def test_compute_chore_diff_no_change():
    existing = {1, 2}
    chores = [make_chore(1), make_chore(2)]

    to_add, to_remove = _compute_chore_diff(existing, chores)

    assert to_add == set()
    assert to_remove == set()


def test_compute_chore_diff_empty_existing():
    existing = set()
    chores = [make_chore(10), make_chore(20)]

    to_add, to_remove = _compute_chore_diff(existing, chores)

    assert to_add == {10, 20}
    assert to_remove == set()
