"""Persist a compact, auditable summary of the raw hourly ATG audit JSON."""
import hashlib
import json
import sys
from pathlib import Path


def main():
    source, destination = map(Path, sys.argv[1:3])
    raw = source.read_bytes()
    audit = json.loads(raw)
    evidence = {
        "start_utc": audit["start_utc"],
        "end_utc": audit["end_utc"],
        "raw_local_file": str(source),
        "raw_local_sha256": hashlib.sha256(raw).hexdigest(),
        "index": audit["index"],
        "probe": audit["probe"],
        "pdfs": [
            {k: v for k, v in p.items() if k not in ("hits", "page_stats", "first_page")}
            for p in audit["pdfs"]
        ],
        "pages": [
            {k: v for k, v in page.items() if k != "relevant_links"}
            | {"relevant_links": page.get("relevant_links", [])[-15:]}
            for page in audit["pages"]
        ],
        "convocation": audit["convocation"],
        "limitations": [
            "Text extraction only; no independent visual inspection of all pages",
            "PDF signature flags observed, but no cryptographic signature validation",
            "No access to restricted HR/DIGP systems",
            "HTTP 404 is not proof of permanent absence",
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"path": str(destination), "bytes": destination.stat().st_size,
                      "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                      "raw_sha256": evidence["raw_local_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
