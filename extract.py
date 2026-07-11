#!/usr/bin/env python3
"""Extract the July 2026 CLDC DRD register from Docling JSON."""

import argparse
import hashlib
import html
import json
import os
import platform
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

SHA256 = "443c2ceaef75b5560dc310a22e584c3f4a964802d1095b6d29e9a589171df3e0"
BASELINE = "draft_rfp"
SECTIONS = (
    "Initial Submission", "Submission Frequency", "Maintenance", "Applicable Documents",
    "Contents", "Scope", "Format", "Distribution", "Remarks",
)
CONTENT_SECTIONS = {"Initial Submission", "Submission Frequency", "Contents", "Format", "Distribution"}
MANDATORY = re.compile(
    r"\b(?:shall|must)\b|\b(?:is|are|be|being|was|were)\s+required\b|\brequired\s+to\b|"
    r"\bminimum\b[^.;:]{0,80}\brequired\b|\brequires?\s+(?:the\s+)?(?:contractor|provider|offeror)\s+to\b",
    re.I,
)
NOT_REQUIRED = re.compile(r"\b(?:is|are|be|being|was|were)\s+not\s+required\b", re.I)
ADVISORY = re.compile(r"\bshould\b|\brecommend(?:ed|ation)?\b", re.I)
PERMISSION = re.compile(r"\bmay\b", re.I)
COMMITMENT = re.compile(r"\bwill\b", re.I)
IMPERATIVE = re.compile(
    r"^(?:the contractor\s+)?(?:address|analyze|assess|capture|complete|conduct|contain|"
    r"define|deliver|describe|develop|document|ensure|establish|evaluate|identify|include|"
    r"incorporate|indicate|list|maintain|perform|prepare|provide|record|report|retain|submit|"
    r"summarize|track|update|use|verify)\b", re.I,
)
LEAD_IN = re.compile(
    r"(?:(?:\b(?:shall|must)\s+(?:include|be included|contain|address|provide|be provided|define|identify|describe|track|report|submit|deliver|be delivered)\b|"
    r"\band\s+(?:shall\s+)?(?:include|contain|address|provide|identify|describe|track|report|submit|deliver)\b).*|\b(?:shall|must)\s*):\s*$",
    re.I,
)
ALIAS = {f"CLDC-214.{n}": f"CLDC-211.{n}" for n in range(1, 5)}
REFERENCE_CATEGORIES = (
    "cldp_program", "nasa_std", "npr", "npd", "jpr", "jsc", "far", "nfs",
    "mil_std", "internal_drd", "other", "unresolved",
)
REFERENCE_PATTERNS = (
    ("cldp_program", "cldp", re.compile(r"\bCLD(?:P)?\s*-\s*(?:PLN|REQ|STD)\s*-\s*\d{4}\b", re.I)),
    ("nasa_std", "nasa_std", re.compile(r"\bNASA\s*-\s*STD\s*-\s*\d+(?:\.\d+)?[A-Z]?(?:\s+Vol\.\s*\d+)?\b", re.I)),
    ("npr", "directive", re.compile(r"\bNPR\b\)?\s+\d{4}\.\d+[A-Z]?\b", re.I)),
    ("npd", "directive", re.compile(r"\bNPD\b\)?\s+\d{4}\.\d+[A-Z]?\b", re.I)),
    ("jpr", "directive", re.compile(r"\bJPR\b\)?\s+\d{4}\.\d+[A-Z]?\b", re.I)),
    ("jsc", "jsc", re.compile(r"\bJSC\b\)?\s*-?\s*\d{5}\b", re.I)),
    ("far", "regulation", re.compile(r"\bFAR\b\)?\s+(?:Subpart\s+)?\d+(?:\.\d+)+(?:\s*-\s*\d+)?\b", re.I)),
    ("nfs", "regulation", re.compile(r"\bNFS\b\)?\s+\d+(?:\.\d+)+(?:\s*-\s*\d+)?\b", re.I)),
    ("mil_std", "mil_std", re.compile(r"\bMIL\s*-\s*STD\s*-\s*\d+\b", re.I)),
    ("internal_drd", "internal_drd", re.compile(r"\bDRD\s+CLDC\s*-\s*\d{3}(?:\.\d+)?\b", re.I)),
    ("other", "nasa_report", re.compile(r"\bNASA/(?:TP|TM)-\d{4}-\d+\b", re.I)),
    ("other", "nist", re.compile(r"\bNIST\s+SP\s+\d{3}-\d+\b", re.I)),
    ("other", "omb", re.compile(r"\bOMB\s+(?:Circular\s+A-\d+|Memorandum\s+M-\d{2}-\d{2})\b", re.I)),
    ("other", "fisma", re.compile(r"\bFISMA\s+\d{4}\b", re.I)),
    ("other", "sae_eia", re.compile(r"\bSAE\s*-\s*EIA\s*-\s*\d+(?:-\d+)?\b", re.I)),
    ("other", "sae_as", re.compile(r"\b(?:SAE\s*[- ]\s*)?AS\s*-?\s*\d{4,5}\b", re.I)),
    ("other", "center_directive", re.compile(r"\b(?:NAII|JAII|JWI)\s+\d{4}\.\d+\b", re.I)),
    ("other", "ssp", re.compile(r"\bSSP\b\)?\s+\d{5}\b", re.I)),
    ("other", "pmod", re.compile(r"\bPMOD\s*-\s*PIDD\s*-\s*\d+\b", re.I)),
    ("other", "ck_wi", re.compile(r"\bCK\s*-\s*WI\s*-\s*\d+\b", re.I)),
    ("other", "cfr", re.compile(r"\bCFR\b\)?\s+Title\s+\d+\s+Parts?\s+\d+\s+and\s+\d+\b", re.I)),
)


