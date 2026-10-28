"""Read-only primary-source audit for Sao Vicente CP 02/2026, ATG.

Run from the repository root. All HTTP results are evidence, not absence proofs.
"""
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
import re
import tempfile
import time
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

import fitz
import requests
from lxml import html

ROOT = "https://www.saovicente.sp.gov.br"
INDEX = ROOT + "/transparencia/bom"
CONV = ROOT + "/institucional/concursos/convocacoes/convocacao-concursos-de-2026/convocacao-dias-03-04-05-e-06-de-novembro-de-2026.pdf"
PAGES = [
    ROOT + "/institucional/concursos/concurso-no-02-2026",
    ROOT + "/institucional/concursos/concurso-no-02-2026?b_start:int=20",
    ROOT + "/institucional/concursos/concurso-no-02-2026?b_start:int=40",
    ROOT + "/institucional/concursos",
    ROOT + "/institucional/concursos/convocacoes/convocacao-concursos-de-2026",
    "https://www.ibamsp-concursos.org.br/informacoes/134/",
]
PAT = re.compile(r"bom-edicao-(\d+)", re.I)
TERMS = ["29820", "gabriel veloso", "caio monticelli", "eduardo poliselli", "assistente tecnico de gestao", "concurso publico n 02/2026", "prorrogacao de posse", "desistencia", "nomeacao", "convocacao", "reclassificacao", "vacancia", "exoneracao", "posse", "seg es", "digp"]
RUN_ID = dt.datetime.now(dt.timezone(dt.timedelta(hours=-3))).strftime("%Y%m%d_%H%M%S")
OUT = Path(tempfile.gettempdir()) / ("sv_atg_" + RUN_ID)
OUT.mkdir(parents=True, exist_ok=True)

def fetch(url, method="GET"):
    for attempt in range(3):
        try:
            r = requests.request(method, url, timeout=(8, 20), headers={"User-Agent": "Mozilla/5.0 (compatible; municipal-publication-audit/1.0)"})
            data = r.content if method == "GET" else b""
            return {"url": url, "http": r.status_code, "bytes": len(data), "pdf": data.startswith(b"%PDF-"), "data": data, "content_type": r.headers.get("Content-Type", ""), "error": None}
        except requests.RequestException as e:
            error = f"{type(e).__name__}: {str(e)[:160]}"
            if attempt < 2:
                time.sleep(0.5 * (attempt + 1))
    return {"url": url, "http": None, "bytes": 0, "pdf": False, "data": b"", "content_type": "", "error": error}

def normalize(s):
    s = unicodedata.normalize("NFKD", s.lower())
    return "".join(c for c in s if not unicodedata.combining(c))

def pdf_audit(r):
    raw = r["data"]
    d = fitz.open(stream=raw, filetype="pdf")
    pages = []
    all_text = []
    hits = []
    for i, page in enumerate(d):
        t = page.get_text(sort=True)
        all_text.append(f"\n===== PAGE {i + 1} / {len(d)} =====\n{t}")
        pages.append({"page": i + 1, "chars": len(t), "images": len(page.get_images())})
        nt = normalize(t)
        for term in TERMS:
            start = nt.find(term)
            if start >= 0:
                hits.append({"page": i + 1, "term": term, "excerpt": t[max(0,start-130):start+260].replace("\n", " ")[:390]})
        if "assistente" in nt and "gestao" in nt:
            for m in re.finditer(r"assistente.{0,30}gestao", nt):
                hits.append({"page": i + 1, "term": "ATG context", "excerpt": t[max(0,m.start()-130):m.start()+300].replace("\n", " ")[:430]})
    name = re.sub(r"[^a-z0-9_-]", "_", r["url"].rsplit("/",1)[-1].lower())
    (OUT / (name + ".pdf")).write_bytes(raw)
    (OUT / (name + ".txt")).write_text("\n".join(all_text), encoding="utf-8")
    return {"url":r["url"], "http":r["http"], "bytes":len(raw), "sha256":hashlib.sha256(raw).hexdigest(), "pages":len(d), "pages_extracted":len(pages), "empty_pages":[p["page"] for p in pages if p["chars"]<15], "first_page":d[0].get_text(sort=True)[:800] if len(d) else "", "signature_flags":d.get_sigflags(), "hits":hits, "page_stats":pages}

