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

Because this is a draft RFP published for industry feedback, every extracted record should carry `baseline_status: "draft_rfp"`. A future proposal, negotiation, final solicitation, contract award, modification, or approved provider document is a different baseline and must not silently overwrite this one.

One useful critique of the acquisition is:

> "It's got all the requirements, deliverables, and clauses of a cost-plus contract, but they are stuffed into a firm fixed-price bag."

Treat that as a hypothesis to test with data, not a conclusion to encode. The register should make it possible to measure outcome-oriented requirements versus prescribed processes, recurring reporting, approval gates, Government insight/control, incorporated obligations, and verification burden.

## Source document

Authoritative public source: [Commercial Low Earth Orbit (LEO) Destination Contract (CLDC) Draft Request for Proposal on SAM.gov](https://sam.gov/workspace/contract/opp/19a8a55c066441ef891e33bac770dd9d/view).

SAM.gov identifies the notice as `80JSC026R0021DRFP`, published July 6, 2026 by NASA Johnson Space Center. The notice is a Sources Sought posting for information, planning, and industry feedback; it explicitly states that it is not a request for proposals.

Observed source facts:

- Public attachment: `03_CLDC Integrated DRD July 2026.pdf`
- SAM.gov access classification: Public
- SAM.gov listed size: 2.25 MB
- PDF pages: 246
- PDF metadata creation/modification date: 2026-07-02
- SHA-256: `443c2ceaef75b5560dc310a22e584c3f4a964802d1095b6d29e9a589171df3e0`
- General provisions: pages 2-6
- Data Requirements List (DRL): pages 7-9
- DRD definitions: pages 10-246

Use the SAM.gov notice and attachment name as the public citation rather than a workstation path. The attachment is listed as Public, but whether to redistribute the PDF or a full-text derivative in this repository remains a separate project decision. Findings, hashes, locators, schemas, and extraction code can be published independently.

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

## Outputs

All of the following were produced by the completed first pass (2026-07-10). Create or regenerate them only via `extract.py`:

```text
data/manifest.json          source fingerprint, policy, tool versions, and counts
data/families.json          DRD hierarchy and metadata
data/source-items.jsonl     lossless, addressable source items
data/requirements.jsonl     reviewed atomic requirements
data/references.jsonl       deduplicated register of cited external documents
data/anomalies.jsonl        numbering, extraction, ambiguity, and conflict findings
extract.py                  minimal reproducible extraction/normalization script
site-build.py               builds docs/data/explorer.json from the registers
docs/                       static CLDC Explorer site, served by GitHub Pages
```

Generated Docling and layout files belong under `tmp/` and should not be committed.

## CLDC Explorer

`docs/` holds a static, single-page explorer over these registers, published with GitHub Pages:
<https://interplanetarychris.github.io/cldc-requirements/> (live once the repository is public and
Pages is enabled from the `main` branch `/docs` folder).

The theory: the authoritative artifact is a 246-page PDF, and today every audience re-reads it by
hand, with offerors, NASA, and the public each building a private index of the same text. The
explorer renders the extracted register in one shared interface instead. Every requirement is
searchable and filterable; every record links to its DRD family, its cited external documents, and
the exact source page; the treemap, recurrence, and reference views show at a glance what the
registers otherwise reveal only through queries. It also mocks what a more modern solicitation
could publish alongside the PDF: machine-readable response templates, an industry-day roster, an
assistance-provider registry, and agent-consumable formats (markdown mirrors, raw JSONL, an MCP
server).

The explorer is a citizen concept built from the public record, not an official NASA product. A
persistent banner on every page says so and links to the SAM.gov notice. Verbatim source language
remains the authority; everything else is reviewable analysis, and the machine-classified counting
caveats above apply to every figure shown.

The page fetches `docs/data/explorer.json` at load. Rebuild that payload after any extraction
change:

```bash
python3 site-build.py
```

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
  "baseline_status": "draft_rfp",
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
PDF="${PDF:?Set PDF to the downloaded '03_CLDC Integrated DRD July 2026.pdf'}"
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

## First-pass extraction results (2026-07-10)

The first pass described below is complete. `extract.py` (Python standard library only, reading the Docling JSON and `pdftotext -layout` intermediates) regenerates every output deterministically in about 4 seconds once `tmp/` exists:

```bash
python3 extract.py --pdf "/path/to/03_CLDC+Integrated+DRD+July+2026.pdf"
```

The script ends with a `validate()` pass that asserts every check in the runnable-check list below; a run that completes has passed all of them. Note the downloaded attachment filename contains literal `+` characters.

Headline counts, reconciled against actual JSONL line counts:

