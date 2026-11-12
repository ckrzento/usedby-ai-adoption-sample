"""Read the public directory and allocate a bounded API budget across categories."""
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

URL = "https://www.usedby.ai/tools"


def inventory(html):
    streams = [json.loads(match) for match in re.findall(
        r'self\.__next_f\.push\(\[1,("(?:\\.|[^"\\])*")\]\)', html)]
    stream = "".join(streams)
    start = stream.index('"rows":[{"id":') + len('"rows":')
    rows, _ = json.JSONDecoder().raw_decode(stream[start:])
    groups = defaultdict(list)
    for row in rows:
        if row["mix"]["confirmed"]:
            groups[(row.get("category") or {}).get("slug", "uncategorized")].append(row)
    ranked = []
    for category, tools in groups.items():
        for rank, tool in enumerate(sorted(tools, key=lambda t: (-t["mix"]["confirmed"], t["slug"]))):
            ranked.append((rank, category, tool["slug"]))
    chosen = sorted(ranked)[:100]
    return {"source": URL, "collected_at": datetime.now(timezone.utc).isoformat(),
            "catalog_tools": len(rows), "tools_with_confirmed": len(ranked),
            "selection": "Up to 100 tools, round-robin across categories, confirmed count then slug within category",
            "categories": {slug: category for _, category, slug in chosen},
            "tools": [slug for _, _, slug in chosen]}


if __name__ == "__main__":
    with urlopen(URL, timeout=45) as response:
        result = inventory(response.read().decode())
    Path(__file__).with_name("sample-tools.json").write_text(json.dumps(result, indent=2) + "\n")
