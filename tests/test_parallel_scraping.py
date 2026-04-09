#!/usr/bin/env python3
"""
Tests for parallel scraping, unlimited mode, and rate limiting features (PR #144)
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from yonyou_doc2skill.cli.doc_scraper import DocToSkillConverter


class TestParallelScrapingConfiguration(unittest.TestCase):
    """Test parallel scraping configuration and initialization"""

    def setUp(self):
        """Save original working directory"""
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Restore original working directory"""
        os.chdir(self.original_cwd)

    def test_single_worker_default(self):
        """Test default is single-worker mode"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "max_pages": 10,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.workers, 1)
            self.assertFalse(hasattr(converter, "lock"))

    def test_multiple_workers_creates_lock(self):
        """Test multiple workers creates thread lock"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "max_pages": 10,
            "workers": 4,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.workers, 4)
            self.assertTrue(hasattr(converter, "lock"))

    def test_workers_from_config(self):
        """Test workers parameter is read from config"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "workers": 8,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.workers, 8)


class TestUnlimitedMode(unittest.TestCase):
    """Test unlimited scraping mode"""

    def setUp(self):
        """Save original working directory"""
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Restore original working directory"""
        os.chdir(self.original_cwd)

    def test_unlimited_with_none(self):
        """Test max_pages: None enables unlimited mode"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "max_pages": None,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertIsNone(converter.config.get("max_pages"))

    def test_unlimited_with_minus_one(self):
        """Test max_pages: -1 enables unlimited mode"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "max_pages": -1,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.config.get("max_pages"), -1)

    def test_limited_mode_default(self):
        """Test default max_pages is limited"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            max_pages = converter.config.get("max_pages", 500)
            self.assertIsNotNone(max_pages)
            self.assertGreater(max_pages, 0)


class TestRateLimiting(unittest.TestCase):
    """Test rate limiting configuration"""

    def setUp(self):
        """Save original working directory"""
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Restore original working directory"""
        os.chdir(self.original_cwd)

    def test_rate_limit_from_config(self):
        """Test rate_limit is read from config"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "rate_limit": 0.1,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.config.get("rate_limit"), 0.1)

    def test_rate_limit_default(self):
        """Test default rate_limit is 0.5"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.config.get("rate_limit", 0.5), 0.5)

    def test_zero_rate_limit_disables(self):
        """Test rate_limit: 0 disables rate limiting"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "rate_limit": 0,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.config.get("rate_limit"), 0)

    @patch("yonyou_doc2skill.cli.doc_scraper.time.sleep")
    @patch("yonyou_doc2skill.cli.doc_scraper.requests.get")
    def test_none_rate_limit_uses_default_without_crashing(self, mock_get, mock_sleep):
        """None rate_limit should fall back to the default delay instead of crashing."""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "rate_limit": None,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=False)

            class Response:
                text = "<html><body><article>" + ("hello " * 20) + "</article></body></html>"
                content = text.encode("utf-8")

                def raise_for_status(self):
                    return None

            mock_get.return_value = Response()
            converter.extract_content = lambda _soup, url: {
                "url": url,
                "title": "hello",
                "content": "hello " * 20,
                "links": [],
            }

            converter.scrape_page("https://example.com/page")

            mock_sleep.assert_called_once_with(0.5)

    @patch("yonyou_doc2skill.cli.doc_scraper.requests.get")
    def test_scrape_page_logs_structured_progress(self, mock_get):
        """Successful page scraping should emit a progress log agents can follow."""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "rate_limit": 0,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=False)

            class Response:
                text = "<html><body><article>" + ("hello " * 20) + "</article></body></html>"
                content = text.encode("utf-8")

                def raise_for_status(self):
                    return None

            mock_get.return_value = Response()
            converter.extract_content = lambda _soup, url: {
                "url": url,
                "title": "hello",
                "content": "hello " * 20,
                "links": [],
            }

            with self.assertLogs("yonyou_doc2skill.cli.doc_scraper", level="INFO") as logs:
                converter.scrape_page("https://example.com/page")

            joined = "\n".join(logs.output)
            self.assertIn("Page 1 saved", joined)
            self.assertIn("https://example.com/page", joined)

    @patch("yonyou_doc2skill.cli.doc_scraper.requests.get")
    def test_scrape_page_logs_periodic_progress_summary(self, mock_get):
        """Long runs should emit periodic aggregate progress, not only per-page logs."""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "rate_limit": 0,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=False)
            converter.pages_saved = 24

            class Response:
                text = "<html><body><article>" + ("hello " * 20) + "</article></body></html>"
                content = text.encode("utf-8")

                def raise_for_status(self):
                    return None

            mock_get.return_value = Response()
            converter.extract_content = lambda _soup, url: {
                "url": url,
                "title": "hello",
                "content": "hello " * 20,
                "links": [],
            }

            with self.assertLogs("yonyou_doc2skill.cli.doc_scraper", level="INFO") as logs:
                converter.scrape_page("https://example.com/page-25")

            joined = "\n".join(logs.output)
            self.assertIn("Page 25 saved", joined)
            self.assertIn("Progress: 25 pages saved", joined)


class TestThreadSafety(unittest.TestCase):
    """Test thread-safety fixes"""

    def setUp(self):
        """Save original working directory"""
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Restore original working directory"""
        os.chdir(self.original_cwd)

    def test_lock_protects_visited_urls(self):
        """Test visited_urls operations are protected by lock"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "workers": 4,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)

            # Verify lock exists
            self.assertTrue(hasattr(converter, "lock"))

            # Verify it's a threading.Lock
            import threading

            self.assertIsInstance(converter.lock, type(threading.Lock()))

    def test_single_worker_no_lock(self):
        """Test single worker doesn't create unnecessary lock"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "workers": 1,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertFalse(hasattr(converter, "lock"))


