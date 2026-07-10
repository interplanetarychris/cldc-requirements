# CLDC Requirements

An independent, reproducible exploration of the requirements and data-delivery obligations in NASA's July 2026 Commercial Low Earth Orbit Destination Contract (CLDC) draft RFP.

This project treats the PDF as the authoritative source artifact and builds complementary machine-readable views for counting, citation, comparison, review, and eventual revision. It does **not** turn an RFP into a negotiated requirements baseline, replace the solicitation, or provide an official NASA or legal interpretation.

## Why this exists

The document needs to serve people doing different but connected work:

- Program and contract management: delivery burden, milestones, approvals, dependencies, and change control.
- Systems engineering: requirement families, allocation, interfaces, traceability, and derived requirements.
- Safety and mission assurance: applicability, evidence, closure, exceptions, and risk.
- Design and operations: implementation decisions, constraints, and affected system elements.
- Verification and validation: success criteria, methods, evidence, status, and closure.
- Compliance and interpretation: exact source language, incorporated references, ambiguities, conflicts, and rationale.

Because this is a draft RFP, every extracted record should carry `baseline_status: "solicitation"`. A future proposal, negotiation, contract award, modification, or approved provider document is a different baseline and must not silently overwrite this one.

One useful critique of the acquisition is:

> "It's got all the requirements, deliverables, and clauses of a cost-plus contract, but they are stuffed into a firm fixed-price bag."

Treat that as a hypothesis to test with data, not a conclusion to encode. The register should make it possible to measure outcome-oriented requirements versus prescribed processes, recurring reporting, approval gates, Government insight/control, incorporated obligations, and verification burden.

## Source document

Local working copy:

```text
/Users/chris/Downloads/03_CLDC+Integrated+DRD+July+2026.pdf
```

Observed source facts:

- File: `03_CLDC+Integrated+DRD+July+2026.pdf`
- PDF pages: 246
- PDF metadata creation/modification date: 2026-07-02
- SHA-256: `443c2ceaef75b5560dc310a22e584c3f4a964802d1095b6d29e9a589171df3e0`
- General provisions: pages 2-6
- Data Requirements List (DRL): pages 7-9
- DRD definitions: pages 10-246

Do not commit the source PDF or a full-text derivative to a public repository until its publication source and redistribution posture have been recorded. Findings, hashes, locators, schemas, and extraction code can be published independently.

## Initial inventory

The following counts have been checked against both the PDF text layer and rendered pages:

- 60 top-level DRD families.
- 14 top-level DRDs are grouping parents.
- 38 child DRDs.
- 84 leaf deliverables: `60 - 14 + 38`.
- 98 official identifiers in the DRL: 60 top-level plus 38 children.

Lexical occurrences in the PDF text layer:

- `shall`: 736
- `must`: 37
- `required`: 192
- `should`: 78
- `may`: 107
- `will`: 248

These are reproducible word counts, **not** requirement counts. Some occurrences are descriptive, quoted, repeated, Government commitments, or multiple obligations in one sentence. Conversely, mandatory list children often inherit a `shall include` lead-in without repeating a modal verb.

Known source anomalies include:

1. The DRL and CLDC-211 header define CLDC-211.1 through CLDC-211.4, while the corresponding body section headings say CLDC-214.1 through CLDC-214.4 on pages 236-242. Preserve both values and record a suspected alias; do not silently correct the source.
2. CLDC-101 begins its Contents numbering at item 19, apparently continuing the preceding DRD's numbering. Printed ordinal numbers therefore cannot be durable identifiers.
3. A list item can continue across a page boundary and be emitted by an extractor as two items. For example, the CLDC-001 Critical Path item crosses pages 11-12.
4. Required ITAR/EAR notice text contains modal language that is part of the required notice. The obligation to include the notice and the quoted notice content must not be double-counted.

## Extraction decision

Use JSONL as the canonical requirement register:

- one independently addressable record per line;
- easy streaming, validation, diffing, and Git review;
- stable links without loading one large JSON document;
- straightforward conversion to JSON, CSV, HTML, a database, or ReqIF when an actual consumer requires one.

Do not invent custom XML. Export ReqIF only when exchanging data with a requirements-management tool that needs it.

Keep two linked layers so the word "count" remains auditable:

1. **Source items** preserve each addressable paragraph, list item, or table entry after documented page-break repairs.
2. **Atomic requirements** split a source item only when it contains independently verifiable obligations.

Report both counts. Never present a candidate modal-word count as an exact requirement count.

## Proposed outputs

Create these only as the extraction reaches them:

```text
data/manifest.json          source fingerprint, policy, tool versions, and counts
data/families.json          DRD hierarchy and metadata
data/source-items.jsonl     lossless, addressable source items
data/requirements.jsonl     reviewed atomic requirements
data/anomalies.jsonl        numbering, extraction, ambiguity, and conflict findings
extract.py                  minimal reproducible extraction/normalization script
```

Generated Docling and layout files belong under `tmp/` and should not be committed.

## Stable identifiers

Use readable, immutable identifiers assigned once:

```text
CLDC-GEN-REQ-0001
CLDC-001-REQ-0001
CLDC-108.2-REQ-0001
```

An ID must not contain a page number or printed bullet number. Pages and ordinals move when the source is revised. Keep the familiar citation as separate provenance:

```text
CLDC-001, Contents 1.a, PDF page 11
```

If a later baseline moves unchanged text, retain the requirement ID and update its provenance. If it materially changes, preserve history using `supersedes`/`superseded_by`. Never reuse retired IDs.

## Minimum requirement record

