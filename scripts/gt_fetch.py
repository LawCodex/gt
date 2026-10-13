#!/usr/bin/env python3
"""Guatemala: decretos of the Congreso de la República (PDFs under
https://www.congreso.gob.gt/assets/uploads/info_legislativo/decretos/) and the Constitution.

www.congreso.gob.gt sits behind an Incapsula bot challenge (HTTP 403 for non-browser clients),
which we do not circumvent. The PDFs are therefore taken from the Internet Archive's
Wayback Machine captures of those official URLs (CDX listing, latest 200 capture per file,
downloaded through the raw ``id_`` endpoint). Each PDF is checked, its text extracted and
cached ($RAW/text/<name>.json), then the PDF is deleted.

Usage: gt_fetch.py [cdx|download|convert|all]
"""
import json
import os
import re
import sys
import time
from datetime import date

import requests
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gt_pdfmd as P  # noqa: E402

RAW = os.environ.get("RAW", "/Users/magicaltux/projects/lawcodex/_raw/gt")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
CDX = ("https://web.archive.org/cdx/search/cdx?url=congreso.gob.gt/assets/uploads/info_legislativo/decretos/"
       "&matchType=prefix&filter=statuscode:200&filter=mimetype:application/pdf&fl=original,timestamp,length")
CONST = ("http://www.congreso.gob.gt:80/2004/constitucion2/Constitucion.pdf", "20050116080048")
TODAY = date.today().isoformat()
s = requests.Session()
s.headers["User-Agent"] = UA
_last = [0.0]


def get(url, binary=True):
    for k in range(6):
        w = 1.5 - (time.time() - _last[0])
        if w > 0:
            time.sleep(w)
        _last[0] = time.time()
        try:
            r = s.get(url, timeout=(30, 600))
            if r.status_code == 200:
                return r.content if binary else r.text
            if r.status_code in (404, 403):
                return None
            print("HTTP", r.status_code, url, file=sys.stderr, flush=True)
        except requests.RequestException as e:
            print("ERR", url, e, file=sys.stderr, flush=True)
        time.sleep(20 * (k + 1))
    return None


def parse_name(url):
    f = url.rsplit("/", 1)[-1]
    m = re.search(r"(\d{1,4})-(\d{4})\.pdf$", f, re.I)
    if m and 1900 < int(m.group(2)) <= date.today().year:
        return int(m.group(1)), int(m.group(2))
    m = re.fullmatch(r"(\d{1,3})-(\d{2})\.pdf", f, re.I)
    if m:
        y = int(m.group(2))
        return int(m.group(1)), (2000 + y if y < 50 else 1900 + y)
    return None


def cdx():
    txt = get(CDX, binary=False)
    best = {}
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        url, ts = parts[0], parts[1]
        key = parse_name(url)
        if not key:
            continue
        # keep the latest capture of each decree number
        if key not in best or ts > best[key][1]:
            best[key] = (url, ts)
    rows = [{"numero": k[0], "anio": k[1], "url": v[0], "ts": v[1]} for k, v in sorted(best.items(), key=lambda x: (x[0][1], x[0][0]))]
    json.dump(rows, open(os.path.join(RAW, "decretos.json"), "w"), indent=0)
    print("decretos", len(rows))


def fetch_text(url, ts, key):
    d = os.path.join(RAW, "text")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, key + ".json")
    if os.path.exists(out):
        return
    tmp = os.path.join(RAW, "tmp.pdf")
    for k in range(3):
        c = get(f"https://web.archive.org/web/{ts}id_/{url}")
        if not c:
            break
        open(tmp, "wb").write(c)
        if P.pdf_ok(tmp):
            try:
                pages = P.extract_pages(tmp)
            except Exception as e:
                pages = None
                print("PARSE", url, e, file=sys.stderr)
            json.dump({"url": url, "ts": ts, "pages": pages}, open(out, "w"), ensure_ascii=False)
            os.remove(tmp)
            return
    json.dump({"url": url, "ts": ts, "pages": None, "error": "download/verify failed"}, open(out, "w"))
    if os.path.exists(tmp):
        os.remove(tmp)


def download():
    fetch_text(CONST[0], CONST[1], "constitucion")
    rows = json.load(open(os.path.join(RAW, "decretos.json")))
    for i, r in enumerate(rows):
        fetch_text(r["url"], r["ts"], f"{r['anio']}-{r['numero']:04d}")
        if i % 100 == 0:
            print("progress", i, len(rows), flush=True)


