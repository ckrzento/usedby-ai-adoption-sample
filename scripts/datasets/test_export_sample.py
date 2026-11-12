import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from urllib.error import HTTPError

from catalog_inventory import inventory
from export_sample import extract, run, select, fetch, BLOCKED_SOURCES, render_card


def response():
    return {"tool": {"name": "Synthetic Tool", "slug": "synthetic-tool"},
            "customers": {"total": 1, "truncated": False, "listed": [{
                "company": "Synthetic Company", "slug": "synthetic-company", "proof": "CONFIRMED",
                "claim": {"id": "synthetic-claim", "url": "https://www.usedby.ai/claims/synthetic-claim",
                          "proof": {"level": "CONFIRMED", "method": "CASE_STUDY", "checkedAt": "2026-11-01", "stale": False},
                          "relationship": {"type": "documented_usage"},
                          "source": {"url": "https://example.com/source", "excerpt": "DO NOT REDISTRIBUTE"},
                          "freshness": {"lastVerifiedAt": None, "capturedAt": "2026-11-01T00:00:00Z"},
                          "dates": {"sourcePublishedAt": None}}}]}}


class SampleTests(unittest.TestCase):
    def test_published_snapshot_integrity(self):
        root = Path(__file__).resolve().parents[2]
        data = (root / "data.jsonl").read_bytes()
        manifest = json.loads((root / "manifest.json").read_text())
        rows = [json.loads(line) for line in data.splitlines()]
        self.assertEqual(hashlib.sha256(data).hexdigest(), manifest["data_sha256"])
        self.assertEqual(len(rows), manifest["sample_rows"])
        self.assertTrue(0 < len(rows) <= 500)
        self.assertEqual(len({(r["tool_slug"], r["company_slug"]) for r in rows}), len(rows))
        self.assertEqual(sum(r["rows_read"] for r in manifest["receipts"]), manifest["rows_read"])
        for row in rows:
            self.assertEqual(row["proof_level"], "CONFIRMED")
            self.assertTrue(row["proof_checked_at"])
            self.assertTrue(row["source_url"].startswith(("https://", "http://")))
            self.assertEqual(row["claim_url"], "https://www.usedby.ai/claims/" + row["claim_id"])
            self.assertIs(type(row["proof_stale"]), bool)
            self.assertNotIn("excerpt", row)

    def test_transient_errors_retry_but_auth_errors_do_not(self):
        for status, expected in ((503, 3), (403, 1), (429, 3)):
            calls, waits = [], []
            def opener(*args, **kwargs):
                calls.append(1)
                raise HTTPError("https://example.com", status, "synthetic error", {"Retry-After": "7"}, None)
            with self.assertRaises(HTTPError):
                fetch("https://example.com", opener=opener, sleeper=waits.append)
            self.assertEqual(len(calls), expected)
            if status == 429:
                self.assertEqual(waits, [7, 10])

    def test_dates_stay_distinct_and_third_party_text_is_not_exported(self):
        rows, excluded = extract(response(), "synthetic-tool", "2026-11-12T00:00:00Z")
        self.assertEqual(excluded, {})
        self.assertIsNone(rows[0]["source_published_at"])
        self.assertIsNone(rows[0]["last_verified_at"])
        self.assertNotIn("DO NOT REDISTRIBUTE", json.dumps(rows))

    def test_catalog_balances_categories_before_filling_remaining_slots(self):
        tools = [{"id": str(i), "slug": f"a-{i}", "category": {"slug": "a"},
                  "mix": {"confirmed": i}} for i in range(102)]
        tools.append({"id": "last", "slug": "b", "category": {"slug": "b"}, "mix": {"confirmed": 1}})
        stream = json.dumps({"rows": tools}, separators=(",", ":"))
        html = f"<script>self.__next_f.push([1,{json.dumps(stream)}])</script>"
        result = inventory(html)
        self.assertEqual(result["catalog_tools"], 103)
        self.assertEqual(len(result["tools"]), 100)
        self.assertEqual(result["tools"][:2], ["a-101", "b"])
        self.assertNotIn("a-0", result["tools"])

    def test_publication_matches_source_review(self):
        root = Path(__file__).resolve().parents[2]
        audit = json.loads((root / "source-checks.json").read_text())
        reviewed = {(r["claim_id"], r["source_url"]) for r in audit["checks"] if r["decision"] == "retain"}
        published = [json.loads(line) for line in (root / "data.jsonl").read_text().splitlines()]
        self.assertEqual(reviewed, {(r["claim_id"], r["source_url"]) for r in published})
        self.assertEqual(len(audit["checks"]), audit["reviewed_rows"])
        self.assertEqual(len(published), audit["retained"])

    def test_withdrawn_source_is_excluded(self):
        payload = response()
        payload["customers"]["listed"][0]["claim"]["source"]["url"] = next(iter(BLOCKED_SOURCES))
        self.assertEqual(extract(payload, "synthetic-tool", "today"), ([], {"withdrawn_source": 1}))

    def test_selection_covers_tools_and_prefers_fresh_records(self):
        rows, _ = extract(response(), "synthetic-tool", "today")
        fresh = rows[0]
        stale = dict(fresh, claim_id="stale", company_slug="stale", proof_stale=True)
        other = dict(fresh, claim_id="other", tool_slug="another-tool")
        selected, _ = select([stale, other, fresh], 2)
        self.assertEqual(selected, [other, fresh])
        self.assertIn(json.dumps(other, indent=2), render_card("{{preview}}", selected))

    def test_exclusions(self):
        for kind in ("signal", "source", "date", "credentials"):
            data = response()
            row = data["customers"]["listed"][0]
            if kind == "signal":
                row["proof"] = row["claim"]["proof"]["level"] = "SIGNAL"
            elif kind == "source":
                row["claim"]["source"] = None
            elif kind == "credentials":
                row["claim"]["source"]["url"] = "https://user:secret@example.com/source"
            else:
                row["claim"]["proof"]["checkedAt"] = None
            rows, excluded = extract(data, "synthetic-tool", "today")
            self.assertEqual(rows, [])
            self.assertEqual(sum(excluded.values()), 1)

    def test_mismatch_and_invalid_date_fail_closed(self):
        for kind in ("tool", "proof", "date", "url"):
            data = response()
            claim = data["customers"]["listed"][0]["claim"]
            if kind == "tool":
                data["tool"]["slug"] = "wrong"
            elif kind == "proof":
                claim["proof"]["level"] = "SIGNAL"
            elif kind == "url":
                claim["url"] = "https://example.com/wrong"
            else:
                claim["proof"]["checkedAt"] = "not-a-date"
            with self.assertRaises(ValueError):
                extract(data, "synthetic-tool", "today")

    def test_selection_deduplicates_and_is_order_independent(self):
        rows, _ = extract(response(), "synthetic-tool", "today")
        second = dict(rows[0], claim_id="second", company_slug="second")
        self.assertEqual(select(rows + [second] + rows, 1), select([second] + rows, 1))
        self.assertEqual(select(rows + rows, 500)[1], 1)
        with self.assertRaisesRegex(ValueError, "duplicate_conflict"):
            select(rows + [dict(rows[0], source_url="https://example.com/changed")], 500)
        with self.assertRaisesRegex(ValueError, "duplicate_conflict"):
            select(rows + [dict(rows[0], company_slug="another")], 500)

    def test_empty_network_and_malformed_leave_no_output(self):
        empty = response()
        empty["customers"]["listed"] = []
        def failed(_):
            raise HTTPError("https://example.com", 429, "synthetic quota error", {}, None)
        for fetcher in (lambda _: json.dumps(empty).encode(), lambda _: b"not json", failed):
            with tempfile.TemporaryDirectory() as root:
                output = Path(root) / "export"
                with self.assertRaises(Exception):
                    run({"tools": ["synthetic-tool"]}, output, delay=0, fetcher=fetcher)
                self.assertFalse(output.exists())

    def test_success_and_existing_directory_guard(self):
        with tempfile.TemporaryDirectory() as root:
            output = Path(root) / "export"
            manifest = run({"tools": ["synthetic-tool"]}, output, delay=0,
                           fetcher=lambda _: json.dumps(response()).encode())
            self.assertEqual(manifest["sample_rows"], 1)
            self.assertEqual(set(p.name for p in output.iterdir()), {"README.md", "manifest.json", "data.jsonl"})
            self.assertEqual(json.loads((output / "manifest.json").read_text()), manifest)
            with self.assertRaisesRegex(ValueError, "output_exists"):
                run({"tools": ["synthetic-tool"]}, output)


if __name__ == "__main__":
    unittest.main()
