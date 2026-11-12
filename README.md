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
pretty_name: usedby public AI adoption sample
---

# Who uses which AI tools?

Use this dataset to find a documented example of a company using an AI tool. Each row links the company and tool to a usedby claim and its original public source.

**500 relationships · 100 tools · 463 companies**

Example: **Intercom** and **Claude**. [Public claim](https://www.usedby.ai/claims/cmjzggc8c00rn569kaflxnkkp) · [Original source](https://www.intercom.com/blog/fin-2-powered-by-anthropic-claude-llm).

```json
{
  "captured_at": "2026-11-11T09:32:33.685Z",
  "claim_id": "cmjzggc8c00rn569kaflxnkkp",
  "claim_url": "https://www.usedby.ai/claims/cmjzggc8c00rn569kaflxnkkp",
  "collected_at": "2026-11-12T14:00:14.583577+00:00",
  "company": "Intercom",
  "company_slug": "intercom",
  "evidence_method": "CASE_STUDY",
  "last_verified_at": "2026-11-11T09:32:33.685Z",
  "proof_checked_at": "2026-11-11",
  "proof_level": "CONFIRMED",
  "proof_stale": false,
  "relationship_type": "documented_usage",
  "source_published_at": null,
  "source_url": "https://www.intercom.com/blog/fin-2-powered-by-anthropic-claude-llm",
  "tool": "Claude",
  "tool_slug": "claude"
}
```

### Ten tools with the most rows in this sample

| Tool | Rows |
| --- | ---: |
| [Baseten](https://www.usedby.ai/tools/baseten) | 10 |
| [CodeRabbit](https://www.usedby.ai/tools/coderabbit) | 9 |
| [Dust](https://www.usedby.ai/tools/dust) | 9 |
| [Exa](https://www.usedby.ai/tools/exa) | 9 |
| [Glean](https://www.usedby.ai/tools/glean) | 9 |
| [Synthesia](https://www.usedby.ai/tools/synthesia) | 9 |
| [Perplexity](https://www.usedby.ai/tools/perplexity) | 8 |
| [Photoroom](https://www.usedby.ai/tools/photoroom) | 8 |
| [Vanta](https://www.usedby.ai/tools/vanta) | 8 |
| [Braintrust](https://www.usedby.ai/tools/braintrust) | 7 |

## How the sample is built

The exporter starts from the [public tool directory](https://www.usedby.ai/tools). Within each category it orders tools by confirmed relationship count, then slug. It takes one tool per category per round, in category slug order, up to 100 tools. For each tool it reads the first 100 public customer rows. It keeps distinct company–tool pairs marked `CONFIRMED` with a public source and a recorded proof check. Known withdrawn URLs and previously rejected claim/source pairs are excluded. Monthly builds produce review candidates. A release may contain fewer rows after evidence review.

The sample takes one relationship per tool each round, in tool slug order, up to 500 rows. Each tool contributes its non-stale records first, then its most recently checked records. Company slug breaks ties. The [manifest](https://github.com/ckrzento/usedby-ai-adoption-sample/blob/main/manifest.json) records the inventory, response hashes, counts and collection times.

The latest maintenance run rechecked 500 published relationships, retained 499 and replaced 1. Direct reads were compared with previously reviewed evidence. The [review log](https://github.com/ckrzento/usedby-ai-adoption-sample/blob/main/source-checks.json) records exceptions, alternate publisher pages and decisions.

## Interpretation

Counts describe this sample. Public disclosure, directory coverage and first-page ordering affect inclusion. A case study can document a specific use. It cannot establish current spend or company-wide deployment. Open the linked source to check its scope. Null dates mean unknown. Collection time records retrieval. Proof checks, source publication and verification each have a separate field. Links can change after collection.

## Reproduce and cite

The [exporter and tests](https://github.com/ckrzento/usedby-ai-adoption-sample/tree/main/scripts/datasets) use Python's standard library. Run these commands from the GitHub checkout. Use the committed inventory to repeat the selection on current API data.

```sh
python3 scripts/datasets/export_sample.py --output /tmp/usedby-sample-YYYY-MM-DD
python3 -m unittest discover -s scripts/datasets -p 'test_*.py'
```

Credit **usedby, Public AI adoption sample**, with the collection date from the manifest. Preserve the claim and original source links. CC BY 4.0 covers the exported data and usedby documentation. Linked sources retain their own rights. The exporter uses the MIT license.

[Methodology](https://www.usedby.ai/methodology) · [API](https://www.usedby.ai/developers) · [Report a correction](mailto:contact@usedby.ai)
