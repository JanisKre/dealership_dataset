#!/usr/bin/env python3
"""Derive smaller sample datasets from the 500-record dataset.

    python3 scripts/make_subsets.py            # writes data/*_{250,100,50,10}.*
    python3 scripts/make_subsets.py --check    # verifies the committed files

Selection (deterministic, standard library only):

* Every federal state gets a quota proportional to its share of the
  500 records (largest remainder method). From 50 records up, every state
  gets at least one record.
* Within a state, records are ranked by the SHA-256 hash of their OSM object
  ("node/123"), a reproducible pseudo-random order that does not depend on
  the row order of the source file.
* Smaller sets are subsets of larger ones: 10 ⊂ 50 ⊂ 100 ⊂ 250 ⊂ 500.
* Rows keep their ID from the 500-record file, so every subset can be joined
  back to it; they appear in the same order as there.

The XLSX files are written from the 500-record workbook: same styles, table,
column widths and notes sheet, with the row count, table range, formulas,
cached results and the selection note adapted.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCE_SIZE = 500
SIZES = (250, 100, 50, 10)
MIN_PER_STATE_FROM = 50
STEM = "car_dealerships_germany_{n}"
FIRST_DATA_ROW = 5  # rows 1-2 title, 3 blank, 4 header in the workbook


def read_records() -> tuple[list[str], list[dict[str, str]]]:
    with open(DATA / f"{STEM.format(n=SOURCE_SIZE)}.csv", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def quotas(counts: Counter[str], n: int) -> dict[str, int]:
    """Largest-remainder allocation of n records over the states."""
    total = sum(counts.values())
    # Ties: larger state first, then name, so the result never depends on dict order.
    order = sorted(counts, key=lambda s: (-counts[s], s))
    exact = {s: n * counts[s] / total for s in order}
    q = {s: int(exact[s]) for s in order}
    by_remainder = sorted(order, key=lambda s: (-(exact[s] - q[s]), -counts[s], s))
    for s in by_remainder[: n - sum(q.values())]:
        q[s] += 1
    if n >= MIN_PER_STATE_FROM:
        for s in [s for s in order if q[s] == 0]:
            # Take the record from the state that is most over its exact share.
            donor = max((d for d in order if q[d] > 1), key=lambda d: (q[d] - exact[d], counts[d]))
            q[donor] -= 1
            q[s] = 1
    assert sum(q.values()) == n
    return q


def rank_key(record: dict[str, str]) -> str:
    return hashlib.sha256(f"{record['OSM Type']}/{record['OSM ID']}".encode()).hexdigest()


def select(records: list[dict[str, str]]) -> dict[int, list[dict[str, str]]]:
    counts = Counter(r["Federal State"] for r in records)
    ranked = {
        s: sorted((r for r in records if r["Federal State"] == s), key=rank_key) for s in counts
    }
    position = {r["ID"]: i for i, r in enumerate(records)}
    plans = {n: quotas(counts, n) for n in (SOURCE_SIZE, *SIZES)}
    for larger, smaller in zip((SOURCE_SIZE, *SIZES), SIZES):
        for s in counts:
            assert plans[smaller][s] <= plans[larger][s], (smaller, s)
    result = {}
    for n, plan in plans.items():
        chosen = [r for s in counts for r in ranked[s][: plan[s]]]
        result[n] = sorted(chosen, key=lambda r: position[r["ID"]])
    return result


def csv_bytes(fieldnames: list[str], records: list[dict[str, str]]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writeheader()
    writer.writerows(records)
    return ("﻿" + buf.getvalue()).encode("utf-8")


# --- XLSX -------------------------------------------------------------------

ROW_RE = re.compile(r'<x:row r="(\d+)"[^>]*>.*?</x:row>', re.S)


def cell_styles(row_xml: str) -> list[str]:
    return re.findall(r'<x:c r="[A-Z]+\d+" s="(\d+)"', row_xml)


def restyle(row_xml: str, new_row: int, styles: list[str]) -> str:
    row_xml = re.sub(r'^<x:row r="\d+"', f'<x:row r="{new_row}"', row_xml)
    it = iter(styles)
    return re.sub(
        r'<x:c r="([A-Z]+)\d+" s="\d+"',
        lambda m: f'<x:c r="{m.group(1)}{new_row}" s="{next(it)}"',
        row_xml,
    )


def dealerships_sheet(xml: str, ids: list[str]) -> str:
    rows = {int(m.group(1)): m.group(0) for m in ROW_RE.finditer(xml)}
    data = {r: x for r, x in rows.items() if r >= FIRST_DATA_ROW}
    by_id = {re.search(r"<x:v>(\d+)</x:v>", x).group(1): x for x in data.values()}
    last = max(data)
    first_style = cell_styles(data[FIRST_DATA_ROW])
    middle_style = cell_styles(data[FIRST_DATA_ROW + 1])
    last_style = cell_styles(data[last])
    new_rows = []
    for i, record_id in enumerate(ids):
        style = first_style if i == 0 else last_style if i == len(ids) - 1 else middle_style
        new_rows.append(restyle(by_id[record_id], FIRST_DATA_ROW + i, style))
    head = "".join(x for r, x in sorted(rows.items()) if r < FIRST_DATA_ROW)
    start = xml.index("<x:sheetData>") + len("<x:sheetData>")
    end = xml.index("</x:sheetData>")
    xml = xml[:start] + head + "".join(new_rows) + xml[end:]
    return xml.replace(
        f"Sample Dataset: {SOURCE_SIZE} Car Dealerships", f"Sample Dataset: {len(ids)} Car Dealerships"
    )


def notes_sheet(xml: str, records: list[dict[str, str]], n: int) -> str:
    last = FIRST_DATA_ROW + n - 1
    source_last = FIRST_DATA_ROW + SOURCE_SIZE - 1
    xml = xml.replace(f"$A$5:$A${source_last}", f"$A$5:$A${last}")
    xml = xml.replace(f"$G$5:$G${source_last}", f"$G$5:$G${last}")
    counts = Counter(r["Federal State"] for r in records)
    xml = re.sub(r"(COUNTA\([^<]*\)</x:f><x:v>)\d+", rf"\g<1>{n}", xml)
    xml = re.sub(
        r'(<x:c r="B5" s="\d+" t="n"><x:v>)\d+',
        rf"\g<1>{len(counts)}",
        xml,
    )

    def count_cell(m: re.Match[str]) -> str:
        row = m.group(1)
        state = re.search(rf'<x:c r="A{row}"[^>]*><x:v>([^<]*)</x:v>', xml).group(1)
        return f"{m.group(0)[: -len(m.group(2))]}{counts.get(state, 0)}"

    xml = re.sub(r'<x:c r="B(\d+)"[^>]*><x:f>COUNTIF\([^<]*\)</x:f><x:v>(\d+)', count_cell, xml)

    def share_cell(m: re.Match[str]) -> str:
        row = m.group(1)
        state = re.search(rf'<x:c r="A{row}"[^>]*><x:v>([^<]*)</x:v>', xml).group(1)
        share = round(counts.get(state, 0) / n, 15)
        text = f"{share:.15g}" if share else "0"
        return f"{m.group(0)[: -len(m.group(2))]}{text}"

    xml = re.sub(r'<x:c r="C(\d+)"[^>]*><x:f>B\d+/\$B\$4</x:f><x:v>([^<]*)', share_cell, xml)
    if n != SOURCE_SIZE:
        states = len(counts)
        coverage = "all 16 German federal states" if states == 16 else f"{states} of the 16 German federal states"
        note = (
            f"{n} records drawn from {STEM.format(n=SOURCE_SIZE)} across {coverage}: "
            "quotas proportional to each state's share (largest remainder"
            + (", at least one per state" if n >= MIN_PER_STATE_FROM else "")
            + "), ranked within a state by SHA-256 of the OSM object. "
            "Smaller sets are subsets of larger ones; IDs match the 500-record file."
        )
        xml = re.sub(
            r'(<x:c r="E7" s="\d+" t="str"><x:v>)[^<]*',
            lambda m: m.group(1) + escape(note),
            xml,
        )
    return xml


def xlsx_bytes(records: list[dict[str, str]], n: int) -> bytes:
    source = DATA / f"{STEM.format(n=SOURCE_SIZE)}.xlsx"
    ids = [r["ID"] for r in records]
    out = io.BytesIO()
    with zipfile.ZipFile(source) as zin, zipfile.ZipFile(out, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info)
            if info.filename == "xl/worksheets/sheet1.xml":
                data = dealerships_sheet(data.decode("utf-8"), ids).encode("utf-8")
            elif info.filename == "xl/worksheets/sheet2.xml":
                data = notes_sheet(data.decode("utf-8"), records, n).encode("utf-8")
            elif info.filename == "xl/tables/table1.xml":
                text = data.decode("utf-8")
                data = re.sub(r'ref="A4:O\d+"', f'ref="A4:O{FIRST_DATA_ROW + n - 1}"', text).encode("utf-8")
            zout.writestr(info, data)
    return out.getvalue()


def xlsx_parts(blob: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        return {i.filename: z.read(i) for i in z.infolist()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="verify instead of writing")
    args = parser.parse_args()

    fieldnames, records = read_records()
    selections = select(records)

    # Self-test: the full selection must reproduce the source files exactly.
    assert csv_bytes(fieldnames, selections[SOURCE_SIZE]) == (
        DATA / f"{STEM.format(n=SOURCE_SIZE)}.csv"
    ).read_bytes(), "CSV writer does not reproduce the source file"
    assert xlsx_parts(xlsx_bytes(selections[SOURCE_SIZE], SOURCE_SIZE)) == xlsx_parts(
        (DATA / f"{STEM.format(n=SOURCE_SIZE)}.xlsx").read_bytes()
    ), "XLSX writer does not reproduce the source workbook"

    failures = 0
    for n in SIZES:
        chosen = selections[n]
        csv_path = DATA / f"{STEM.format(n=n)}.csv"
        xlsx_path = DATA / f"{STEM.format(n=n)}.xlsx"
        csv_out = csv_bytes(fieldnames, chosen)
        xlsx_out = xlsx_bytes(chosen, n)
        if args.check:
            ok = (
                csv_path.exists()
                and csv_path.read_bytes() == csv_out
                and xlsx_path.exists()
                and xlsx_parts(xlsx_path.read_bytes()) == xlsx_parts(xlsx_out)
            )
            failures += not ok
            print(f"{'ok  ' if ok else 'DIFF'} {n}")
        else:
            csv_path.write_bytes(csv_out)
            xlsx_path.write_bytes(xlsx_out)
            states = Counter(r["Federal State"] for r in chosen)
            print(f"{n:>4} records, {len(states):>2} states -> {csv_path.name}, {xlsx_path.name}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
