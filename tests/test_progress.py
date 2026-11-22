import json

from codequest.progress import BACKUP_NAME, Progress


def make(tmp_path):
    main = tmp_path / "appdata" / "progress.json"
    backup = tmp_path / "Documents" / "OneSpace CodeQuest"
    return Progress(main, backup), main, backup


def test_save_writes_main_and_backup(tmp_path):
    progress, main, backup = make(tmp_path)
    progress.completed.add("1-1")
    progress.code["1-1"] = "hero.move_right(6)\n"
    progress.save()
    assert json.loads(main.read_text(encoding="utf-8"))["completed"] == ["1-1"]
    assert json.loads((backup / BACKUP_NAME).read_text(encoding="utf-8"))["code"]["1-1"].startswith("hero")


def test_reinstall_keeps_progress(tmp_path):
    progress, main, backup = make(tmp_path)
    progress.completed.update({"1-1", "1-2"})
    progress.save()
    reopened = Progress(main, backup)
    assert reopened.completed == {"1-1", "1-2"}
    assert not reopened.restored_from_backup


def test_lost_main_file_restores_from_documents_backup(tmp_path):
    progress, main, backup = make(tmp_path)
    progress.completed.add("2-1")
    progress.save()
    main.unlink()
    main.with_name("progress.json.bak").unlink(missing_ok=True)
    reopened = Progress(main, backup)
    assert reopened.completed == {"2-1"}
    assert reopened.restored_from_backup


def test_corrupt_main_file_falls_back_to_previous_save(tmp_path):
    progress, main, _backup = make(tmp_path)
    progress.completed.add("3-1")
    progress.save()
    progress.completed.add("3-2")
    progress.save()
    main.write_text("{ broken", encoding="utf-8")
    reopened = Progress(main, None)
    assert "3-1" in reopened.completed


def test_restore_backup_merges_without_losing_current_work(tmp_path):
    progress, _main, backup = make(tmp_path)
    backup.mkdir(parents=True)
    (backup / BACKUP_NAME).write_text(
        json.dumps({"completed": ["4-1", "4-2"], "code": {"4-1": "old", "5-1": "from usb"}}),
        encoding="utf-8",
    )
    progress.completed.add("1-1")
    progress.code["4-1"] = "current"
    added = progress.restore_backup()
    assert added == 2
    assert progress.completed == {"1-1", "4-1", "4-2"}
    assert progress.code["4-1"] == "current"
    assert progress.code["5-1"] == "from usb"


def test_no_backup_folder_in_development(tmp_path):
    progress = Progress(tmp_path / "progress.json", None)
    assert progress.export_backup() is None
    assert progress.restore_backup() is None


def test_old_bought_skins_are_refunded_once(tmp_path):
    import json

    from codequest.progress import Progress

    save_file = tmp_path / "progress.json"
    old = {"format": 2, "completed": [], "coins": 10, "owned": ["skin2", "skin3"], "skin": "skin3"}
    save_file.write_text(json.dumps(old), encoding="utf-8")
    progress = Progress(save_file, None)
    assert progress.coins == 10 + 120 + 220
    assert progress.skin == "skin3" and not progress.hero_picked
    progress.save()
    assert Progress(save_file, None).coins == 350
