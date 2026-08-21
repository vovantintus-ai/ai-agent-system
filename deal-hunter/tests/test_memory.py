import os

from dealhunter.memory import SeenStore


def test_new_then_seen(tmp_path):
    path = os.path.join(tmp_path, "seen.json")
    store = SeenStore(path)
    assert store.is_new("a")
    store.mark("a")
    assert not store.is_new("a")


def test_persistence_round_trip(tmp_path):
    path = os.path.join(tmp_path, "seen.json")
    s1 = SeenStore(path)
    s1.mark("x")
    s1.save()
    s2 = SeenStore(path)
    assert not s2.is_new("x")


def test_filter_new(tmp_path):
    store = SeenStore(os.path.join(tmp_path, "seen.json"))
    store.mark("a")
    assert store.filter_new(["a", "b", "c"]) == ["b", "c"]


def test_prune_bounds_size(tmp_path):
    store = SeenStore(os.path.join(tmp_path, "seen.json"))
    for i in range(20):
        store.mark(f"id{i:02d}", when=f"2026-01-01T00:00:{i:02d}+00:00")
    store.prune(keep=5)
    assert len(store) == 5
    # keeps the most-recent timestamps
    assert not store.is_new("id19")
    assert store.is_new("id00")


def test_corrupt_file_does_not_crash(tmp_path):
    path = os.path.join(tmp_path, "seen.json")
    with open(path, "w") as fh:
        fh.write("{not valid json")
    store = SeenStore(path)  # should recover, not raise
    assert store.is_new("anything")
    assert os.path.exists(path + ".corrupt")
