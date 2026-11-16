"""The move from ~/.smart_espresso to ~/.baristaos."""

import logging

from baristaos.shot_history import ShotHistory
from baristaos.state_home import expand_state_path, state_dir


def test_move_happens_and_logs_once(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("HOME", str(tmp_path))
    old = tmp_path / ".smart_espresso"
    old.mkdir()
    (old / "shot_history.json").write_text('{"shots": []}', encoding="utf-8")
    with caplog.at_level(logging.INFO, logger="baristaos.state_home"):
        found = state_dir()
    assert found == str(tmp_path / ".baristaos")
    assert (tmp_path / ".baristaos" / "shot_history.json").read_text(
        encoding="utf-8"
    ) == '{"shots": []}'
    assert not old.exists()
    infos = [record for record in caplog.records if record.levelno == logging.INFO]
    assert len(infos) == 1
    assert "Moved saved state" in infos[0].getMessage()
    assert str(old) in infos[0].getMessage()
    assert str(tmp_path / ".baristaos") in infos[0].getMessage()


def test_both_folders_use_the_new_one(tmp_path, monkeypatch, caplog):
    monkeypatch.setenv("HOME", str(tmp_path))
    old = tmp_path / ".smart_espresso"
    new = tmp_path / ".baristaos"
    old.mkdir()
    new.mkdir()
    (old / "shot_history.json").write_text("old", encoding="utf-8")
    (new / "shot_history.json").write_text("new", encoding="utf-8")
    with caplog.at_level(logging.INFO, logger="baristaos.state_home"):
        assert state_dir() == str(new)
    assert (old / "shot_history.json").read_text(encoding="utf-8") == "old"
    assert (new / "shot_history.json").read_text(encoding="utf-8") == "new"
    assert not [record for record in caplog.records if record.levelno == logging.INFO]


def test_only_the_new_folder_is_used(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    new = tmp_path / ".baristaos"
    new.mkdir()
    (new / "shot_history.json").write_text("ok", encoding="utf-8")
    assert state_dir() == str(new)
    assert not (tmp_path / ".smart_espresso").exists()


def test_neither_folder_points_at_the_new_path(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    found = state_dir()
    assert found == str(tmp_path / ".baristaos")
    assert not (tmp_path / ".baristaos").exists()
    assert not (tmp_path / ".smart_espresso").exists()


def test_failed_move_falls_back_to_the_old_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    old = tmp_path / ".smart_espresso"
    old.mkdir()
    (old / "shot_history.json").write_text("kept", encoding="utf-8")

    def boom(*_args, **_kwargs):
        raise PermissionError("cross-device")

    monkeypatch.setattr("baristaos.state_home.shutil.move", boom)
    assert state_dir() == str(old)
    resolved = expand_state_path("~/.baristaos/shot_history.json")
    assert resolved == str(old / "shot_history.json")
    assert open(resolved, encoding="utf-8").read() == "kept"
    assert old.is_dir()
    assert not (tmp_path / ".baristaos").exists()


def test_shot_history_opens_the_moved_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    old = tmp_path / ".smart_espresso"
    old.mkdir()
    (old / "marker").write_text("1", encoding="utf-8")
    history = ShotHistory(state_path="~/.baristaos/shot_history.json")
    assert history.state_path == str(tmp_path / ".baristaos" / "shot_history.json")
    assert (tmp_path / ".baristaos" / "marker").is_file()
    assert not old.exists()
