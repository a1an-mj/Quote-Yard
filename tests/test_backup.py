import os
import shutil
import subprocess
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "deploy" / "backup.sh"
pytestmark = pytest.mark.skipif(shutil.which("pg_dump") is None, reason="pg_dump not installed")


def run(tmp_path, db):
    data = tmp_path / "data"
    data.mkdir(exist_ok=True)
    (data / "a.json").write_text("[]")
    env = {**os.environ, "QUOTE_YARD_BACKUP_DIR": str(tmp_path / "b"),
           "QUOTE_YARD_BACKUP_DB": db, "QUOTE_YARD_BACKUP_DATA": str(data)}
    return subprocess.run([str(SCRIPT)], env=env, capture_output=True, text=True)


@pytest.fixture
def db():
    url = os.environ["QUOTE_YARD_DATABASE_URL"]
    try:
        create_engine(url).connect().close()
    except Exception:
        pytest.skip("PostgreSQL not reachable")
    return make_url(url).database


def test_backup_makes_private_restorable_files(tmp_path, db):
    result = run(tmp_path, db)
    assert result.returncode == 0, result.stderr
    folder = tmp_path / "b"
    assert (folder.stat().st_mode & 0o777) == 0o700
    dump = next(folder.glob("quote_yard-*.dump"))
    assert (dump.stat().st_mode & 0o777) == 0o600
    assert next(folder.glob("data-*.tar")).exists()
    toc = subprocess.run(["pg_restore", "--list", str(dump)], capture_output=True, text=True).stdout
    assert "TABLE DATA public price_history" in toc


def test_retention_keeps_14_daily_and_6_monthly(tmp_path, db):
    folder = tmp_path / "b"
    folder.mkdir()
    (folder / "notes.txt").write_text("not a backup")
    days = [f"2020-{m:02}-01" for m in range(1, 13)] + [f"2021-01-{d:02}" for d in range(2, 22)]
    for day in days:
        (folder / f"quote_yard-{day}.dump").write_text("x")
        (folder / f"data-{day}.tar").write_text("x")
    assert run(tmp_path, db).returncode == 0
    kept = {p.name[11:21] for p in folder.glob("quote_yard-*.dump")}
    assert {"2021-01-21", "2021-01-09"} <= kept          # recent dailies
    assert "2021-01-08" not in kept                      # 14th-oldest cut, today's backup counts
    # Today's backup counts as a monthly one when run on the 1st.
    firsts = sorted({d for d in days if d.endswith("-01")} | {date.today().isoformat()}, reverse=True)
    firsts = [d for d in firsts if d.endswith("-01")]
    assert set(firsts[:6]) <= kept and not set(firsts[6:]) & kept
    assert (folder / "notes.txt").exists()
    assert {p.name[5:15] for p in folder.glob("data-*.tar")} == kept


def test_failed_dump_keeps_existing_backups(tmp_path):
    folder = tmp_path / "b"
    folder.mkdir()
    old = folder / "quote_yard-2021-01-01.dump"
    old.write_text("x")
    assert run(tmp_path, "no_such_database_test").returncode != 0
    assert old.exists() and not list(folder.glob(".tmp*"))
