# LawCodex — Guatemala (gt)

Guatemalan legislation as Markdown: the **Constitución Política de la República de Guatemala
(1985, reformed 1993)** and the **decrees of the Congreso de la República** (Decretos — the
form in which Guatemalan laws and codes are enacted) whose official PDF has a text layer, from
the Congreso's website as preserved by the **Internet Archive**.

Part of [LawCodex](https://github.com/LawCodex): one public repository per jurisdiction.

Retrieved: **2026-10-13**. Language: Spanish (`es`).

Status: **partial** — see "What is NOT covered".

## What is covered

| Category | Directory | Files |
|---|---|---|
| Constitución Política de la República de Guatemala (1985, with the 1993 reforms) | `constitucion/` | 1 |
| Decretos del Congreso (laws, codes, approvals), by year | `decretos/<year>/decreto-<nnn>-<year>.md` | 458 |

The Congreso publishes each decree as a PDF at
`https://www.congreso.gob.gt/assets/uploads/info_legislativo/decretos/<file>.pdf`. The Internet
Archive's CDX index lists 2,050 distinct decree numbers among its captures of that folder;
1,495 of them are scanned images (no text layer — essentially all decrees before ~2008)
and were not converted (no OCR); 78 more have only a poor OCR text layer (garbled; skipped);
a few could not be downloaded. Texts are the decrees as
enacted (not consolidated); amendments are separate decrees.

Front matter: `source` is the official URL, `archived_source` the Wayback Machine capture used.

## What is NOT covered

- **Live access to www.congreso.gob.gt**: the site is behind an Incapsula bot challenge
  (HTTP 403 for non-browser clients). We do not circumvent such challenges; the archived copies
  of the official PDFs were used instead.
- Scanned decrees (pre-2000 for the most part), decrees never captured by the Internet Archive,
  and the older files named `gtd?x<number><year>.pdf` (decrees of the 1930s–1980s, scanned).
- Consolidated texts of the codes (Código Civil, Código Penal, Código de Comercio, Código de
  Trabajo… — the original decrees of these codes are older scanned PDFs).
- Acuerdos gubernativos and other executive norms.

## Source

- Congreso de la República de Guatemala, "Decretos" (PDFs) — via the Internet Archive
  Wayback Machine (CDX API, latest successful capture of each file, raw `id_` download).
- Constitution: `http://www.congreso.gob.gt/2004/constitucion2/Constitucion.pdf` (capture of
  16 Jan 2005).

## Copyright

Guatemala's Ley de Derecho de Autor y Derechos Conexos (Decreto 33-98) excludes laws and other
official texts from copyright protection.

## Regenerate

```
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
RAW=/path/to/scratch .venv/bin/python scripts/gt_fetch.py all
```