def compact(text):
    return re.sub(r"\s+", " ", text or "").strip()


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tool_version(command):
    try:
        output = subprocess.run(command, capture_output=True, text=True, check=True).stdout
        return compact(output.splitlines()[0])
    except (OSError, subprocess.CalledProcessError, IndexError):
        return "unavailable"


def parse_families(markdown, layout):
    rows = []
    drl_page = 6
    pattern = re.compile(
        r"(CLDC-\d{3}(?:\.\d+)?)\s+(.*?)\s+(1/3|2/3|1|2|3)\s+CDO\b"
    )
    for line in markdown.splitlines():
        if not line.startswith("| DRD #"):
            continue
        drl_page += 1
        for family_id, title, data_type in pattern.findall(line):
            rows.append({
                "id": family_id,
                "title": compact(html.unescape(title)),
                "data_type": data_type,
                "opr": "CDO",
                "drl_page": drl_page,
            })

    children = defaultdict(list)
    for row in rows:
        if "." in row["id"]:
            children[row["id"].rsplit(".", 1)[0]].append(row["id"])

    pages = layout.split("\f")
    header_pages = {}
    for page_number, page in enumerate(pages, 1):
        match = re.search(r"DRD No\.:\s*(CLDC-\d{3})\b", page)
        if match:
            header_pages[match.group(1)] = page_number

    families = [{
        "id": "CLDC-GEN",
        "title": "General provisions",
        "baseline_status": BASELINE,
        "kind": "general",
        "parent_id": None,
        "child_ids": [],
        "is_grouping_parent": False,
        "is_leaf_deliverable": False,
        "source_pages": [2, 3, 4, 5, 6],
    }]
    for row in rows:
        family_id = row["id"]
        parent_id = family_id.rsplit(".", 1)[0] if "." in family_id else None
        families.append({
            **row,
            "baseline_status": BASELINE,
            "kind": "child" if parent_id else "top_level",
            "parent_id": parent_id,
            "child_ids": children.get(family_id, []),
            "is_grouping_parent": bool(children.get(family_id)),
            "is_leaf_deliverable": bool(parent_id) or not children.get(family_id),
            "body_start_page": header_pages.get(family_id) if not parent_id else None,
        })
    return families, header_pages


def bbox_of(item):
    prov = item.get("prov") or []
    return prov[0].get("bbox") if prov else None


def raw_items(doc):
    items = []
    for order, item in enumerate(doc["texts"]):
        prov = item.get("prov") or []
        if not prov:
            continue
        page = prov[0]["page_no"]
        if page not in range(2, 7) and page not in range(10, 247):
            continue
        if item.get("label") in {"page_header", "page_footer"}:
            continue
        text = item.get("orig") or item.get("text") or ""
        if not compact(text):
            continue
        bbox = bbox_of(item)
        items.append({
            "kind": "text",
            "docling_ref": item.get("self_ref"),
            "parent_ref": (item.get("parent") or {}).get("$ref"),
            "label": item.get("label"),
            "text": compact(text),
            "marker": item.get("marker") or "",
            "page": page,
            "pages": [page],
            "bboxes": [{"page": page, "bbox": bbox}],
            "fragments": [{"ref": item.get("self_ref"), "page": page, "text": text, "bbox": bbox}],
            "top": (bbox or {}).get("t", 0),
            "left": (bbox or {}).get("l", 0),
            "order": order,
            "repairs": [],
        })

    for table_order, table in enumerate(doc["tables"]):
        prov = table.get("prov") or []
        if not prov:
            continue
        page = prov[0]["page_no"]
        if page < 10 or page > 246:
            continue
        bbox = bbox_of(table)
        for row_number, row in enumerate(table.get("data", {}).get("grid", []), 1):
            cells = []
            for cell in row:
                value = compact(cell.get("text"))
                if value and (not cells or value != cells[-1]):
                    cells.append(value)
            if not cells:
                continue
            text = " | ".join(cells)
            items.append({
                "kind": "table_row",
                "docling_ref": table.get("self_ref"),
                "parent_ref": table.get("self_ref"),
                "label": "table_row",
                "text": text,
                "marker": str(row_number),
                "page": page,
                "pages": [page],
                "bboxes": [{"page": page, "bbox": bbox}],
                "fragments": [{"ref": table.get("self_ref"), "page": page, "row": row_number, "cells": cells, "text": text, "bbox": bbox}],
                "top": (bbox or {}).get("t", 0) - row_number / 1000,
                "left": (bbox or {}).get("l", 0),
                "order": len(doc["texts"]) + table_order,
                "repairs": [],
            })
    return sorted(items, key=lambda item: (item["page"], -item["top"], item["left"], item["order"]))


