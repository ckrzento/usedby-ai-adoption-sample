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

**500 relationships · 100 tools · 461 companies**

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
| [Abnormal AI](https://www.usedby.ai/tools/abnormal-ai) | 6 |
| [Abridge](https://www.usedby.ai/tools/abridge) | 6 |
| [Adobe Firefly](https://www.usedby.ai/tools/adobe-firefly) | 6 |
| [Amplemarket](https://www.usedby.ai/tools/amplemarket) | 6 |
| [Attio](https://www.usedby.ai/tools/attio) | 6 |
| [Augment Code](https://www.usedby.ai/tools/augment-code) | 6 |
| [Baseten](https://www.usedby.ai/tools/baseten) | 6 |
| [Beamery](https://www.usedby.ai/tools/beamery) | 6 |
| [Beautiful.ai](https://www.usedby.ai/tools/beautiful) | 5 |
| [Braintrust](https://www.usedby.ai/tools/braintrust) | 5 |

## How the sample is built

The exporter starts from the [public tool directory](https://www.usedby.ai/tools). Within each category it orders tools by confirmed relationship count, then slug. It takes one tool per category per round, in category slug order, up to 100 tools. For each tool it reads the first 100 public customer rows. It keeps distinct company–tool pairs marked `CONFIRMED` with a public source and a recorded proof check. Known withdrawn source URLs are excluded.

The sample takes one relationship per tool each round, in tool slug order, up to 500 rows. Each tool contributes its non-stale records first, then its most recently checked records. Company slug breaks ties. The [manifest](https://github.com/ckrzento/usedby-ai-adoption-sample/blob/main/manifest.json) records the inventory, response hashes, counts and collection times.

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