```json
{
  "id": "CLDC-001-REQ-0001",
  "family_id": "CLDC-001",
  "source_item_id": "CLDC-001-SRC-0001",
  "baseline_status": "solicitation",
  "source": {
    "document_sha256": "443c2ceaef75b5560dc310a22e584c3f4a964802d1095b6d29e9a589171df3e0",
    "page": 10,
    "section": "Initial Submission",
    "printed_path": null,
    "bbox": null,
    "verbatim_text": "The Draft IMS shall be due at proposal with the contents below."
  },
  "atomic_text": "The Draft IMS shall be due at proposal.",
  "actor": "contractor",
  "modality": "shall",
  "classification": "mandatory",
  "countable": true,
  "review_status": "candidate",
  "applicability": null,
  "links": []
}
```

`source.verbatim_text` is authoritative for the extraction. `atomic_text`, classifications, interpretations, and links are reviewable analysis and must remain distinguishable from source language.

Useful link types may eventually include `derived_from`, `allocated_to`, `implements`, `verifies`, `evidenced_by`, `depends_on`, `conflicts_with`, `duplicates`, and `supersedes`. Add only links backed by an actual use case.

## Counting policy

Use this default policy unless the project records a different decision in `manifest.json`:

- Count each independently verifiable mandatory obligation once.
- Treat `shall`, `must`, and unambiguous `required` constructions as mandatory.
- Treat imperatives and list children inherited from a mandatory lead-in as mandatory.
- Split a source item when it contains independently testable actions, objects, conditions, or due events.
- Preserve `should` as advisory and `may` as permission; do not include either in the mandatory headline count.
- Classify `will` by actor and context rather than assuming it is a provider obligation.
- Distinguish offeror, contractor/provider, Government/NASA, subcontractor, and shared actors.
- Record conditional applicability explicitly.
- Record incorporated documents and clauses as references; do not recursively count all external requirements as requirements in this PDF.
- Count repeated boilerplate as separate applicable instances, while also reporting deduplicated text patterns.
- Exclude quoted notice language from the obligation count when the independently countable obligation is to reproduce that notice.
- Retain every excluded candidate with an exclusion reason.
- Publish a mandatory count only for `review_status: "confirmed"`; report unresolved candidates separately.

## Docling baseline

Docling 2.85.0 was tested successfully against the full PDF with OCR disabled. The PDF already has a useful text layer.

Observed Docling output:

- DoclingDocument schema version 1.10.0
- 246 pages
- 6,199 text blocks
- 2,674 list items
- 1,013 groups
- 49 detected tables
- page number and bounding-box provenance on text items
- about 81 seconds runtime on the test machine

Docling preserved the DRD body structure well. It did **not** reconstruct the three unusually wide DRL tables on pages 7-9 into useful rows and columns; those tables collapsed and require the PDF text layer or a focused parser.

Reproduce the intermediate conversion:

```bash
PDF='/Users/chris/Downloads/03_CLDC+Integrated+DRD+July+2026.pdf'
mkdir -p tmp/docling
docling "$PDF" \
  --from pdf \
  --to json \
  --to md \
  --no-ocr \
  --tables \
  --table-mode accurate \
  --image-export-mode placeholder \
  --output tmp/docling \
  --abort-on-error \
  --num-threads 4
pdftotext -layout "$PDF" tmp/source-layout.txt
shasum -a 256 "$PDF"
```

Docling fields worth retaining include `orig`, `text`, `label`, `prov`, `bbox`, `marker`, `enumerated`, `parent`, and `self_ref`.

## Fresh-agent starting task

Start with deterministic source normalization, not semantic atomization:

1. Read this README and verify the source SHA-256 before processing.
2. Reproduce the Docling JSON and layout-text intermediates under `tmp/`.
3. Write the smallest practical `extract.py`, using the Python standard library to read Docling JSON.
4. Build `families.json` from the 60 top-level DRD headers plus the 38 official child IDs in DRL pages 7-9.
5. Normalize body items from general pages 2-6 and DRD pages 10-246 into `source-items.jsonl`.
6. Preserve all original fragments and provenance when joining page-break continuations. Record every repair in the output rather than changing text invisibly.
7. Map body headings CLDC-214.1 through CLDC-214.4 to official families CLDC-211.1 through CLDC-211.4 as a suspected alias, retaining the printed heading and an anomaly record.
8. Classify source items as explicit mandatory, inherited mandatory, advisory, permission, commitment, reference, descriptive, quoted, or unresolved.
9. Only then split confirmed source items into atomic requirements.
10. Write manifest counts and reconcile them against actual JSONL line counts.

The first runnable check should assert at least:

- 246 Docling pages;
- source SHA-256 matches the manifest;
- 60 top-level DRD headers;
- 98 official DRL identifiers;
- 14 grouping parents;
- 38 child DRDs;
- 84 leaf deliverables;
- all four CLDC-214.x body-heading anomalies are retained and mapped;
- every source item has a source page and family;
- every JSONL line parses independently.

Do not add a database, web application, ontology, or requirements-management integration during the first extraction. Add one only when a real consumer cannot use the versioned files.

## Questions this data should eventually answer

- How many confirmed mandatory obligations exist, and under which counting policy?
- How many are content, delivery, schedule, format, reporting, approval, process, interface, safety, security, records, or verification obligations?
- Which requirements specify outcomes versus implementation methods?
- Which obligations recur across DRDs, and how much recurring delivery effort do they imply?
- Which requirements depend on external standards, Government-furnished services, approvals, or future negotiation?
- Which statements are ambiguous, contradictory, duplicated, incomplete, or incorrectly numbered?
- Which design elements, risks, verification methods, evidence artifacts, and closure decisions trace to each requirement?
- What changes between solicitation, proposal, negotiated contract, modification, and approved provider baselines?

The objective is not merely a bigger list. It is a defensible chain from exact source language to interpretation, implementation, evidence, risk, and change history.
