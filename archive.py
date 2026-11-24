"""Import explicitly selected LINE export files into a per-user archive."""
import argparse
from collections import Counter
from contextlib import closing
from datetime import date
import os
from pathlib import Path
import re
import sqlite3

ROOT = Path(os.environ["LOCALAPPDATA"]) / "LineExportArchive"
INBOX = ROOT / "inbox"
DATABASE = ROOT / "archive.sqlite"
MAX_BYTES = 32 * 1024 * 1024
DAY = re.compile(r"^(?P<year>\d{4})[./-](?P<month>\d{1,2})[./-](?P<day>\d{1,2})(?:\s*(?:[（(][^）)]{1,12}[）)]|\S{1,4}))?$")
MESSAGE = re.compile(r"^(?P<hour>[01]?\d|2[0-3]):(?P<minute>[0-5]\d)\t([^\t]+)\t(.*)$")
SCHEMA = """
CREATE TABLE IF NOT EXISTS message (
    id INTEGER PRIMARY KEY,
    chat TEXT NOT NULL,
    stamp TEXT NOT NULL,
    sender TEXT NOT NULL,
    body TEXT NOT NULL,
    occurrence INTEGER NOT NULL,
    UNIQUE (chat, stamp, sender, body, occurrence)
);
CREATE TABLE IF NOT EXISTS imported (
    name TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    modified INTEGER NOT NULL
);
"""


def parse(source):
    """Parse year-first dated exports with tab-separated 24-hour messages."""
    current_day = None
    current = None
    body = []
    for line in source.splitlines():
        day = DAY.fullmatch(line)
        if day:
            try:
                parsed_day = date(**{key: int(value) for key, value in day.groupdict().items()})
            except ValueError:
                day = None
        message = MESSAGE.fullmatch(line) if current_day and not day else None
        if day or message:
            if current:
                yield (*current, "\n".join(body).rstrip("\n"))
                current = None
            if day:
                current_day = parsed_day
            else:
                hour, minute, sender, text = message.groups()
                current = (f"{current_day} {int(hour):02}:{minute}", sender)
                body = [text]
        elif current:
            body.append(line)
    if current:
        yield (*current, "\n".join(body).rstrip("\n"))


def import_exports():
    INBOX.mkdir(parents=True, exist_ok=True)
    imported, skipped = 0, 0
    with closing(sqlite3.connect(DATABASE, timeout=15)) as db:
        db.executescript(SCHEMA)
        for path in sorted(INBOX.glob("*.txt")):
            try:
                if path.is_symlink() or not path.is_file():
                    continue
                stat = path.stat()
                version = (stat.st_size, stat.st_mtime_ns)
                if db.execute("SELECT size, modified FROM imported WHERE name = ?", (path.name,)).fetchone() == version:
                    continue
                with path.open("rb") as stream:
                    data = stream.read(MAX_BYTES + 1)
                if not 0 < len(data) <= MAX_BYTES or path.stat() != stat:
                    skipped += 1
                    continue
                encoding = "utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"
                messages = Counter(parse(data.decode(encoding)))
            except (OSError, UnicodeError):
                skipped += 1
                continue
            if not messages:
                skipped += 1
                continue
            with db:
                db.executemany(
                    """INSERT OR IGNORE INTO message (chat, stamp, sender, body, occurrence)
                    VALUES (?, ?, ?, ?, ?)""",
                    ((path.stem, *message, occurrence)
                     for message, count in messages.items()
                     for occurrence in range(1, count + 1)),
                )
                db.execute("INSERT OR REPLACE INTO imported VALUES (?, ?, ?)", (path.name, *version))
            imported += 1
    return imported, skipped


def read_database():
    if not DATABASE.is_file():
        return None
    return closing(sqlite3.connect(DATABASE.as_uri() + "?mode=ro", uri=True))


def archive_status():
    database = read_database()
    if database is None:
        return {}
    with database as db:
        return {
            chat: {"count": count, "first": first, "last": last}
            for chat, count, first, last in db.execute(
                "SELECT chat, count(*), min(stamp), max(stamp) FROM message GROUP BY chat ORDER BY chat"
            )
        }


def search(chat, keyword="", since=None, until=None, before_id=None, limit=25):
    for bound in (since, until):
        if bound is not None and date.fromisoformat(bound).isoformat() != bound:
            raise ValueError("Use YYYY-MM-DD for date bounds.")
    if since and until and since >= until:
        raise ValueError("The exclusive end date must follow the start date.")
    limit = max(1, min(limit, 25))
    database = read_database()
    if database is None:
        return {"messages": [], "next_before_id": None}
    with database as db:
        rows = db.execute(
            """SELECT id, stamp, sender, substr(body, 1, 2000), length(body) FROM message
            WHERE chat = ? AND instr(body, ?) > 0 AND stamp >= ? AND stamp < ? AND id < ?
            ORDER BY id DESC LIMIT ?""",
            (chat, keyword, since or "", until or "~", before_id if before_id is not None else 2**63 - 1, limit + 1),
        ).fetchall()
    return {
        "messages": [
            {"id": item_id, "local_time": stamp, "sender": sender[:150], "text": text,
             "text_truncated": body_length > 2000}
            for item_id, stamp, sender, text, body_length in rows[:limit]
        ],
        "next_before_id": rows[limit - 1][0] if len(rows) > limit else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.parse_args()
    imported, skipped = import_exports()
    print(f"Imported exports: {imported}. Skipped exports: {skipped}.")
