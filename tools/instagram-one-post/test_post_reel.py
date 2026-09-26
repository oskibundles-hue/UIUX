"""Tests for post_reel.py against a fake Instagram Graph API.

Run: python3 -m unittest -v test_post_reel.py
"""

import contextlib
import io
import json
import os
import tempfile
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import post_reel

TOKEN = "test-token-abc123"
VIDEO_BYTES = 1234


class FakeInstagram:
    """Minimal stand-in for graph.instagram.com, rupload and a Dropbox raw link."""

    def __init__(self):
        self.username = "nq.young"
        self.recent = []                       # captions already on the account
        self.statuses = ["IN_PROGRESS", "FINISHED"]
        self.post_during_processing = None     # caption another agent posts mid-processing
        self.publish_fails = False
        self.calls = []                        # (method, path, params)
        self.uploaded = None
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _reply(self, code, obj, headers=None):
                body = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                for k, v in (headers or {}).items():
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                u = urllib.parse.urlparse(self.path)
                q = dict(urllib.parse.parse_qsl(u.query))
                fake.calls.append(("GET", u.path, q))
                if u.path == "/video.mp4":
                    self.send_response(206)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Range", f"bytes 0-15/{VIDEO_BYTES}")
                    self.send_header("Content-Length", "16")
                    self.end_headers()
                    self.wfile.write(b"\0" * 16)
                    return
                if q.get("access_token") != TOKEN:
                    return self._reply(400, {"error": {"message": "Invalid OAuth 2.0 Access Token", "code": 190}})
                if u.path == "/v23.0/me":
                    return self._reply(200, {"id": "999", "user_id": "178", "username": fake.username})
                if u.path == "/v23.0/178/media":
                    return self._reply(200, {"data": [
                        {"id": str(i), "caption": c, "timestamp": "2026-09-26T19:00:00+0000",
                         "permalink": f"https://www.instagram.com/reel/x{i}/"} for i, c in enumerate(fake.recent)]})
                if u.path == "/v23.0/178/content_publishing_limit":
                    return self._reply(200, {"data": [{"quota_usage": 2, "config": {"quota_total": 100}}]})
                if u.path == "/v23.0/C1":
                    status = fake.statuses.pop(0) if len(fake.statuses) > 1 else fake.statuses[0]
                    if fake.post_during_processing:
                        fake.recent.append(fake.post_during_processing)
                        fake.post_during_processing = None
                    return self._reply(200, {"status_code": status, "status": status, "id": "C1"})
                if u.path == "/v23.0/M1":
                    return self._reply(200, {"permalink": "https://www.instagram.com/reel/NEW/",
                                             "timestamp": "2026-09-26T22:00:00+0000"})
                return self._reply(404, {"error": {"message": "unknown path " + u.path}})

            def do_POST(self):
                u = urllib.parse.urlparse(self.path)
                length = int(self.headers.get("Content-Length", 0))
                raw = self.rfile.read(length)
                if u.path.startswith("/ig-api-upload/"):
                    fake.calls.append(("UPLOAD", u.path, {k.lower(): v for k, v in self.headers.items()}))
                    fake.uploaded = raw
                    return self._reply(200, {"success": True, "message": "Upload successful."})
                q = dict(urllib.parse.parse_qsl(raw.decode()))
                fake.calls.append(("POST", u.path, q))
                if q.get("access_token") != TOKEN:
                    return self._reply(400, {"error": {"message": "bad token", "code": 190}})
                if u.path == "/v23.0/178/media":
                    out = {"id": "C1"}
                    if q.get("upload_type") == "resumable":
                        out["uri"] = f"{fake.base}/ig-api-upload/v23.0/C1"
                    return self._reply(200, out)
                if u.path == "/v23.0/178/media_publish":
                    if fake.publish_fails:
                        return self._reply(500, {"error": {"message": "An unexpected error has occurred.", "code": 2}})
                    return self._reply(200, {"id": "M1"})
                return self._reply(404, {"error": {"message": "unknown path " + u.path}})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()

    def posts(self, path_suffix):
        return [c for c in self.calls if c[0] == "POST" and c[1].endswith(path_suffix)]