def section_in(text, label):
    for section in SECTIONS:
        if re.search(rf"\b{re.escape(section)}\s*:", text, re.I):
            return section
    if label == "section_header":
        if re.search(r"International Traffic in Arms Regulations.*Notice", text, re.I):
            return "ITAR Notice"
        if re.search(r"Export Administration Regulations.*Notice", text, re.I):
            return "EAR Notice"
        if re.match(r"^\d+(?:\.\d+)*\s+\S", text):
            return text
    return None


def assign_context(items, families, header_pages):
    family_by_id = {family["id"]: family for family in families}
    top_by_page = {page: family_id for family_id, page in header_pages.items()}
    current_family = "CLDC-GEN"
    current_top = "CLDC-GEN"
    current_section = "General provisions"
    previous_page = None
    for item in items:
        if item["page"] != previous_page and item["page"] in top_by_page:
            current_top = current_family = top_by_page[item["page"]]
            current_section = "DRD metadata"
        previous_page = item["page"]

        heading = re.match(r"^\s*(?:[·•-]\s*)?(?:DRD\s+)?(CLDC-\d{3}\.\d+)\b", item["text"], re.I)
        if heading:
            printed = heading.group(1).upper()
            official = ALIAS.get(printed, printed)
            family = family_by_id.get(official)
            if family and family.get("parent_id") == current_top:
                current_family = official
                current_section = family["title"]
                item["printed_family_heading"] = printed

        found_section = section_in(item["text"], item["label"])
        if found_section:
            current_section = found_section
        item["family_id"] = current_family
        item["section"] = current_section


def join_page_breaks(items):
    joined = []
    for item in items:
        if not joined:
            joined.append(item)
            continue
        previous = joined[-1]
        same_context = item["family_id"] == previous["family_id"] and item["section"] == previous["section"]
        previous_bbox = previous["bboxes"][-1]["bbox"] or {}
        item_bbox = item["bboxes"][0]["bbox"] or {}
        isolated_marker = (
            item["page"] == previous["pages"][-1]
            and same_context
            and re.fullmatch(r"(?:\d+|[a-z])\.", previous["text"], re.I)
            and abs(previous_bbox.get("t", 0) - item_bbox.get("t", 1)) < 1
        )
        same_page_continuation = (
            item["page"] == previous["pages"][-1]
            and same_context
            and not item["marker"]
            and not re.match(r"^(?:[·•▪*-]|o\s)", item["text"], re.I)
            and (
                (item["label"] == previous["label"] and item["text"][:1].islower())
                or re.search(r"\b(?:and|or|of|the|to|with|including)\s*$", previous["text"], re.I)
            )
            and not re.search(r"[.!?:;]\s*$", previous["text"])
        )
        page_break_continuation = (
            item["page"] == previous["pages"][-1] + 1
            and same_context
            and item["label"] not in {"section_header", "title"}
            and not item["marker"]
            and (
                (item["label"] == previous["label"] == "list_item")
                or (item["text"][:1].islower() and not re.search(r"[.!?:;]\s*$", previous["text"]))
            )
        )
        if not (isolated_marker or same_page_continuation or page_break_continuation):
            joined.append(item)
            continue
        repair = {
            "type": "page_break_join" if page_break_continuation else "same_page_fragment_join",
            "from_pages": sorted(set([previous["pages"][-1], item["page"]])),
            "joined_refs": [previous["fragments"][-1].get("ref"), item["fragments"][0].get("ref")],
            "reason": "unmarked continuation at the top of the following page" if page_break_continuation else "extractor split one printed item into adjacent fragments",
        }
        if isolated_marker:
            previous["marker"] = previous["text"]
        previous["text"] = compact(previous["text"] + " " + item["text"])
        previous["pages"].extend(p for p in item["pages"] if p not in previous["pages"])
        previous["bboxes"].extend(item["bboxes"])
        previous["fragments"].extend(item["fragments"])
        previous["repairs"].append(repair)
    return joined


def is_reference(text, section):
    return section == "Applicable Documents" or bool(re.match(
        r"^(?:[·•-]\s*)?(?:reference\b|(?:CLDP|NPR|NPD|NASA-STD|MIL-STD|ISO|SAE|ANSI|ASME|IEEE)-?[A-Z0-9])",
        text, re.I,
    ))


def is_imperative_clause(text):
    text = re.sub(r"^\s*(?:[·•▪*-]\s*)?(?:(?:\d+|[a-z]|[ivxlcdm]+)[.)]\s*)?", "", text, flags=re.I)
    text = re.sub(r"^(?:If|When|Where|Unless)\b[^,;]*[,;]\s*", "", text, flags=re.I)
    return bool(IMPERATIVE.match(text))


def has_imperative(text):
    return any(is_imperative_clause(part) for part in re.split(r"(?<=[.!?])\s+", compact(text)))