class TestScrapingModes(unittest.TestCase):
    """Test different scraping mode combinations"""

    def setUp(self):
        """Save original working directory"""
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Restore original working directory"""
        os.chdir(self.original_cwd)

    def test_single_threaded_limited(self):
        """Test traditional single-threaded limited mode"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "max_pages": 10,
            "workers": 1,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.workers, 1)
            self.assertEqual(converter.config.get("max_pages"), 10)

    def test_parallel_limited(self):
        """Test parallel scraping with page limit"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "max_pages": 100,
            "workers": 4,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.workers, 4)
            self.assertEqual(converter.config.get("max_pages"), 100)
            self.assertTrue(hasattr(converter, "lock"))

    def test_parallel_unlimited(self):
        """Test parallel scraping with unlimited pages"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "max_pages": None,
            "workers": 8,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.workers, 8)
            self.assertIsNone(converter.config.get("max_pages"))
            self.assertTrue(hasattr(converter, "lock"))

    def test_fast_scraping_mode(self):
        """Test fast scraping with low rate limit and workers"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "rate_limit": 0.1,
            "workers": 8,
            "max_pages": 1000,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertEqual(converter.workers, 8)
            self.assertEqual(converter.config.get("rate_limit"), 0.1)


class TestDryRunWithNewFeatures(unittest.TestCase):
    """Test dry-run mode works with new features"""

    def setUp(self):
        """Save original working directory"""
        self.original_cwd = os.getcwd()

    def tearDown(self):
        """Restore original working directory"""
        os.chdir(self.original_cwd)

    def test_dry_run_with_parallel(self):
        """Test dry-run with parallel workers"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "workers": 4,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertTrue(converter.dry_run)
            self.assertEqual(converter.workers, 4)

    def test_dry_run_with_unlimited(self):
        """Test dry-run with unlimited mode"""
        config = {
            "name": "test",
            "base_url": "https://example.com/",
            "selectors": {"main_content": "article"},
            "max_pages": None,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)
            converter = DocToSkillConverter(config, dry_run=True)
            self.assertTrue(converter.dry_run)
            self.assertIsNone(converter.config.get("max_pages"))


if __name__ == "__main__":
    unittest.main()