class PostReelTest(unittest.TestCase):
    def setUp(self):
        self.fake = FakeInstagram()
        self.tmp = tempfile.TemporaryDirectory()
        self.state = os.path.join(self.tmp.name, "state")
        self.config = os.path.join(self.tmp.name, "post.json")
        self.write_config()
        os.environ["IG_ACCESS_TOKEN"] = TOKEN
        os.environ.pop("IG_VIDEO_URL", None)

    def tearDown(self):
        self.fake.close()
        self.tmp.cleanup()
        os.environ.pop("IG_ACCESS_TOKEN", None)

    def write_config(self, **over):
        cfg = {"title": "The floor goes down", "account_username": "@NQ.young",
               "caption": "The floor goes down 🏗️🔥 Shop build.\n\n#shopbuild",
               "duplicate_marker": "The floor goes down", "expected_size_bytes": VIDEO_BYTES,
               "thumb_offset_ms": 1000}
        cfg.update(over)
        with open(self.config, "w", encoding="utf-8") as f:
            json.dump(cfg, f)

    def run_tool(self, *extra):
        out = io.StringIO()
        argv = ["--config", self.config, "--state-dir", self.state, "--graph-base", self.fake.base,
                "--rupload-base", self.fake.base, "--poll-seconds", "0", "--timeout-minutes", "0.05",
                "--video-url", self.fake.base + "/video.mp4", *extra]
        with contextlib.redirect_stdout(out):
            code = post_reel.main(argv)
        return code, out.getvalue()

    def test_dry_run_posts_nothing(self):
        code, out = self.run_tool()
        self.assertEqual(code, 0, out)
        self.assertIn("DRY RUN passed", out)
        self.assertEqual([c for c in self.fake.calls if c[0] == "POST"], [])

    def test_publish_happy_path_posts_once(self):
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 0, out)
        self.assertIn("POSTED to @nq.young: https://www.instagram.com/reel/NEW/", out)
        created = self.fake.posts("/178/media")
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0][2]["media_type"], "REELS")
        self.assertEqual(created[0][2]["video_url"], self.fake.base + "/video.mp4")
        self.assertEqual(created[0][2]["thumb_offset"], "1000")
        self.assertEqual(created[0][2]["share_to_feed"], "true")
        self.assertIn("🏗️", created[0][2]["caption"])
        self.assertEqual(len(self.fake.posts("/media_publish")), 1)
        self.assertNotIn(TOKEN, out)

    def test_second_run_refused_by_state_file(self):
        self.assertEqual(self.run_tool("--publish")[0], 0)
        self.fake.calls.clear()
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 1, out)
        self.assertIn("already posted from here", out)
        self.assertEqual([c for c in self.fake.calls if c[0] == "POST"], [])

    def test_wrong_account_refused(self):
        self.fake.username = "youngomarie"
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 1, out)
        self.assertIn("token is for @youngomarie", out)
        self.assertEqual([c for c in self.fake.calls if c[0] == "POST"], [])

    def test_already_on_account_refused(self):
        self.fake.recent = ["The floor goes down 🏗️🔥 Studio build officially underway."]
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 1, out)
        self.assertIn("already has this post", out)
        self.assertEqual([c for c in self.fake.calls if c[0] == "POST"], [])

    def test_posted_elsewhere_while_processing_is_not_published(self):
        self.fake.post_during_processing = "The floor goes down (posted by Darkweb)"
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 1, out)
        self.assertIn("went up elsewhere", out)
        self.assertEqual(len(self.fake.posts("/media_publish")), 0)

    def test_processing_error_is_not_published(self):
        self.fake.statuses = ["IN_PROGRESS", "ERROR"]
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 3, out)
        self.assertIn("could not process", out)
        self.assertEqual(len(self.fake.posts("/media_publish")), 0)

    def test_processing_timeout_is_not_published(self):
        self.fake.statuses = ["IN_PROGRESS"]
        code, out = self.run_tool("--publish", "--poll-seconds", "0.5")
        self.assertEqual(code, 3, out)
        self.assertIn("still processing", out)
        self.assertEqual(len(self.fake.posts("/media_publish")), 0)

    def test_publish_failure_is_not_retried(self):
        self.fake.publish_fails = True
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 3, out)
        self.assertIn("Do not re-run blindly", out)
        self.assertEqual(len(self.fake.posts("/media_publish")), 1)
        self.assertFalse(os.path.exists(self.state))

    def test_resumable_file_upload(self):
        video = os.path.join(self.tmp.name, "reel.mp4")
        with open(video, "wb") as f:
            f.write(b"x" * 5000)
        code, out = self.run_tool("--publish", "--video-file", video)
        self.assertEqual(code, 0, out)
        created = self.fake.posts("/178/media")[0][2]
        self.assertEqual(created["upload_type"], "resumable")
        self.assertNotIn("video_url", created)
        upload = [c for c in self.fake.calls if c[0] == "UPLOAD"][0][2]
        self.assertEqual(upload["offset"], "0")
        self.assertEqual(upload["file_size"], "5000")
        self.assertEqual(upload["authorization"], f"OAuth {TOKEN}")
        self.assertEqual(self.fake.uploaded, b"x" * 5000)

    def test_wrong_file_size_refused(self):
        self.write_config(expected_size_bytes=999)
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 2, out)
        self.assertIn("wrong file?", out)
        self.assertEqual([c for c in self.fake.calls if c[0] == "POST"], [])

    def test_missing_token(self):
        os.environ.pop("IG_ACCESS_TOKEN")
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 2, out)
        self.assertIn("IG_ACCESS_TOKEN is not set", out)

    def test_bad_token_error_is_redacted(self):
        os.environ["IG_ACCESS_TOKEN"] = "wrong-token-xyz"
        code, out = self.run_tool()
        self.assertEqual(code, 3, out)
        self.assertIn("Invalid OAuth 2.0 Access Token", out)
        self.assertNotIn("wrong-token-xyz", out)

    def test_blank_account_refuses_to_start(self):
        self.write_config(account_username="")
        code, out = self.run_tool("--publish")
        self.assertEqual(code, 2, out)
        self.assertIn("'account_username' is empty", out)
        self.assertEqual(self.fake.calls, [])

    def test_missing_video_link(self):
        out = io.StringIO()
        argv = ["--config", self.config, "--state-dir", self.state, "--graph-base", self.fake.base]
        with contextlib.redirect_stdout(out):
            code = post_reel.main(argv)
        self.assertEqual(code, 2, out.getvalue())
        self.assertIn("no video", out.getvalue())

    def test_shipped_post_json_is_valid_but_needs_an_account(self):
        cfg_path = os.path.join(os.path.dirname(os.path.abspath(post_reel.__file__)), "post.json")
        with open(cfg_path, encoding="utf-8") as f:
            cfg = json.load(f)
        self.assertEqual(cfg["expected_size_bytes"], 299378366)
        self.assertNotIn("video_url", cfg)  # the link must stay out of this public repo
        self.assertLessEqual(len(cfg["caption"]), 2200)
        self.assertIn(cfg["duplicate_marker"], cfg["caption"])


if __name__ == "__main__":
    unittest.main()