def classify(items):
    active_lead = {}
    previous_family_section = None
    for item in items:
        text = item["text"]
        key = (item["family_id"], item["section"])
        if key != previous_family_section:
            previous_family_section = key
        quoted = item["section"] in {"ITAR Notice", "EAR Notice"} and not re.search(
            r"data delivered.*shall contain", text, re.I
        )
        negative_required = bool(NOT_REQUIRED.search(text) and not re.search(r"\b(?:shall|must)\b", text, re.I) and not has_imperative(text))
        explicit = bool(MANDATORY.search(text) or has_imperative(text)) and not negative_required
        inherited = (
            item["section"] in CONTENT_SECTIONS
            or (item["label"] in {"list_item", "table_row"} and key in active_lead)
        )
        section_tail = None
        for section in SECTIONS:
            match = re.match(rf"^\s*(?:\d+[.)]?\s*)?{re.escape(section)}\s*:\s*(.*)$", text, re.I)
            if match:
                section_tail = compact(match.group(1))
                break
        normalized_empty = compact(text).rstrip(".").upper()
        empty_or_na = (
            section_tail is not None and section_tail.rstrip(".").upper() in {"", "N/A", "NONE", "NOT APPLICABLE"}
        ) or normalized_empty in {"N/A", "NONE", "NOT APPLICABLE"}
        government_will = bool(re.search(r"\b(?:NASA|Government|Contracting Officer|COR)\b[^.;]*\bwill\b", text, re.I))
        if quoted:
            classification = "quoted"
        elif negative_required:
            classification = "descriptive"
        elif explicit:
            classification = "explicit_mandatory"
        elif empty_or_na or item["label"] == "section_header" or re.match(r"^\*+\s", text):
            classification = "descriptive"
        elif is_reference(text, item["section"]):
            classification = "reference"
        elif ADVISORY.search(text):
            classification = "advisory"
        elif PERMISSION.search(text):
            classification = "permission"
        elif government_will:
            classification = "commitment"
        elif inherited and compact(text).upper() not in {"N/A", "NONE"}:
            classification = "inherited_mandatory"
        elif COMMITMENT.search(text):
            classification = "commitment"
        else:
            classification = "descriptive"

        lead = (
            bool(LEAD_IN.search(text))
            or bool(re.search(r"\bminimum\b[^:]{0,160}\brequired\b[^:]*:\s*$", text, re.I))
            or (classification == "inherited_mandatory" and text.rstrip().endswith(":"))
        ) and not re.search(r"(?:ITAR|EAR) Notice", text, re.I)
        if lead:
            active_lead[key] = True
        independently_countable = bool(lead_prefixes(text)) if lead else True
        item["classification"] = classification
        item["lead_in"] = lead
        item["countable"] = classification in {"explicit_mandatory", "inherited_mandatory"} and (not lead or independently_countable)
        item["review_status"] = "confirmed"
        item["exclusion_reason"] = None if item["countable"] else (
            "mandatory_lead_in_counted_through_children" if lead else classification
        )


def source_records(items, document_hash):
    counters = Counter()
    records = []
    for item in items:
        family_id = item["family_id"]
        counters[family_id] += 1
        source_id = f"{family_id}-SRC-{counters[family_id]:04d}"
        item["source_item_id"] = source_id
        printed = item["marker"] or None
        records.append({
            "id": source_id,
            "family_id": family_id,
            "baseline_status": BASELINE,
            "source": {
                "document_sha256": document_hash,
                "page": item["page"],
                "pages": item["pages"],
                "section": item["section"],
                "printed_path": printed,
                "bbox": item["bboxes"][0]["bbox"],
                "bboxes": item["bboxes"],
                "verbatim_text": item["text"],
                "fragments": item["fragments"],
                "docling_ref": item["docling_ref"],
            },
            "source_kind": item["kind"],
            "docling_label": item["label"],
            "classification": item["classification"],
            "countable": item["countable"],
            "review_status": item["review_status"],
            "exclusion_reason": item["exclusion_reason"],
            "repairs": item["repairs"],
            "lead_in": item["lead_in"],
            **({"printed_family_heading": item["printed_family_heading"]} if item.get("printed_family_heading") else {}),
        })
    return records


