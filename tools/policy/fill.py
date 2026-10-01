#!/usr/bin/env python3
"""Replace @@S@@ (Settings tab), @@T@@ (telemetry toggle), @@A@@ (Recently Deleted album) in bodies
with the app's own strings from ui_terms.tsv, so ZWNJ and tanwin never depend on typing."""
import csv, re
from pathlib import Path
HERE = Path(__file__).parent
rows = {r["lang"]: r for r in csv.DictReader(open(HERE / "ui_terms.tsv"), delimiter="\t")}
for body in sorted((HERE / "bodies").glob("*.html")):
    t = body.read_text()
    if "@@" not in t:
        continue
    r = rows[body.stem]
    album = re.split(r"\s*[→←]\s*", r["cleanup_step_navigate_pre26"])[-1].strip("«»「」 ")
    if "Recently Deleted" in album:
        album = "Recently Deleted"
    t = t.replace("@@S@@", r["tab_settings"]).replace("@@T@@", r["settings_telemetry_toggle"].rstrip("۔")).replace("@@A@@", album)
    assert "@@" not in t, body
    body.write_text(t)
    print("filled", body.stem)
