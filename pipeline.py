"""
Quote Yard - full update in one command.

    scrape (each retailer) -> clean -> normalize -> brand -> load -> match -> alerts

Usage (from the repo root):
    python -m pipeline                         # everything
    python -m pipeline --only myg oxygen       # scrape only these retailers
    python -m pipeline --skip-scrape           # reprocess the data/ already on disk
    python -m pipeline --skip-scrape --dry-run # nothing saved or emailed

Rules:
- Each scraper runs in its own process with a timeout, so one retailer
  crashing or hanging never stops the others.
- data/ is backed up before scraping. A file that comes back empty or
  unreadable while the old one had records is restored from the backup
  (a blocked scrape must not wipe a good snapshot). A file that shrinks by
  more than half is kept but flagged.
- Processing stages depend on each other: the first failure stops the run.
- One run at a time (lock file). Logs go to logs/<timestamp>/.
- Exit code: 0 all good, 1 a retailer failed or was restored, 2 a
  processing stage failed or another run holds the lock.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

# key -> (scraper command, prefix of the data/ files it writes)
SCRAPERS = {
    "myg": ([PY, "scrapers/myg_scraper.py", "--headless"], "myg_"),
    "oxygen": ([PY, "scrapers/oxygen_scraper.py", "--headless"], "oxygen_"),
    "pittappillil": ([PY, "scrapers/pittappillil_scraper.py", "--headless"], "pittappillil_"),
    "nandilath": ([PY, "scrapers/nandilath_scraper.py", "--headless"], "nandilath_"),
}

STAGES = [
    ("clean", [PY, "data_processing/run_cleaning.py"]),
    ("normalize", [PY, "data_processing/run_normalization.py"]),
    ("brand", [PY, "data_processing/run_branding.py"]),
    ("load", [PY, "-m", "db.loader"]),
    ("match", [PY, "-m", "db.match_writer"]),
    # Last on purpose: the day's prices are already saved if email fails.
    ("alerts", [PY, "-m", "api.send_alerts"]),
]
DRY_RUN_STAGES = {"load", "match", "alerts"}  # these accept --dry-run

KEEP_RUNS = 14  # log folders (each holds a data/ backup) kept after a run
SHRINK_WARNING = 0.5
SCRAPE_TIMEOUT_S = 60 * 60
STAGE_TIMEOUT_S = 15 * 60


@dataclass
class StepResult:
    name: str
    ok: bool
    seconds: float
    detail: str = ""
    notes: list[str] = field(default_factory=list)


def run_logged(cmd: list[str], log_path: Path, timeout: int, cwd: Path) -> tuple[bool, str]:
    """Run a command with output to log_path. Returns (ok, detail)."""
    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"$ {' '.join(cmd)}\n\n")
        log.flush()
        try:
            proc = subprocess.run(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                  timeout=timeout)
        except subprocess.TimeoutExpired:
            return False, f"timed out after {timeout}s"
        except OSError as exc:
            return False, f"could not start: {exc}"
    return proc.returncode == 0, "" if proc.returncode == 0 else f"exit code {proc.returncode}"


def count_records(path: Path) -> int | None:
    """Number of records in a scraper file, or None if it is not a JSON list."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return len(data) if isinstance(data, list) else None


def check_outputs(prefix: str, data_dir: Path, backup_dir: Path) -> tuple[list[str], bool]:
    """Restore files a scrape emptied or broke. Returns (notes, restored_any)."""
    notes, restored = [], False
    for backup in sorted(backup_dir.glob(f"{prefix}*.json")):
        before = count_records(backup) or 0
        current = data_dir / backup.name
        after = count_records(current) if current.exists() else None
        if before and not after:  # empty, missing or unreadable
            shutil.copy2(backup, current)
            notes.append(f"{backup.name}: came back {'empty' if after == 0 else 'unreadable'}, "
                         f"restored previous {before} records")
            restored = True
        elif before and after < before * SHRINK_WARNING:
            notes.append(f"{backup.name}: {before} -> {after} records (kept, check it)")
    return notes, restored


def prune_runs(logs_dir: Path, keep: int = KEEP_RUNS) -> None:
    runs = sorted(p for p in logs_dir.iterdir() if p.is_dir())
    for old in runs[:-keep]:
        shutil.rmtree(old)


def run_pipeline(only=None, skip_scrape=False, dry_run=False, root: Path = ROOT,
                 scrapers=None, stages=None, scrape_timeout=SCRAPE_TIMEOUT_S,
                 stage_timeout=STAGE_TIMEOUT_S, out=print) -> int:
    scrapers = SCRAPERS if scrapers is None else scrapers
    stages = STAGES if stages is None else stages
    data_dir = root / "data"
    (root / "logs").mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir, n = root / "logs" / stamp, 1
    while run_dir.exists():
        n += 1
        run_dir = root / "logs" / f"{stamp}-{n}"
    run_dir.mkdir()

    lock_file = (root / "logs" / "pipeline.lock").open("w")
    try:
        fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        out("Another pipeline run is in progress (logs/pipeline.lock). Not starting.")
        return 2

    try:
        results: list[StepResult] = []
        retailer_problem = False

        if not skip_scrape:
            backup_dir = run_dir / "data_before"
            if data_dir.exists():
                shutil.copytree(data_dir, backup_dir)
            else:
                backup_dir.mkdir()
            for key in only or list(scrapers):
                cmd, prefix = scrapers[key]
                start = time.monotonic()
                ok, detail = run_logged(cmd, run_dir / f"scrape-{key}.log", scrape_timeout, root)
                notes, restored = check_outputs(prefix, data_dir, backup_dir)
                results.append(StepResult(f"scrape {key}", ok and not restored,
                                          time.monotonic() - start, detail, notes))
                retailer_problem |= not ok or restored

        for name, cmd in stages:
            cmd = cmd + (["--dry-run"] if dry_run and name in DRY_RUN_STAGES else [])
            start = time.monotonic()
            ok, detail = run_logged(cmd, run_dir / f"{name}.log", stage_timeout, root)
            results.append(StepResult(name, ok, time.monotonic() - start, detail))
            if not ok:
                break

        stage_failed = any(not r.ok for r in results if not r.name.startswith("scrape "))
        code = 2 if stage_failed else 1 if retailer_problem else 0

        out(f"Pipeline run {run_dir.name}{' (dry run)' if dry_run else ''}")
        for r in results:
            status = "ok" if r.ok else "FAILED"
            out(f"  {r.name:<22} {status:<7} {r.seconds:7.1f}s  {r.detail}")
            for note in r.notes:
                out(f"      ! {note}")
        skipped = [n for n, _ in stages][len([r for r in results if not r.name.startswith("scrape ")]):]
        if skipped:
            out(f"  not run: {', '.join(skipped)}")
        out(f"Logs: {run_dir}")
        out({0: "Result: OK", 1: "Result: finished, but a retailer needs attention",
             2: "Result: FAILED, a processing stage did not finish"}[code])
        prune_runs(root / "logs")
        return code
    finally:
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full Quote Yard update.")
    parser.add_argument("--only", nargs="+", choices=list(SCRAPERS),
                        help="scrape only these retailers")
    parser.add_argument("--skip-scrape", action="store_true",
                        help="reprocess the data/ already on disk")
    parser.add_argument("--dry-run", action="store_true",
                        help="load and match roll back (scraping still writes data/)")
    args = parser.parse_args()
    if args.only and args.skip_scrape:
        parser.error("--only and --skip-scrape cannot be combined")
    sys.exit(run_pipeline(args.only, args.skip_scrape, args.dry_run))


if __name__ == "__main__":
    main()