def parse_reference(text):
    candidates = []
    for category, kind, pattern in REFERENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            candidates.append((match.start(), category, kind, match))
    if not candidates:
        return None

    _, category, kind, match = min(candidates, key=lambda candidate: candidate[0])
    observed = compact(match.group()).replace(")", "")
    revision = None
    notes = []
    if kind == "cldp":
        parsed = re.search(r"CLD(P)?\s*-\s*(PLN|REQ|STD)\s*-\s*(\d{4})", observed, re.I)
        canonical = f"CLDP-{parsed.group(2).upper()}-{parsed.group(3)}"
        if not parsed.group(1):
            notes.append("CLD prefix grouped with the CLDP base identifier; observed source form retained")
    elif kind == "nasa_std":
        parsed = re.search(r"STD\s*-\s*(\d+(?:\.\d+)?)([A-Z]?)(?:\s+Vol\.\s*(\d+))?", observed, re.I)
        canonical = f"NASA-STD-{parsed.group(1)}"
        revision = parsed.group(2).upper() or None
        volume = parsed.group(3) or ("2" if re.search(r"\bVolume\s+2\b", text, re.I) else None)
        if volume:
            canonical += f" VOL. {volume}"
    elif kind == "directive":
        parsed = re.search(r"(NPR|NPD|JPR)\b\s+(\d{4}\.\d+)([A-Z]?)", observed, re.I)
        canonical = f"{parsed.group(1).upper()} {parsed.group(2)}"
        revision = parsed.group(3).upper() or None
    elif kind == "jsc":
        canonical = f"JSC-{re.search(r'\d{5}', observed).group()}"
    elif kind == "regulation":
        number = re.search(r"\d+(?:\.\d+)+(?:\s*-\s*\d+)?", observed).group()
        canonical = f"{category.upper()} {re.sub(r'\s*-\s*', '-', number)}"
    elif kind == "mil_std":
        canonical = f"MIL-STD-{re.search(r'\d+', observed).group()}"
    elif kind == "internal_drd":
        number = re.search(r"CLDC\s*-\s*(\d{3}(?:\.\d+)?)", observed, re.I).group(1)
        canonical = f"CLDC-{number}"
    elif kind == "nasa_report":
        canonical = observed.upper()
    elif kind == "nist":
        number = re.search(r"\d{3}-\d+", observed).group()
        canonical = f"NIST SP {number}"
    elif kind == "omb":
        canonical = re.sub(r"\s+", " ", observed)
    elif kind == "fisma":
        canonical = observed.upper()
    elif kind == "sae_eia":
        canonical = re.sub(r"\s*-\s*", "-", observed.upper())
    elif kind == "sae_as":
        canonical = f"SAE AS{re.search(r'\d{4,5}', observed).group()}"
    elif kind == "center_directive":
        parsed = re.search(r"(NAII|JAII|JWI)\s+(\d{4}\.\d+)", observed, re.I)
        canonical = f"{parsed.group(1).upper()} {parsed.group(2)}"
    elif kind == "ssp":
        canonical = f"SSP {re.search(r'\d{5}', observed).group()}"
    elif kind == "pmod":
        canonical = re.sub(r"\s*-\s*", "-", observed.upper())
    elif kind == "ck_wi":
        canonical = re.sub(r"\s*-\s*", "-", observed.upper())
    else:
        numbers = re.search(r"Title\s+(\d+)\s+Parts?\s+(\d+)\s+and\s+(\d+)", observed, re.I)
        canonical = f"CFR Title {numbers.group(1)} Parts {numbers.group(2)} and {numbers.group(3)}"

    parts = [compact(part) for part in text.split("|")]
    title = parts[1] if len(parts) >= 2 else compact(text[match.end():].lstrip(" ,.-|"))
    if text.startswith("(Note:"):
        title = None
    identifier_variants = [observed]
    revisions = [revision] if revision else []
    if len(parts) >= 3 and parts[2]:
        if re.search(r"\bCLD(?:P)?\s*-\s*(?:PLN|REQ|STD)\s*-", parts[2], re.I):
            identifier_variants.append(parts[2])
        else:
            revisions.append(parts[2])
    if revision:
        notes.append("revision suffix excluded from the canonical base identifier; observed source form retained")
    return {
        "canonical_identifier": canonical,
        "category": category,
        "title_variant": title or None,
        "identifier_variants": identifier_variants,
        "revision_variants": revisions,
        "grouping_notes": notes,
    }


def reference_records(sources):
    groups = {}
    for source in sources:
        if source["classification"] != "reference":
            continue
        text = source["source"]["verbatim_text"]
        parsed = parse_reference(text)
        key = (parsed["category"], parsed["canonical_identifier"]) if parsed else ("unresolved", text)
        group = groups.setdefault(key, {
            "canonical_identifier": parsed["canonical_identifier"] if parsed else None,
            "category": parsed["category"] if parsed else "unresolved",
            "title_variants": set(),
            "identifier_variants": set(),
            "revision_variants": set(),
            "verbatim_texts": set(),
            "family_ids": set(),
            "source_item_ids": [],
            "grouping_notes": set(),
        })
        if parsed:
            if parsed["title_variant"]:
                group["title_variants"].add(parsed["title_variant"])
            group["identifier_variants"].update(parsed["identifier_variants"])
            group["revision_variants"].update(parsed["revision_variants"])
            group["grouping_notes"].update(parsed["grouping_notes"])
        group["verbatim_texts"].add(text)
        group["family_ids"].add(source["family_id"])
        group["source_item_ids"].append(source["id"])

    order = {category: index for index, category in enumerate(REFERENCE_CATEGORIES)}
    records = []
    for (category, key), group in sorted(groups.items(), key=lambda item: (order[item[0][0]], item[0][1])):
        if category == "unresolved":
            suffix = "UNRESOLVED-" + hashlib.sha256(key.encode()).hexdigest()[:12].upper()
        else:
            suffix = re.sub(r"[^A-Z0-9]+", "-", key.upper()).strip("-")
        record = {
            "id": f"CLDC-REF-{suffix}",
            "baseline_status": BASELINE,
            "canonical_identifier": group["canonical_identifier"],
            "category": category,
            "title_variants": sorted(group["title_variants"]),
            "identifier_variants": sorted(group["identifier_variants"]),
            "revision_variants": sorted(group["revision_variants"]),
            "verbatim_texts": sorted(group["verbatim_texts"]),
            "instance_count": len(group["source_item_ids"]),
            "family_ids": sorted(group["family_ids"]),
            "source_item_ids": sorted(group["source_item_ids"]),
        }
        if group["grouping_notes"]:
            record["grouping_notes"] = sorted(group["grouping_notes"])
        if category == "unresolved":
            record["unresolved_reason"] = "no parseable document identifier in verbatim source text"
        records.append(record)
    return records


