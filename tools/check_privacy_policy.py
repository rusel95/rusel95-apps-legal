#!/usr/bin/env python3
"""Check every translation of Compresso's privacy policy against the English original.

    python3 tools/check_privacy_policy.py

The English page is the source of truth. A translation that loses a link, a list item, a
section or a number (the 14 months, the 30 days, the age of 13) fails, and so does one whose
language switcher or "English prevails" note is broken. Run it after every edit to any page.
"""
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "MediaCleaner"
RTL = {"ar", "he", "ur"}
MUST_CONTAIN = ["Compresso", "Sentry", "Google Analytics", "RevenueCat", "iCloud", "IDFA", "AdServices",
                "ruslanpopesku95@gmail.com", "14", "30", "13"]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.html_attrs, self.tags, self.hrefs, self.switcher, self.current = {}, Counter(), [], [], []
        self.h2, self.note, self.text = [], None, []
        self._in_details = self._in_note = self._in_h2 = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.html_attrs = a
        elif tag == "details":
            self._in_details = True
        elif tag == "p" and a.get("class") == "note":
            self._in_note, self.note = True, []
        elif self._in_details and tag == "a":
            self.switcher.append(a["href"])
            if "aria-current" in a:
                self.current.append(a["href"])
        elif self._in_note and tag == "a":
            self.note.append(a["href"])
        elif not self._in_details:
            self.tags[tag + ("." + a["class"] if "class" in a else "")] += 1
            if tag == "a":
                self.hrefs.append(a["href"].split("?")[0])
            self._in_h2 = tag == "h2"

    def handle_endtag(self, tag):
        if tag == "details":
            self._in_details = False
        elif tag == "p":
            self._in_note = False
        elif tag == "h2":
            self._in_h2 = False

    def handle_data(self, data):
        if self._in_h2:
            self.h2.append(data.strip())
        if not self._in_details and not self._in_note:
            self.text.append(data)


def code_of(path):
    m = re.fullmatch(r"privacy-policy(?:\.(.+))?\.html", path.name)
    return m.group(1) or "en"


def main():
    pages = {code_of(p): p for p in sorted(DIR.glob("privacy-policy*.html"))}
    en = Page(pages["en"].read_text())
    errors = []
    for code, path in pages.items():
        page, fail = Page(path.read_text()), lambda msg: errors.append(f"{path.name}: {msg}")
        if page.html_attrs.get("lang") != code:
            fail(f'<html lang="{page.html_attrs.get("lang")}">, expected "{code}"')
        if (page.html_attrs.get("dir") == "rtl") != (code in RTL):
            fail(f'dir="{page.html_attrs.get("dir")}" is wrong for {code}')
        if sorted(page.hrefs) != sorted(en.hrefs):
            fail(f"links differ from English: {sorted(set(page.hrefs) ^ set(en.hrefs)) or 'counts differ'}")
        for tag, n in en.tags.items():
            if tag != "p.note" and page.tags[tag] != n:
                fail(f"{page.tags[tag]} × <{tag}>, English has {n}")
        numbers = [re.match(r"\d+", h) and re.match(r"\d+", h).group() for h in page.h2]
        if numbers != [str(i) for i in range(1, len(en.h2) + 1)]:
            fail(f"section headings are not numbered 1..{len(en.h2)}: {page.h2}")
        text = " ".join(page.text)
        for token in MUST_CONTAIN:
            if token not in text:
                fail(f"missing {token!r}")
        if sorted(page.switcher) != sorted(p.name for p in pages.values()):
            fail(f"language switcher links {len(page.switcher)} pages, not the {len(pages)} that exist")
        if page.current != [path.name]:
            fail(f"switcher marks {page.current} as current")
        if code == "en":
            if page.note is not None:
                fail("the English original must not carry the translation note")
        elif page.note != ["privacy-policy.html"]:
            fail("missing the note that links the English version and says it prevails")
    for e in errors:
        print(e)
    print(f"{len(pages)} pages checked, {len(errors)} problems")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
