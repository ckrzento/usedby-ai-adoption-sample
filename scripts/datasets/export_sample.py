#!/usr/bin/env python3
"""Create a bounded, reviewable sample from Usedby's public API (stdlib only)."""
import argparse
import hashlib
import json
import re
import time
import socket
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from urllib.error import HTTPError, URLError

BASE = "https://www.usedby.ai"


BLOCKED_SOURCES = {
    "https://www.patronus.ai/case-studies/weaviate-leverages-patronus-percival-to-accelerate-complex-ai-agent-development",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def public_url(value):
    if not isinstance(value, str):
        return False
    try:
        url = urlsplit(value)
        return url.scheme in ("http", "https") and bool(url.hostname) and not url.username and not url.password
    except ValueError:
        return False


def date_or_none(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("invalid_date: expected ISO date or null")
    datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value


def extract(payload, expected_slug, collected_at):
    if payload.get("tool", {}).get("slug") != expected_slug:
        raise ValueError("invalid_tool: response does not match requested tool")
    tool = payload["tool"]
    customers = payload["customers"]
    rows = customers["listed"]
    if not isinstance(rows, list) or len(rows) > 100:
        raise ValueError("invalid_rows: expected at most 100 public rows")
    result, excluded = [], Counter()
    for row in rows:
        claim = row["claim"]
        if row["proof"] != claim["proof"]["level"]:
            raise ValueError("proof_mismatch: row and claim disagree")
        if row["proof"] != "CONFIRMED":
            excluded["not_confirmed"] += 1
            continue
        source = claim.get("source") or {}
        if not public_url(source.get("url")):
            excluded["no_public_source"] += 1
            continue
        if source["url"] in BLOCKED_SOURCES:
            excluded["withdrawn_source"] += 1
            continue
        checked = date_or_none(claim["proof"].get("checkedAt"))
        if checked is None:
            excluded["no_check_date"] += 1
            continue
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", claim["id"]):
            raise ValueError("invalid_claim_id")
        canonical = BASE + "/claims/" + claim["id"]
        if claim["url"] != canonical:
            raise ValueError("invalid_claim_url: expected canonical permalink")
        for value in (tool["name"], row["company"], row["slug"]):
            if not isinstance(value, str) or not value.strip():
                raise ValueError("invalid_entity: missing name or slug")
        if type(claim["proof"]["stale"]) is not bool:
            raise ValueError("invalid_stale_flag: expected boolean")
        dates, freshness = claim["dates"], claim["freshness"]
        result.append({
            "claim_id": claim["id"], "claim_url": canonical,
            "tool": tool["name"], "tool_slug": expected_slug,
            "company": row["company"], "company_slug": row["slug"],
            "proof_level": "CONFIRMED", "evidence_method": claim["proof"]["method"],
            "relationship_type": claim["relationship"]["type"],
            "source_url": source["url"],
            "source_published_at": date_or_none(dates["sourcePublishedAt"]),
            "proof_checked_at": checked, "proof_stale": claim["proof"]["stale"],
            "last_verified_at": date_or_none(freshness["lastVerifiedAt"]),
            "captured_at": date_or_none(freshness["capturedAt"]),
            "collected_at": collected_at,
        })
    return result, dict(excluded)


def select(rows, limit):
    pairs, ids = {}, {}
    for row in rows:
        pair = (row["tool_slug"], row["company_slug"])
        if pair in pairs and pairs[pair] != row:
            raise ValueError("duplicate_conflict: company/tool pair differs")
        if row["claim_id"] in ids and ids[row["claim_id"]] != pair:
            raise ValueError("duplicate_conflict: claim ID maps to multiple pairs")
        pairs[pair], ids[row["claim_id"]] = row, pair
    groups = defaultdict(list)
    for row in pairs.values():
        groups[row["tool_slug"]].append(row)
    ranked = []
    for slug, group in groups.items():
        group.sort(key=lambda r: r["company_slug"])
        group.sort(key=lambda r: r["proof_checked_at"], reverse=True)
        group.sort(key=lambda r: r["proof_stale"])
        ranked.extend((rank, slug, row) for rank, row in enumerate(group))
    ordered = [row for _, _, row in sorted(ranked)]
    return ordered[:limit], len(pairs)


def fetch(url, opener=urlopen, sleeper=time.sleep):
    request = Request(url, headers={"User-Agent": "usedby-public-sample/1.0", "Accept": "application/json"})
    for attempt in range(3):
        try:
            with opener(request, timeout=45) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError, socket.timeout) as error:
            transient = not isinstance(error, HTTPError) or error.code in (429, 500, 502, 503, 504)
            if not transient or attempt == 2:
                raise
            delay = 5 * (attempt + 1)
            if isinstance(error, HTTPError) and error.code == 429:
                retry_after = error.headers.get("Retry-After", "60")
                if not retry_after.isdigit() or int(retry_after) > 60:
                    raise
                delay = max(delay, int(retry_after))
            print(f"sample_retry: {type(error).__name__}; attempt={attempt + 2}; wait={delay}s", flush=True)
            sleeper(delay)


def render_card(template, rows):
    counts = Counter(r["tool_slug"] for r in rows)
    tools = {r["tool_slug"]: r["tool"] for r in rows}
    companies = len({r["company_slug"] for r in rows})
    example = next((r for r in rows if r["tool_slug"] == "claude"), rows[0])
    lines = [f'**{len(rows)} relationships · {len(tools)} tools · {companies} companies**',
             "", f'Example: **{example["company"]}** and **{example["tool"]}**. '
             f'[Public claim]({example["claim_url"]}) · [Original source]({example["source_url"]}).',
             "", "```json", json.dumps(example, indent=2, ensure_ascii=False), "```",
             "", "### Ten tools with the most rows in this sample", "",
             "| Tool | Rows |", "| --- | ---: |"]
    for slug, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:10]:
        lines.append(f"| [{tools[slug]}]({BASE}/tools/{slug}) | {count} |")
    return template.replace("{{preview}}", "\n".join(lines))


