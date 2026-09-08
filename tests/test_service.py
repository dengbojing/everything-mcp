import unittest
from unittest.mock import patch

from everything_mcp import service as app


class UnitTests(unittest.TestCase):
    def test_filters(self):
        f = app.Filters(
            min_bytes=0,
            max_bytes=100,
            modified_from="2025-11-01",
            modified_to="2025-11-30",
            extensions=[".pdf"],
        )
        self.assertIn("dm:<2025-12-01", f.expression())
        for values in (
            {"min_bytes": 2, "max_bytes": 1},
            {"extensions": ["pdf | file:"]},
            {"recent_days": 1, "modified_from": "2025-01-01"},
        ):
            with self.assertRaises(ValueError):
                app.Filters(**values)

    def test_mixed_polyphonic(self):
        self.assertTrue(app.pinyin_match("约会指南.pdf", "约会zn", "mixed", False))
        self.assertTrue(app.pinyin_match("重庆报告", "chongqing", "full", True))
        self.assertTrue(app.pinyin_match("重庆报告", "zhongqing", "full", True))
        self.assertFalse(app.pinyin_match("重庆报告", "beijing", "full", True))

    def test_typo_pagination(self):
        page = {
            "items": [{"path": "D:\\合同.pdf"}, {"path": "D:\\合约.pdf"}],
            "has_more": True,
            "next_offset": 2,
        }
        with patch.object(app, "everything_search", return_value=page):
            result = app.everything_search_typo("合同", threshold=40)
            self.assertEqual(result["items"][0]["score"], 100)
            self.assertEqual(result["next_candidate_offset"], 2)
            self.assertFalse(result["candidates_exhausted"])

    def test_switch_rejected(self):
        for query in ("-exit", "/reindex", "  -save-db", ""):
            with self.assertRaises(ValueError):
                app.everything_search(query)

    def test_csv_unicode(self):
        with patch.object(
            app,
            "run_es",
            return_value='Filename,Size,Date Modified\n"D:\\中文,文件.pdf",123,2025-01-01\n',
        ):
            self.assertEqual(app.everything_search("中文")["items"][0]["size_bytes"], 123)

    def test_empty(self):
        with patch.object(app, "run_es", return_value="Filename,Size,Date Modified\n"):
            self.assertEqual(app.everything_search("不存在")["items"], [])

    def test_pinyin(self):
        page = {"items": [{"path": "D:\\约会指南.pdf"}], "has_more": False}
        for query in ("yuehuizhinan", "yhzn"):
            with patch.object(app, "everything_search", return_value=page):
                self.assertEqual(app.everything_search_pinyin(query)["returned"], 1)

    def test_fuzzy_literal(self):
        with patch.object(app, "everything_search_regex", return_value={}) as call:
            app.everything_search_fuzzy("a.b")
            self.assertEqual(call.call_args.args[0], r"a.*\..*b")


if __name__ == "__main__":
    unittest.main()