def sentences(text):
    protected = compact(text)
    protected = re.sub(r"^(\s*(?:[·•▪*-]\s*)?(?:\d+|[a-z]|[ivxlcdm]+))\.(\s+)", r"\1<DOT>\2", protected, flags=re.I)
    protected = re.sub(r"\b(?:U\.\s*S|e\.g|i\.e|No|Dr|Mr|Ms|Fig|etc|vs)\.", lambda m: m.group(0).replace(".", "<DOT>"), protected, flags=re.I)
    protected = re.sub(r"(?<=[A-Za-z])\.(?=\d)", "<DOT>", protected)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", protected)
    output = []
    for part in parts:
        clauses = re.split(r";\s+(?=(?:The|Contractor|NASA|Government|All|Each|Any|This|These|Such)\b)", part)
        output.extend(compact(clause.replace("<DOT>", ".")) for clause in clauses if compact(clause))
    return output


def lead_prefixes(text):
    parts = sentences(text)
    if not parts:
        return []
    prefixes = [part for part in parts[:-1] if MANDATORY.search(part) or is_imperative_clause(part)]
    final = parts[-1]
    split = re.split(
        r"\s+and\s+(?:(?:the\s+\w+|it)\s+)?(?:shall\s+)?(?=(?:include|contain|address|provide|identify|describe)\b)",
        final,
        maxsplit=1,
        flags=re.I,
    )
    if len(split) == 2 and (MANDATORY.search(split[0]) or is_imperative_clause(split[0])):
        prefixes.append(compact(split[0]) + ".")
    return prefixes


def actor_for(text, inherited=False):
    if inherited:
        return "contractor"
    lower = text.lower()
    modal = re.search(r"\b(?:shall|must|required)\b", lower)
    subject = lower[:modal.start()] if modal else lower[:120]
    contractor = bool(re.search(r"\b(?:contractor|provider)\b", subject))
    government = bool(re.search(r"\b(?:nasa|government|contracting officer|cor)\b", subject))
    if contractor and government:
        return "shared"
    if "subcontractor" in subject:
        return "subcontractor"
    if "offeror" in subject:
        return "offeror"
    if government:
        return "government"
    return "contractor"


def modality_for(text, inherited=False):
    lower = text.lower()
    if "shall" in lower:
        return "shall"
    if "must" in lower:
        return "must"
    if MANDATORY.search(text) and "required" in lower:
        return "required"
    return "inherited" if inherited else "imperative"


def applicability_for(text):
    match = re.match(r"^((?:If|When|Where|Unless|For)\b[^,.;]*[,;])", text, re.I)
    return match.group(1) if match else None


def requirement_records(sources, family_by_id):
    counters = Counter()
    requirements = []
    for source in sources:
        if not source["countable"]:
            continue
        inherited = source["classification"] == "inherited_mandatory"
        if source.get("lead_in"):
            candidates = lead_prefixes(source["source"]["verbatim_text"])
        else:
            candidates = sentences(source["source"]["verbatim_text"])
        if not inherited and not source.get("lead_in"):
            candidates = [
                part for part in candidates
                if (MANDATORY.search(part) or is_imperative_clause(part)) and not LEAD_IN.search(part)
            ]
        if not candidates:
            candidates = [source["source"]["verbatim_text"]]
        for atomic_text in candidates:
            family_id = source["family_id"]
            counters[family_id] += 1
            requirements.append({
                "id": f"{family_id}-REQ-{counters[family_id]:04d}",
                "family_id": family_id,
                "source_item_id": source["id"],
                "baseline_status": BASELINE,
                "source": {
                    "document_sha256": source["source"]["document_sha256"],
                    "page": source["source"]["page"],
                    "section": source["source"]["section"],
                    "printed_path": source["source"]["printed_path"],
                    "bbox": source["source"]["bbox"],
                    "verbatim_text": source["source"]["verbatim_text"],
                },
                "atomic_text": atomic_text,
                "actor": actor_for(atomic_text, inherited),
                "modality": modality_for(atomic_text, inherited),
                "classification": "mandatory",
                "countable": True,
                "review_status": "confirmed",
                "applicability": applicability_for(atomic_text),
                "links": [],
                **({"inheritance": {"basis": "mandatory DRD content/delivery context", "deliverable": family_by_id[family_id]["title"]}} if inherited else {}),
            })
    return requirements


