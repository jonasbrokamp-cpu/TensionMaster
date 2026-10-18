import json, os, re, time, urllib.request
from html.parser import HTMLParser

URL = "https://twu.tennis-warehouse.com/learning_center/stringstiffnesstool.php"
UA = {"User-Agent": "Mozilla/5.0"}
MAX_NEW = 200
PAUSE = 1.5

class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.rows = []; s.row = None; s.cell = None; s.href = None
    def handle_starttag(s, t, a):
        if t == "tr": s.row = []; s.href = None
        elif t in ("td", "th") and s.row is not None: s.cell = ""
        elif t == "a" and s.cell is not None: s.href = dict(a).get("href")
    def handle_data(s, d):
        if s.cell is not None: s.cell += d
    def handle_endtag(s, t):
        if t in ("td", "th") and s.cell is not None and s.row is not None:
            s.row.append(s.cell.strip()); s.cell = None
        elif t == "tr" and s.row is not None:
            r = s.row
            if len(r) >= 4 and r[2].isdigit():
                s.rows.append([r[0], r[1], int(r[2]), r[3], s.href or ""])
            s.row = None

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read().decode("utf-8", "ignore")

p = P(); p.feed(get(URL)); rows = p.rows
if len(rows) < 300:
    raise SystemExit("Zu wenige Zeilen: " + str(len(rows)))
with open("strings.json", "w", encoding="utf-8") as f:
    json.dump([r[:4] for r in rows], f, ensure_ascii=False, separators=(",", ":"))

def has_mm(n):
    return bool(re.search(r"1\.\d{1,3}", n)) or bool(re.search(r"\b1[0-4]\d\s*/\s*1[5-9]", n))

gj = {}
if os.path.exists("gauges.json"):
    try: gj = json.load(open("gauges.json", encoding="utf-8"))
    except Exception: gj = {}

SL = re.compile(r"(\d{2}L?)\s*/\s*(1\.\d{2,3})", re.I)
def find(page):
    t = re.search(r"<title>(.*?)</title>", page, re.S | re.I)
    m = SL.search(t.group(1) if t else "") or re.search(r"Gauge:\s*(\d{2}L?)\s*/\s*(1\.\d{2,3})\s*mm", page, re.I)
    return (m.group(1).upper(), float(m.group(2))) if m else (None, None)

new = 0
for r in rows:
    key = r[0] + "|" + r[1]
    if has_mm(r[1]) or key in gj or "tennis-warehouse.com" not in r[4]:
        continue
    if new >= MAX_NEW:
        break
    try:
        g, mm = find(get(r[4]))
    except Exception as e:
        print("Fehler:", key, e)
        if "404" in str(e) or "410" in str(e):
            gj[key] = {"mm": None, "src": r[4], "err": "nicht gefunden"}
            new += 1
        time.sleep(PAUSE); continue
    w = re.search(r"\b(1[5-9]L?)\b", r[1])
    if mm and w and g and g != w.group(1).upper():
        mm = None
    gj[key] = {"mm": mm, "src": r[4]}
    new += 1
    time.sleep(PAUSE)

with open("gauges.json", "w", encoding="utf-8") as f:
    json.dump(gj, f, ensure_ascii=False, sort_keys=True, indent=0)
miss = [r for r in rows if not has_mm(r[1]) and not (gj.get(r[0] + "|" + r[1]) or {}).get("mm")]
with open("fehlende_dicken.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(r[0] + " | " + r[1] + " | " + r[3] for r in sorted(miss)) + "\n")
print(len(rows), "Saiten,", new, "neu abgefragt,", len(miss), "ohne mm")
