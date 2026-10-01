#!/usr/bin/env python3
"""Each translated body must name the in-app toggle, the Settings tab and the Recently Deleted
album exactly as the app's own Localizable.xcstrings does, so readers can find them."""
import csv
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
rows = {r["lang"]: r for r in csv.DictReader(open(HERE / "ui_terms.tsv"), delimiter="\t")}
bad = 0
for body in sorted((HERE / "bodies").glob("*.html")):
    code = body.stem
    text = body.read_text()
    r = rows[code]
    album = re.split(r"\s*[→←]\s*", r["cleanup_step_navigate_pre26"])[-1].strip("«»「」 ")
    if "Recently Deleted" in album:
        album = "Recently Deleted"
    # The app's own strings carry a suffix here ("…'e gidin", "…に移動") or, for Catalan,
    # a half-Spanish album name; the policy names the iOS album itself.
    album = {"tr": "Son Silinenler", "ja": "最近削除した項目", "ko": "최근 삭제된 항목",
             "ca": "Eliminats recentment"}.get(code, album)
    terms = {"settings tab": r["tab_settings"], "toggle": r["settings_telemetry_toggle"].rstrip("۔"),
             "album": album}
    missing = [f"{k}={v!r}" for k, v in terms.items() if v not in text]
    if missing:
        bad += 1
        print(code, "missing", ", ".join(missing))
print(f"{len(list((HERE / 'bodies').glob('*.html')))} bodies, {bad} with missing UI terms")
sys.exit(1 if bad else 0)