def anomaly_records(items, sources):
    source_by_id = {source["id"]: source for source in sources}
    anomalies = []
    for item in items:
        source_id = item["source_item_id"]
        for repair in item["repairs"]:
            anomalies.append({
                "id": f"ANOM-REPAIR-{len(anomalies) + 1:04d}",
                "type": "extraction_repair",
                "status": "repaired",
                "family_id": item["family_id"],
                "source_item_id": source_id,
                "page": item["page"],
                "details": repair,
            })
        printed = item.get("printed_family_heading")
        if printed in ALIAS:
            anomalies.append({
                "id": f"ANOM-ALIAS-{printed.rsplit('.', 1)[1]}",
                "type": "suspected_alias",
                "status": "open",
                "family_id": ALIAS[printed],
                "source_item_id": source_id,
                "page": item["page"],
                "printed_identifier": printed,
                "official_identifier": ALIAS[printed],
                "verbatim_text": source_by_id[source_id]["source"]["verbatim_text"],
                "details": "DRL/header use CLDC-211.x; body heading prints CLDC-214.x.",
            })
    anomalies.extend([
        {
            "id": "ANOM-NUMBERING-CLDC-101",
            "type": "numbering",
            "status": "open",
            "family_id": "CLDC-101",
            "details": "Contents numbering begins at item 19, apparently continuing the preceding DRD.",
        },
        {
            "id": "ANOM-QUOTED-NOTICES",
            "type": "counting_exclusion",
            "status": "resolved_by_policy",
            "family_id": "CLDC-GEN",
            "details": "Modal language inside required ITAR/EAR notice text is classified quoted and excluded; the obligations to include the notices remain countable.",
        },
    ])
    return anomalies


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def write_jsonl(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n")


def parse_jsonl(path):
    with path.open() as stream:
        return [json.loads(line) for line in stream if line.strip()]


def validate(doc, document_hash, families, header_pages, sources, requirements, references, anomalies, manifest):
    official = [family for family in families if family["id"] != "CLDC-GEN"]
    top = [family for family in official if family["kind"] == "top_level"]
    children = [family for family in official if family["kind"] == "child"]
    parents = [family for family in top if family["is_grouping_parent"]]
    leaves = [family for family in official if family["is_leaf_deliverable"]]
    assert len(doc["pages"]) == 246
    assert document_hash == SHA256 == manifest["source"]["sha256"]
    assert len(header_pages) == len(top) == 60
    assert len(official) == 98
    assert len(parents) == 14
    assert len(children) == 38
    assert len(leaves) == 84
    assert len([a for a in anomalies if a["type"] == "suspected_alias"]) == 4
    assert all(source["source"]["page"] and source["family_id"] for source in sources)
    assert len(sources) == manifest["counts"]["source_items"]
    assert len(requirements) == manifest["counts"]["confirmed_mandatory_requirements"]
    assert all(requirement["source_item_id"] for requirement in requirements)
    assert {family["id"] for family in official} <= {source["family_id"] for source in sources}
    source_ids = {source["id"] for source in sources}
    assert all(requirement["source_item_id"] in source_ids for requirement in requirements)
    assert {source["id"] for source in sources if source["countable"]} <= {requirement["source_item_id"] for requirement in requirements}
    reference_sources = {source["id"] for source in sources if source["classification"] == "reference"}
    registered_sources = [source_id for reference in references for source_id in reference["source_item_ids"]]
    assert len(reference_sources) == manifest["counts"]["reference_instances"] == 268
    assert len(registered_sources) == len(set(registered_sources)) == sum(reference["instance_count"] for reference in references) == 268
    assert set(registered_sources) == reference_sources
    assert len(references) == manifest["counts"]["reference_register_records"]
    assert sum(reference["category"] != "unresolved" for reference in references) == manifest["counts"]["unique_external_documents"]
    assert len({reference["id"] for reference in references}) == len(references)
    assert all(reference["baseline_status"] == BASELINE for reference in references)
    assert all(
        (reference["canonical_identifier"] is None and reference.get("unresolved_reason"))
        if reference["category"] == "unresolved" else reference["canonical_identifier"]
        for reference in references
    )
    assert sum(
        reference["instance_count"] for reference in references if reference["category"] == "unresolved"
    ) == manifest["counts"]["unresolved_reference_items"]
    expected_text_refs = {
        item["self_ref"] for item in doc["texts"]
        if item.get("prov")
        and (item["prov"][0]["page_no"] in range(2, 7) or item["prov"][0]["page_no"] in range(10, 247))
        and item.get("label") not in {"page_header", "page_footer"}
        and compact(item.get("orig") or item.get("text"))
    }
    actual_text_refs = {
        fragment.get("ref") for source in sources for fragment in source["source"]["fragments"]
        if str(fragment.get("ref", "")).startswith("#/texts/")
    }
    assert expected_text_refs == actual_text_refs
    expected_table_rows = sum(
        bool([cell for cell in row if compact(cell.get("text"))])
        for table in doc["tables"] if table.get("prov") and table["prov"][0]["page_no"] in range(10, 247)
        for row in table.get("data", {}).get("grid", [])
    )
    actual_table_rows = sum("row" in fragment for source in sources for fragment in source["source"]["fragments"])
    assert expected_table_rows == actual_table_rows
    assert manifest["counts"]["lexical_occurrences"] == {
        "shall": 736, "must": 37, "required": 192, "should": 78, "may": 107, "will": 248,
    }
    assert any(
        source["family_id"] == "CLDC-001" and source["source"]["pages"] == [11, 12]
        and "tertiary critical paths" in source["source"]["verbatim_text"]
        for source in sources
    )
    for filename, expected in (
        ("source-items.jsonl", len(sources)),
        ("requirements.jsonl", len(requirements)),
        ("references.jsonl", len(references)),
        ("anomalies.jsonl", len(anomalies)),
    ):
        assert len(parse_jsonl(Path("data") / filename)) == expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", default=os.environ.get("PDF"), help="authoritative CLDC PDF (or set PDF)")
    parser.add_argument("--docling-json", default="tmp/docling/03_CLDC+Integrated+DRD+July+2026.json")
    parser.add_argument("--docling-md", default="tmp/docling/03_CLDC+Integrated+DRD+July+2026.md")
    parser.add_argument("--layout", default="tmp/source-layout.txt")
    args = parser.parse_args()
    if not args.pdf:
        parser.error("--pdf or PDF is required")

    pdf = Path(args.pdf)
    doc = json.loads(Path(args.docling_json).read_text())
    markdown = Path(args.docling_md).read_text()
    layout = Path(args.layout).read_text()
    document_hash = sha256(pdf)
    families, header_pages = parse_families(markdown, layout)
    family_by_id = {family["id"]: family for family in families}

    items = raw_items(doc)
    assign_context(items, families, header_pages)
    items = join_page_breaks(items)
    classify(items)
    sources = source_records(items, document_hash)
    requirements = requirement_records(sources, family_by_id)
    references = reference_records(sources)
    anomalies = anomaly_records(items, sources)

    lexical = {word: len(re.findall(rf"\b{word}\b", layout, re.I)) for word in ("shall", "must", "required", "should", "may", "will")}
    normalized_requirements = Counter(compact(req["atomic_text"]).lower() for req in requirements)
    manifest = {
        "schema_version": "1.0",
        "baseline_status": BASELINE,
        "source": {
            "public_notice": "80JSC026R0021DRFP",
            "attachment": "03_CLDC Integrated DRD July 2026.pdf",
            "sha256": document_hash,
            "pages": len(doc["pages"]),
            "pdf_bytes": pdf.stat().st_size,
        },
        "policy": {
            "canonical_format": "JSONL",
            "source_item_scope": "general pages 2-6 and DRD pages 10-246",
            "mandatory_modalities": ["shall", "must", "unambiguous required", "imperative", "inherited mandatory list/content"],
            "nonmandatory_modalities": ["should", "may", "will unless context establishes an obligation"],
            "external_documents": "references only; requirements not recursively imported",
            "reference_register": "group by normalized base identifier; retain all observed identifier, revision, title, and verbatim variants; retain unidentified items with reasons",
            "quoted_notices": "count the reproduce-notice obligation; exclude modal language inside the notice",
            "repeated_boilerplate": "count each applicable instance and report duplicate text patterns",
            "headline_count_filter": {"classification": "mandatory", "review_status": "confirmed", "countable": True},
        },
        "tool_versions": {
            "python": platform.python_version(),
            "docling": tool_version(["docling", "--version"]),
            "docling_document_schema": doc.get("version"),
            "extractor": "extract.py schema 1.0",
        },
        "counts": {
            "docling_text_blocks": len(doc["texts"]),
            "docling_list_items": sum(item.get("label") == "list_item" for item in doc["texts"]),
            "docling_groups": len(doc["groups"]),
            "docling_tables": len(doc["tables"]),
            "top_level_drd_families": 60,
            "official_drl_identifiers": 98,
            "grouping_parents": 14,
            "child_drds": 38,
            "leaf_deliverables": 84,
            "source_items": len(sources),
            "source_items_by_classification": dict(sorted(Counter(source["classification"] for source in sources).items())),
            "reference_instances": sum(reference["instance_count"] for reference in references),
            "reference_register_records": len(references),
            "unique_external_documents": sum(reference["category"] != "unresolved" for reference in references),
            "unique_external_documents_by_category": {
                category: sum(reference["category"] == category for reference in references)
                for category in REFERENCE_CATEGORIES
                if category != "unresolved" and any(reference["category"] == category for reference in references)
            },
            "unresolved_reference_records": sum(reference["category"] == "unresolved" for reference in references),
            "unresolved_reference_items": sum(
                reference["instance_count"] for reference in references if reference["category"] == "unresolved"
            ),
            "extraction_repairs": sum(len(source["repairs"]) for source in sources),
            "page_break_repairs": sum(repair["type"] == "page_break_join" for source in sources for repair in source["repairs"]),
            "same_page_fragment_repairs": sum(repair["type"] == "same_page_fragment_join" for source in sources for repair in source["repairs"]),
            "confirmed_mandatory_requirements": len(requirements),
            "unresolved_candidates": sum(source["classification"] == "unresolved" for source in sources),
            "duplicate_requirement_text_patterns": sum(count > 1 for count in normalized_requirements.values()),
            "anomalies": len(anomalies),
            "lexical_occurrences": lexical,
        },
    }

    write_json(Path("data/families.json"), {"baseline_status": BASELINE, "families": families})
    write_jsonl(Path("data/source-items.jsonl"), sources)
    write_jsonl(Path("data/requirements.jsonl"), requirements)
    write_jsonl(Path("data/references.jsonl"), references)
    write_jsonl(Path("data/anomalies.jsonl"), anomalies)
    write_json(Path("data/manifest.json"), manifest)
    validate(doc, document_hash, families, header_pages, sources, requirements, references, anomalies, manifest)
    print(json.dumps(manifest["counts"], indent=2))


if __name__ == "__main__":
    main()
