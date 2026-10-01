import json, urllib.request
from html.parser import HTMLParser

URL = "https://twu.tennis-warehouse.com/learning_center/stringstiffnesstool.php"

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.rows = []; s.row = None; s.cell = None
    def handle_starttag(s, t, a):
        if t == "tr": s.row = []
        elif t in ("td", "th") and s.row is not None: s.cell = ""
    def handle_data(s, d):
        if s.cell is not None: s.cell += d
    def handle_endtag(s, t):
        if t in ("td", "th") and s.cell is not None and s.row is not None:
            s.row.append(s.cell.strip()); s.cell = None
        elif t == "tr" and s.row is not None:
            r = s.row
            if len(r) >= 4 and r[2].isdigit():
                s.rows.append([r[0], r[1], int(r[2]), r[3]])
            s.row = None

req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "ignore")
p = P(); p.feed(html)
if len(p.rows) < 300:
    raise SystemExit("Zu wenige Zeilen gefunden: " + str(len(p.rows)))
with open("strings.json", "w", encoding="utf-8") as f:
    json.dump(p.rows, f, ensure_ascii=False, separators=(",", ":"))
print(len(p.rows), "Saiten gespeichert")