def garbled(text):
    """Share of tokens that look like OCR noise (mixed case inside a word, letters glued to digits,
    stray symbols). Clean text-layer PDFs score ~0.03-0.06; OCR layers of scanned gazettes much higher."""
    toks = re.findall(r"\S+", text)
    bad = sum(1 for t in toks if re.search(r"[a-záéíóúñ][A-ZÁÉÍÓÚÑ]|[A-Za-zÁÉÍÓÚÑáéíóúñ]\d|\d[A-Za-zÁÉÍÓÚáéíóú]{2,}|[~_·|\\{}<>@^`]|"
                                       r"[a-zA-Z][.,;:'][a-zA-Z]{2,}", t) and not re.fullmatch(r"\d+[ºª°]|\d+-\d+|[A-Z]\d+", t))
    return bad / max(1, len(toks))


def write(path, front, title, md, pre):
    fm = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, width=1000).strip()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write("\n".join(["---", fm, "---", "", f"# {title}", "", pre, "", md, ""]))


def convert():
    st = {"ok": 0, "scanned": 0, "failed": 0}
    skipped = []
    c = json.load(open(os.path.join(RAW, "text", "constitucion.json")))
    md = P.lines_to_md(P.clean_pages(c["pages"]))
    write(os.path.join(REPO, "constitucion", "constitucion-politica-de-la-republica-de-guatemala.md"),
          {"title": "Constitución Política de la República de Guatemala", "identifier": "Constitución de 1985 (reformada por Acuerdo Legislativo 18-93)",
           "type": "constitution", "jurisdiction": "gt", "language": "es", "date": "1985-05-31", "last_amended": "1993-11-17",
           "status": "in_force", "source": CONST[0].replace(":80", ""),
           "archived_source": f"https://web.archive.org/web/{CONST[1]}/{CONST[0]}", "retrieved": TODAY},
          "Constitución Política de la República de Guatemala", md,
          "> Texto publicado por el Congreso de la República (copia archivada por el Internet Archive, 2005); "
          "incluye las reformas del Acuerdo Legislativo 18-93 (consulta popular de 1994). Sin reformas posteriores.")
    rows = json.load(open(os.path.join(RAW, "decretos.json")))
    for r in rows:
        key = f"{r['anio']}-{r['numero']:04d}"
        p = os.path.join(RAW, "text", key + ".json")
        if not os.path.exists(p):
            continue
        d = json.load(open(p))
        pages = d.get("pages")
        if not pages:
            st["failed"] += 1
            skipped.append((r, "descarga fallida"))
            continue
        empty = sum(1 for t in pages if len(t.strip()) < 150)
        if empty > 0.5 * len(pages):
            st["scanned"] += 1
            skipped.append((r, "PDF escaneado (sin capa de texto)"))
            continue
        if garbled("\n".join(pages)) > 0.10:
            st["garbled"] = st.get("garbled", 0) + 1
            skipped.append((r, "texto OCR ilegible"))
            continue
        md = P.lines_to_md(P.clean_pages(pages))
        title = f"Decreto Número {r['numero']}-{r['anio']}"
        m = re.search(r"\n\s*((?:LEY|C[ÓO]DIGO|REFORMAS?|DISPOSICIONES)[^\n]{5,200})", "\n".join(pages[:2]))
        sub = re.sub(r"\s+", " ", m.group(1)).strip() if m else None
        write(os.path.join(REPO, "decretos", str(r["anio"]), f"decreto-{r['numero']:03d}-{r['anio']}.md"),
              {"title": title + (f" — {sub}" if sub else ""), "identifier": f"Decreto {r['numero']}-{r['anio']}",
               "type": "decree-law" if r["anio"] < 1986 else "act", "jurisdiction": "gt", "language": "es",
               "year": r["anio"], "status": "unknown", "source": r["url"],
               "archived_source": f"https://web.archive.org/web/{r['ts']}/{r['url']}", "retrieved": TODAY},
              title + (f" — {sub}" if sub else ""), md,
              "> Texto del PDF publicado por el Congreso de la República (copia archivada por el Internet Archive); "
              "texto original, no consolidado.")
        st["ok"] += 1
    json.dump(skipped, open(os.path.join(RAW, "skipped.json"), "w"), indent=0)
    print(st)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd in ("cdx", "all"):
        cdx()
    if cmd in ("download", "all"):
        download()
    if cmd in ("convert", "all"):
        convert()