- 5,031 source items covering all 98 official identifiers plus `CLDC-GEN` (general provisions, pages 2-6).
- 2,995 mandatory atomic requirements under the default counting policy. This is a **machine-classified first pass**: `review_status: "confirmed"` here means "confirmed by mechanical application of the counting policy," not human review. Treat the headline number as a policy-derived candidate count until records are individually reviewed.
- 60 anomaly records: 41 page-break joins, 13 same-page fragment joins, 4 suspected CLDC-214.x → CLDC-211.x aliases (open), 1 CLDC-101 numbering anomaly (open), 1 ITAR/EAR counting exclusion (resolved by policy). These map exactly to the four known source anomalies above plus mechanical repairs; no new anomaly classes surfaced.

Source-item classification: 707 explicit mandatory, 2,169 inherited mandatory, 1,744 descriptive, 268 reference, 56 permission, 43 commitment, 39 advisory, 5 quoted.

Requirement breakdowns: actor — contractor 2,925, Government 33, shared 22, subcontractor 12, offeror 3; modality — inherited 2,064, `shall` 662, imperative 171, `required` 65, `must` 33. The nine families with zero requirements are all grouping parents whose content lives in their children.

The 268 reference-classified source items were subsequently deduplicated into `data/references.jsonl`: 104 register records covering 94 canonical documents plus 10 unresolved citations (title-only, URL-only, or fragmentary text without a formal identifier — retained verbatim, not dropped). Every reference instance reconciles into the register exactly once, and identifier/title/revision variants observed in the source (e.g. NASA-STD-8739.8 versus 8739.8B) are grouped under one canonical document with the variants recorded rather than silently merged.

## Fresh-agent starting task

The first pass below is **complete**; the instructions are retained verbatim so anyone can independently re-derive the outputs from the public PDF. Start with deterministic source normalization, not semantic atomization:

1. Read this README, obtain `03_CLDC Integrated DRD July 2026.pdf` from the linked SAM.gov notice, and verify its SHA-256 before processing.
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

First-pass answers from the current registers follow each question; unanswered items are future work.

**How many confirmed mandatory obligations exist, and under which counting policy?**

> **2,995**, under the default counting policy in this README, applied mechanically. Human review of individual records is still pending, so report it as a policy-derived count, not a settled baseline.

**How many are content, delivery, schedule, format, reporting, approval, process, interface, safety, security, records, or verification obligations?**

> Partially answerable today by DRD section: content (Contents/Scope) 1,994; format 330; schedule (Initial Submission + Submission Frequency) 248; maintenance/change 179; distribution 154; other 90. Finer semantic categories (approval, safety, interface, verification) are not yet classified.

**Which requirements specify outcomes versus implementation methods?**

> Not yet classified. The register preserves verbatim text, so this can be added as a review dimension without re-extraction.

**Which obligations recur across DRDs, and how much recurring delivery effort do they imply?**

> 226 distinct atomic texts recur, accounting for 888 requirement instances (~30% of the total). The heaviest boilerplate: the maintenance-by-resubmission clause (68 DRDs), NASA CO/COR distribution list entries (53 and 50), complete-reissue-with-change-log (39), clean-copy-plus-redline dual submittal (31), and contractor-format-per-DFCD (36). Recurring delivery effort is therefore dominated by per-DRD resubmission and distribution mechanics.

**Which requirements depend on external standards, Government-furnished services, approvals, or future negotiation?**

> 268 reference instances resolve to **94 unique external documents** in `data/references.jsonl` (plus 10 unresolved citations): 17 CLDP program documents, 17 NASA-STDs, 13 NPRs/NPDs, 3 JPRs, 13 FAR/NFS clauses, and 26 other identifiers (NIST, OMB, CFR, SAE, GAO, and similar), with 2 internal DRD cross-references. Citation weight is heavily concentrated in CLDP program documents: CLDP-REQ-1130 (Requirements and Standards for the CLDP) is incorporated from 30 DRD families, CLDP-STD-1150 (Operations Standards) from 22, CLDP-PLN-3017 (Utilization Integration Plan) from 17, CLDP-PLN-2000 (Certification Plan) from 15, and CLDP-PLN-2110 (Mission Integration Plan) from 11 — so the effective requirement load depends materially on documents outside this PDF. Most NASA-STDs are cited once each.

**Which statements are ambiguous, contradictory, duplicated, incomplete, or incorrectly numbered?**

> See `data/anomalies.jsonl`: 4 open suspected aliases (body headings CLDC-214.1-.4 versus official CLDC-211.1-.4), 1 open numbering anomaly (CLDC-101 Contents starting at item 19), 1 counting exclusion (modal language inside required ITAR/EAR notice text), and 54 documented extraction repairs. Textual duplication is quantified in the recurrence figures above.

**Which design elements, risks, verification methods, evidence artifacts, and closure decisions trace to each requirement?**

> Not yet. The `links` field exists on every record and is empty; populate it only when a real consumer needs a given link type.

**What changes between solicitation, proposal, negotiated contract, modification, and approved provider baselines?**

> Nothing to compare yet: only the `draft_rfp` baseline exists. The ID and `supersedes` rules above define how future baselines diff against it.

The objective is not merely a bigger list. It is a defensible chain from exact source language to interpretation, implementation, evidence, risk, and change history.
