import sqlite3
import unittest
from app.services.online_source_service import identify_official_source, OnlineImportError, _AllowlistedRedirectHandler
from app.database.migrations import migrate

class A4OnlineSourceTests(unittest.TestCase):
    def test_allowlisted_hosts(self):
        name, info = identify_official_source("https://indiacode.nic.in/handle/123")
        self.assertEqual(name, "India Code")
        self.assertEqual(info["jurisdiction"], "Central")
    def test_rejects_non_https(self):
        with self.assertRaises(OnlineImportError):
            identify_official_source("http://indiacode.nic.in/file.pdf")
    def test_rejects_unapproved_host(self):
        with self.assertRaises(OnlineImportError):
            identify_official_source("https://example.com/file.pdf")
    def test_rejects_lookalike_host(self):
        with self.assertRaises(OnlineImportError):
            identify_official_source("https://indiacode.nic.in.example.com/file.pdf")
    def test_redirect_guard_rejects_external_target(self):
        handler = _AllowlistedRedirectHandler()
        with self.assertRaises(OnlineImportError):
            handler.redirect_request(None, None, 302, "Found", {}, "https://example.org/evil.pdf")
    def test_schema_v4(self):
        conn=sqlite3.connect(":memory:")
        conn.row_factory=sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        migrate(conn)
        cols={r["name"] for r in conn.execute("PRAGMA table_info(online_import_log)")}
        self.assertIn("requested_url",cols)
        self.assertIn("sha256",cols)
        self.assertGreaterEqual(conn.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0],4)
        conn.close()

if __name__ == "__main__": unittest.main()
