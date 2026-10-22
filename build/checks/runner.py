"""What the audit needs around the checks: the server, the rebuild and the report."""
import functools
import http.server
import os
import subprocess
import sys
import threading

from .context import GENERATED, PAGES, ROOT


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    # Keep-alive. The HTTP/1.0 default makes Chromium wait on a half-closed
    # connection now and then, which shows up as a resource that timed out
    # against a server that is working perfectly well.
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):
        pass

    def copyfile(self, source, outputfile):
        # A page that closes early (a reload, or the browser quitting) aborts
        # the socket mid-file; that is not an audit failure, and the traceback
        # it prints from the serving thread looks like one.
        try:
            super().copyfile(source, outputfile)
        except (ConnectionError, OSError):
            pass


def serve():
    handler = functools.partial(QuietHandler, directory=ROOT)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    httpd.daemon_threads = True
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def rebuild():
    """Run the generator and return the generated files whose bytes changed."""
    before = {name: open(os.path.join(ROOT, name), "rb").read() for name in GENERATED}
    result = subprocess.run(
        [sys.executable, os.path.join(ROOT, "build", "build.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return None, result
    after = {name: open(os.path.join(ROOT, name), "rb").read() for name in GENERATED}
    return [name for name in GENERATED if before[name] != after[name]], result


def load_pages():
    texts = {}
    for page in PAGES:
        path = os.path.join(ROOT, page)
        if not os.path.exists(path):
            raise SystemExit(f"missing generated page: {page}")
        with open(path, encoding="utf-8") as f:
            texts[page] = f.read()
    return texts


class Audit:
    """One named, timed result per check, so a failure names itself.

    `--only` is matched by the runner before a check is given any work.
    """

    def __init__(self, only=None):
        self.only = [part.strip() for part in (only or "").split(",") if part.strip()]
        self.results = []
        self.skipped = []
        self.notes = []

    def wants(self, name):
        return not self.only or any(part in name for part in self.only)

    def add(self, name, problems, proves, seconds=None):
        problems = list(problems)
        self.results.append(
            {"name": name, "problems": problems, "ok": proves, "seconds": seconds or 0.0}
        )
        if not problems:
            timing = f" ({seconds * 1000:.0f}ms)" if seconds else ""
            print(f"  ok    {name}{timing}")
        return problems

    def skip(self, name, reason=None):
        self.skipped.append(name)
        if reason:
            print(f"  skip  {name}: {reason}")

    def note(self, text):
        self.notes.append(text)

    def slowest(self, count=3):
        finished = [result for result in self.results if result["seconds"]]
        return sorted(finished, key=lambda result: -result["seconds"])[:count]

    def failed(self):
        return [problem for result in self.results for problem in result["problems"]]
