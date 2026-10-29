import fcntl
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import prune_runs, run_pipeline

PY = sys.executable


def write(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records), encoding="utf-8")


def writes(filename, records):
    """A fake scraper that writes `records` to data/<filename>."""
    code = (f"import json,pathlib; pathlib.Path('data').mkdir(exist_ok=True); "
            f"pathlib.Path('data/{filename}').write_text(json.dumps({records!r}))")
    return [PY, "-c", code]


OK = [PY, "-c", "pass"]
FAIL = [PY, "-c", "raise SystemExit(3)"]


def stage_marker(name):
    return [PY, "-c", f"import pathlib; pathlib.Path('ran-{name}').touch()"]


def run(tmp_path, scrapers, stages=None, **kw):
    lines = []
    stages = stages if stages is not None else [(n, stage_marker(n)) for n in ("clean", "load")]
    code = run_pipeline(root=tmp_path, scrapers=scrapers, stages=stages,
                        out=lines.append, **kw)
    return code, "\n".join(str(l) for l in lines)


def test_all_good(tmp_path):
    write(tmp_path / "data/a_x.json", [{"n": 1}])
    code, text = run(tmp_path, {"a": (writes("a_x.json", [{"n": 1}, {"n": 2}]), "a_")})
    assert code == 0 and "Result: OK" in text
    assert json.loads((tmp_path / "data/a_x.json").read_text()) == [{"n": 1}, {"n": 2}]
    assert (tmp_path / "ran-clean").exists() and (tmp_path / "ran-load").exists()


def test_one_retailer_failing_does_not_stop_others(tmp_path):
    code, text = run(tmp_path, {
        "a": (FAIL, "a_"),
        "b": (writes("b_x.json", [{"n": 1}]), "b_"),
    })
    assert code == 1
    assert (tmp_path / "data/b_x.json").exists()
    assert (tmp_path / "ran-load").exists()  # processing still ran
    assert "scrape a" in text and "FAILED" in text and "exit code 3" in text


def test_empty_scrape_restores_previous_file(tmp_path):
    write(tmp_path / "data/a_x.json", [{"n": 1}, {"n": 2}])
    code, text = run(tmp_path, {"a": (writes("a_x.json", []), "a_")})
    assert code == 1
    assert json.loads((tmp_path / "data/a_x.json").read_text()) == [{"n": 1}, {"n": 2}]
    assert "came back empty, restored previous 2 records" in text


def test_unreadable_scrape_restored(tmp_path):
    write(tmp_path / "data/a_x.json", [{"n": 1}])
    broken = [PY, "-c", "open('data/a_x.json','w').write('{not json')"]
    code, text = run(tmp_path, {"a": (broken, "a_")})
    assert code == 1 and "unreadable" in text
    assert json.loads((tmp_path / "data/a_x.json").read_text()) == [{"n": 1}]


def test_big_shrink_kept_but_flagged(tmp_path):
    write(tmp_path / "data/a_x.json", [{"n": i} for i in range(10)])
    code, text = run(tmp_path, {"a": (writes("a_x.json", [{"n": 1}]), "a_")})
    assert code == 0
    assert len(json.loads((tmp_path / "data/a_x.json").read_text())) == 1
    assert "10 -> 1 records (kept, check it)" in text


def test_other_retailers_files_untouched(tmp_path):
    write(tmp_path / "data/b_x.json", [{"n": 1}])
    run(tmp_path, {"a": (writes("a_x.json", []), "a_")})
    assert json.loads((tmp_path / "data/b_x.json").read_text()) == [{"n": 1}]


def test_stage_failure_stops_the_run(tmp_path):
    stages = [("clean", stage_marker("clean")), ("normalize", FAIL), ("load", stage_marker("load"))]
    code, text = run(tmp_path, {}, stages=stages)
    assert code == 2
    assert (tmp_path / "ran-clean").exists() and not (tmp_path / "ran-load").exists()
    assert "not run: load" in text


def test_timeout_counts_as_failure(tmp_path):
    slow = [PY, "-c", "import time; time.sleep(5)"]
    code, text = run(tmp_path, {"a": (slow, "a_")}, scrape_timeout=1)
    assert code == 1 and "timed out" in text


def test_only_and_skip_scrape(tmp_path):
    scrapers = {"a": (writes("a_x.json", [{"n": 1}]), "a_"),
                "b": (writes("b_x.json", [{"n": 1}]), "b_")}
    run(tmp_path, scrapers, only=["b"])
    assert not (tmp_path / "data/a_x.json").exists() and (tmp_path / "data/b_x.json").exists()
    code, text = run(tmp_path, {"a": (FAIL, "a_")}, skip_scrape=True)
    assert code == 0 and "scrape a" not in text


def test_dry_run_flag_only_for_load_and_match(tmp_path):
    echo = [PY, "-c", "import sys,pathlib; pathlib.Path('args-'+sys.argv[1]).write_text(' '.join(sys.argv[2:]))"]
    stages = [(n, echo + [n]) for n in ("clean", "load", "match")]
    run(tmp_path, {}, stages=stages, dry_run=True)
    assert (tmp_path / "args-clean").read_text() == ""
    assert (tmp_path / "args-load").read_text() == "--dry-run"
    assert (tmp_path / "args-match").read_text() == "--dry-run"


def test_second_run_refused_while_locked(tmp_path):
    (tmp_path / "logs").mkdir()
    with (tmp_path / "logs/pipeline.lock").open("w") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        code, text = run(tmp_path, {})
    assert code == 2 and "Another pipeline run" in text


def test_logs_and_backup_written(tmp_path):
    write(tmp_path / "data/a_x.json", [{"n": 1}])
    run(tmp_path, {"a": (writes("a_x.json", [{"n": 2}]), "a_")})
    (run_dir,) = [p for p in (tmp_path / "logs").iterdir() if p.is_dir()]
    assert (run_dir / "scrape-a.log").exists() and (run_dir / "clean.log").exists()
    assert json.loads((run_dir / "data_before/a_x.json").read_text()) == [{"n": 1}]


def test_prune_keeps_newest(tmp_path):
    for name in ("20260101-000000", "20260102-000000", "20260103-000000"):
        (tmp_path / name).mkdir()
    (tmp_path / "pipeline.lock").touch()
    prune_runs(tmp_path, keep=2)
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "20260102-000000", "20260103-000000", "pipeline.lock"]
