#!/usr/bin/env python3
"""Offline balance check against a Money Manager sqlite export.

Formula (proven): sum over active ZINOUTCOME rows (ZISDEL IS NULL OR 0) for a
given ZASSETUID: ZDO_TYPE '1' (expense) +amount, '0' (income) -amount,
'4' (transfer-in) -amount, '3' (transfer-out) +amount.

Usage: python3 verify_db.py <sqlite> <card-uuid> <tad> [--until YYYY-MM-DD]
"""
import argparse
import sqlite3
import sys


def balance(db_path: str, asset_uid: str, until: str | None) -> tuple[float, int]:
    con = sqlite3.connect(db_path)
    q = """
        SELECT ZDO_TYPE, ZAMOUNT FROM ZINOUTCOME
        WHERE (ZISDEL IS NULL OR ZISDEL = 0) AND ZASSETUID = ?
    """
    params = [asset_uid]
    if until:
        q += " AND ZTXDATESTR <= ?"
        params.append(until)
    rows = con.execute(q, params).fetchall()
    con.close()

    total = 0.0
    sign = {"1": 1, "0": -1, "4": -1, "3": 1}
    for do_type, amount in rows:
        total += sign.get(do_type, 0) * (amount or 0.0)
    return total, len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sqlite")
    ap.add_argument("card_uuid")
    ap.add_argument("tad", type=float)
    ap.add_argument("--until", default=None, help="filter ZTXDATESTR <= this date")
    a = ap.parse_args()

    bal, n = balance(a.sqlite, a.card_uuid, a.until)
    diff = bal - a.tad
    verdict = "PASS" if abs(diff) <= 1.01 else "CHECK"
    until_note = f" until={a.until}" if a.until else ""
    print(f"balance={bal:.2f} tad={a.tad:.2f} diff={diff:+.2f} rows={n}{until_note} {verdict}")


def demo():
    """ponytail: smallest self-check — sign math on synthetic rows, no db needed."""
    import tempfile, os
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE ZINOUTCOME (ZISDEL INTEGER, ZAMOUNT FLOAT, ZDO_TYPE VARCHAR,
                 ZASSETUID VARCHAR, ZTXDATESTR VARCHAR)""")
    rows = [
        (None, 100.0, "1", "cardA", "2026-07-01"),  # expense +100
        (None, 20.0, "0", "cardA", "2026-07-02"),   # income -20
        (None, 30.0, "4", "cardA", "2026-07-03"),   # transfer-in -30
        (None, 5.0, "3", "cardA", "2026-07-04"),    # transfer-out +5
        (1, 9999.0, "1", "cardA", "2026-07-05"),    # deleted, ignored
        (None, 100.0, "1", "cardA", "2026-08-01"),  # after --until cutoff
    ]
    con.executemany("INSERT INTO ZINOUTCOME VALUES (?,?,?,?,?)", rows)
    con.commit()
    con.close()

    bal_all, n_all = balance(path, "cardA", None)
    assert n_all == 5, n_all  # excludes the deleted row
    assert abs(bal_all - 155.0) < 1e-9, bal_all  # 100-20-30+5

    bal_cut, n_cut = balance(path, "cardA", "2026-07-04")
    assert n_cut == 4, n_cut
    assert abs(bal_cut - 55.0) < 1e-9, bal_cut  # 100-20-30+5, excludes Aug row

    os.remove(path)
    print("demo OK")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        main()
