"""Build docs/data/explorer.json for the GitHub Pages explorer from the data/ registers.

Run after extract.py whenever the registers change:

    python3 site-build.py
"""
import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "docs" / "data" / "explorer.json"


def load_jsonl(path):
    return [json.loads(line) for line in open(path)]


def main():
    reqs = load_jsonl(ROOT / "data" / "requirements.jsonl")
    fams = json.load(open(ROOT / "data" / "families.json"))["families"]
    refs = load_jsonl(ROOT / "data" / "references.jsonl")
    anoms = load_jsonl(ROOT / "data" / "anomalies.jsonl")

    counts = collections.Counter(r["family_id"] for r in reqs)
    families = [
        {
            "id": f["id"], "t": f.get("title", ""), "dt": f.get("data_type"),
            "kind": f["kind"], "parent": f.get("parent_id"),
            "leaf": f.get("is_leaf_deliverable"), "n": counts.get(f["id"], 0),
            "page": f.get("drl_page"),
        }
        for f in fams
    ]

    references = sorted(
        (
            {
                "id": r["id"], "cat": r["category"], "doc": r.get("canonical_identifier"),
                "n": r["instance_count"], "fams": r["family_ids"],
                "title": (r.get("title_variants") or [""])[0][:80],
                "idv": r.get("identifier_variants", []),
                "txt": (r.get("verbatim_texts") or [""])[0][:110],
            }
            for r in refs
        ),
        key=lambda x: -x["n"],
    )

    anomalies = [
        {
            "id": a["id"], "type": a["type"], "status": a["status"],
            "fam": a.get("family_id"), "page": a.get("page"),
            "d": (a["details"] if isinstance(a.get("details"), str) else a["details"].get("reason", ""))[:130],
            "printed": a.get("printed_identifier"), "official": a.get("official_identifier"),
        }
        for a in anoms
    ]

    records = [
        {
            "id": r["id"], "fam": r["family_id"], "a": r["atomic_text"][:260],
            "actor": r["actor"], "mod": r["modality"],
            "sec": (r["source"].get("section") or "")[:40], "p": r["source"]["page"],
            "v": r["source"]["verbatim_text"][:300],
        }
        for r in reqs
    ]

    texts = collections.Counter(r["atomic_text"] for r in reqs)
    echo = []
    for text, n in texts.most_common(60):
        if n < 8:
            break
        echo.append({
            "t": text[:110], "n": n,
            "fams": sorted({r["family_id"] for r in reqs if r["atomic_text"] == text}),
        })

    agg = {
        "total": len(reqs), "items": 5031, "leaf": 84, "ids": 98,
        "dt": dict(collections.Counter(f.get("data_type") for f in fams if f.get("data_type"))),
        "actor": dict(collections.Counter(r["actor"] for r in reqs)),
        "mod": dict(collections.Counter(r["modality"] for r in reqs)),
        "sec": dict(collections.Counter((r["source"].get("section") or "other") for r in reqs).most_common(8)),
        "dupInstances": sum(c for c in texts.values() if c > 1),
        "riskReqs": sum(1 for r in reqs if "risk" in r["atomic_text"].lower()),
        "echo": echo[:8],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    blob = {"agg": agg, "fams": families, "refs": references, "anoms": anomalies, "reqs": records}
    OUT.write_text(json.dumps(blob, separators=(",", ":")))
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB, {len(records)} requirements)")


if __name__ == "__main__":
    main()