def inspect_page(r):
    out={k:v for k,v in r.items() if k != "data"}
    if r["http"] != 200: return out
    try:
        tree=html.fromstring(r["data"])
        links=[{"text":" ".join(a.text_content().split())[:140],"href":urljoin(r["url"],a.get("href"))} for a in tree.xpath("//a[@href]")]
        out["relevant_links"]=[x for x in links if re.search(r"(convoca|2026|02/2026|32\s*[-–]|33\s*[-–]|atg|novembro)", x["text"]+" "+x["href"],re.I)][-100:]
        out["document_number_candidates"]=[x["text"] for x in links if re.match(r"\s*(\d{1,2})\s*[-–]",x["text"])][-40:]
        out["links_total"]=len(links)
    except Exception as e: out["parse_error"]=str(e)
    return out

def main():
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    index=fetch(INDEX)
    if index["http"]!=200:
        raise RuntimeError("BOM index not accessible: "+str(index["error"] or index["http"]))
    tree=html.fromstring(index["data"])
    real=[]
    for a in tree.xpath("//a[@href]"):
        href=urljoin(INDEX,a.get("href"))
        m=PAT.search(href)
        if m and int(m.group(1))>=687:
            u=href.removesuffix("/view")
            if u not in [x["url"] for x in real]:
                real.append({"edition":int(m.group(1)),"url":u,"label":" ".join(a.text_content().split())[:130]})
    urls={x["url"] for x in real}
    variants=["", "-extra", "-extra-1", "-extra-2", "-extra-3", "-suplementar"]
    for n in range(689,701):
        for v in variants:
            urls.add(f"{INDEX}/bom-edicao-{n}{v}-versaoimpressao.pdf")
    for n in range(689,697):
        for v in ["-1-versaoimpressao-1", "-extra-versaoimpressao-1", "-extra-1-versaoimpressao-1", "-extra-4-versaoimpressao", "-extra-5-versaoimpressao", "-extra-6-versaoimpressao"]:
            urls.add(f"{INDEX}/bom-edicao-{n}{v}.pdf")
    urls=sorted(urls)
    with concurrent.futures.ThreadPoolExecutor(max_workers=14) as ex:
        heads=list(ex.map(lambda u:fetch(u,"HEAD"),urls))
        gets=list(ex.map(fetch,urls))
    meta=[{k:v for k,v in x.items() if k!="data"} for x in gets]
    valid=[x for x in gets if x["pdf"]]
    real_pdfs=[x for x in real if next((r for r in gets if r["url"]==x["url"] and r["pdf"]),None)]
    inaccessible=[x for x in real if not next((r for r in gets if r["url"]==x["url"] and r["pdf"]),None)]
    pdfs=[]
    for r in valid:
        if PAT.search(r["url"]) and int(PAT.search(r["url"]).group(1))<=693:
            pdfs.append(pdf_audit(r))
    conv=fetch(CONV)
    if conv["pdf"]: pdfs.append(pdf_audit(conv))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
        page_results=list(ex.map(fetch,PAGES))
    pages=[inspect_page(r) for r in page_results]
    result={"start_utc":start,"end_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"index":{"http":index["http"],"bytes":index["bytes"],"real_hrefs":real},"probe":{"head_status":dict(Counter(str(r["http"]) for r in heads)),"get_status":dict(Counter(str(r["http"]) for r in gets)),"valid_pdf_count":len(valid),"count":len(urls),"results":meta,"inaccessible_listed":inaccessible,"real_valid":real_pdfs},"pdfs":pdfs,"pages":pages,"convocation":{"http":conv["http"],"bytes":conv["bytes"],"pdf":conv["pdf"],"error":conv["error"]},"output_dir":str(OUT)}
    dest=OUT/"audit.json"
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    summary={"start_utc":start,"end_utc":result["end_utc"],"index_last":real[0] if real else None,"listed_issues":len(real),"inaccessible_listed":inaccessible,"probe":{"count":len(urls),"head_status":result["probe"]["head_status"],"get_status":result["probe"]["get_status"],"valid_pdf_count":len(valid)},"pdfs":[{k:v for k,v in p.items() if k not in ("hits","page_stats","first_page")} for p in pdfs],"pages":[{k:v for k,v in p.items() if k not in ("relevant_links",)}|{"new_links":p.get("relevant_links",[])[-12:]} for p in pages],"audit_json":str(dest),"audit_json_sha256":hashlib.sha256(dest.read_bytes()).hexdigest()}
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=="__main__": main()
