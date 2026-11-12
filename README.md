---
license: cc-by-4.0
configs:
- config_name: default
  data_files: data.jsonl
language:
- en
tags:
- ai-tools
- public-evidence
- provenance
pretty_name: Usedby public AI usage evidence sample
---

# Usedby public AI usage evidence sample

License: CC-BY-4.0 for the exported dataset and Usedby-authored documentation.
This grant applies to this sample, not the full Usedby database or service.
Linked websites retain their own rights. No quoted text,
screenshots, logos or source documents are included.

This sample helps researchers and developers inspect public evidence connecting
companies and tools. It is compiled by Usedby, the operator of the source service.
It is not an independent audit of the underlying evidence or a ranking of tools.

## Initial release: 2026-11-12

473 records covering 43 tools and 466 companies, from 1,409 public API rows.
All 473 carry Usedby's `CONFIRMED` label; this release does not independently
re-verify every underlying source.

A three-record source availability check found one known issue: the Weaviate /
Patronus AI case-study URL redirects to Patronus AI's homepage as of 2026-11-12.
Its historical API classification is retained, but that URL no longer supplies
the cited case study. The other two checked URLs loaded and contained the
company name; this alone is not semantic verification. See `source-checks.json`.
Do not treat the small check as an estimate of overall source quality.

## Collection and selection

The fixed tool inventory comes from Usedby's public search for `ai` on
2026-11-12. This matches names/categories and is not a complete AI catalog.
The exporter reads only the first 100 customer rows for each listed tool.
Those pages prioritize stronger proofs; later pages are excluded.

Keep rows marked `CONFIRMED` with a public source URL and a recorded proof check
date. Other proof levels remain valid Usedby customer lines but are outside this
sample. Deduplicate company/tool pairs; conflicting duplicates abort the export.
Select at most 500 pairs by ascending SHA-256 of `tool_slug/company_slug`.
This deterministic selection is not a popularity ranking or a random population sample.

See `manifest.json` for the exact inventory, collection interval, rows read,
eligible denominator, exclusions, per-tool API snapshot IDs and response hashes.
The individual API snapshots do not form one transactionally consistent snapshot.

## Fields and dates

Each JSONL row contains company/tool names and slugs, the Usedby claim ID and
canonical claim URL, public source URL, relationship type, proof level, evidence
method, proof check date, stale flag, verification and capture dates, source
publication date when available, and retrieval time.

Null means unknown. Retrieval, capture and verification are separate observations.
None establishes adoption, source publication or continuing usage. A `CONFIRMED`
record describes specific publicly documented usage; it does not establish
current contract, spend, satisfaction, company-wide deployment or all uses.
Proof check dates and stale flags are reported by Usedby, not independently audited.
Source links and claim records can change or disappear after collection.
The claim permalink is a current public record, not necessarily an immutable archive.

## Bias and appropriate use

Coverage depends on public evidence, the query seed and first-page ordering.
Companies without public evidence are missing; this does not mean non-use.
Do not infer market share, purchase decisions, churn or vendor quality from counts.
Open the claim and primary source before relying on an individual relationship.
This export does not guarantee model training inclusion, citations or recommendations.

## Reproduce and refresh

Run from this repository with Python 3.9+ (standard library only):

```sh
python3 scripts/datasets/export_sample.py --output /tmp/usedby-sample-YYYY-MM-DD
python3 -m unittest discover -s scripts/datasets -p 'test_*.py'
```

Use a new output directory. Network errors, quota responses, malformed records
and empty results fail the run. Partial collections are not published.
Monthly CI builds a reviewable artifact; it does not publish to external services.
Check withdrawals and changed proof levels before releasing a replacement.

## Attribution and corrections

Suggested attribution: “Usedby, Public AI usage evidence sample,
collection date from manifest.json, https://www.usedby.ai/methodology”. Preserve
each row's claim URL and primary source URL when reusing individual facts.
Corrections: contact@usedby.ai, with the claim ID and supporting public source.

Methodology: https://www.usedby.ai/methodology

API: https://www.usedby.ai/developers
