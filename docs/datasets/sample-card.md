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

{{preview}}

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