def run(inventory, output, limit=500, delay=2.1, fetcher=fetch):
    if output.exists():
        raise ValueError("output_exists: choose a new dated output directory")
    if not 1 <= limit <= 500:
        raise ValueError("invalid_limit: expected 1..500")
    slugs = inventory["tools"]
    if not slugs or len(slugs) != len(set(slugs)) or any(
        not isinstance(s, str) or not re.fullmatch(r"[a-z0-9-]+", s) for s in slugs
    ):
        raise ValueError("invalid_inventory: expected unique tool slugs")
    started, rows, receipts, excluded = utc_now(), [], [], Counter()
    for index, slug in enumerate(sorted(slugs)):
        if index:
            time.sleep(delay)
        url = BASE + "/api/v1/tools/" + slug + "/customers?limit=100"
        raw = fetcher(url)
        payload, collected = json.loads(raw), utc_now()
        eligible, omissions = extract(payload, slug, collected)
        rows.extend(eligible)
        excluded.update(omissions)
        receipts.append({"tool_slug": slug, "url": url, "collected_at": collected,
                         "sha256": hashlib.sha256(raw).hexdigest(),
                         "api_snapshot": payload.get("pagination", {}).get("snapshot"),
                         "public_total": payload["customers"]["total"],
                         "rows_read": len(payload["customers"]["listed"]),
                         "truncated": payload["customers"]["truncated"],
                         "eligible_rows": len(eligible), "excluded": omissions})
        print(f"sample: {index + 1}/{len(slugs)} {slug}: {len(eligible)} eligible", flush=True)
    sample, unique = select(rows, limit)
    if not sample:
        raise ValueError("empty_sample: no eligible rows; no artifact written")
    data = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in sample)
    manifest = {"schema_version": 1, "collection_started_at": started, "collection_finished_at": utc_now(),
                "inventory": inventory, "population": "First 100 public API rows for each fixed inventory tool",
                "rows_read": sum(r["rows_read"] for r in receipts), "eligible_unique_pairs": unique,
                "sample_rows": len(sample), "requested_maximum": limit, "excluded": dict(excluded),
                "deduplication": "Exact tool_slug/company_slug pair; conflicting pairs or claim IDs fail",
                "selection": "Round-robin by tool; non-stale first, then newest proof check, then company slug",
                "selection_bias": "Category-balanced catalog subset; public evidence only; first-page proof-strength ordering; CONFIRMED with public source and check date only. Not representative of adoption or market share.",
                "freshness": "Per-row checked/verified/captured dates; collected_at is retrieval, not verification. No global transactional snapshot.",
                "license": "CC-BY-4.0",
                "data_sha256": hashlib.sha256(data.encode()).hexdigest(), "receipts": receipts}
    # All network and validation work completes before any deliverable is created.
    output.mkdir(parents=True, exist_ok=False)
    (output / "data.jsonl").write_text(data, encoding="utf-8")
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    card = Path(__file__).resolve().parents[2] / "docs/datasets/sample-card.md"
    (output / "README.md").write_text(render_card(card.read_text(encoding="utf-8"), sample), encoding="utf-8")
    print(f"sample_complete: {len(sample)} rows -> {output}", flush=True)
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, default=Path(__file__).with_name("sample-tools.json"))
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    try:
        run(json.loads(args.inventory.read_text()), args.output, args.limit)
    except Exception as error:
        parser.exit(1, f"sample_failed: {type(error).__name__}: {error}\n")
