#!/usr/bin/env python3
"""
Remote command runner — HTTP API server.
Runs on GitHub Actions runner, exposed via ngrok HTTP.

Endpoints:
  GET  /health              -> {"ok": true}
  POST /run                 -> {"cmd": "...", "cwd": "...", "timeout": 300} -> {"stdout", "stderr", "exit_code"}
  POST /upload              -> {"path": "/remote/file", "b64": "base64content"} -> {"ok", "size"}
  GET  /download?path=...   -> raw file bytes
  GET  /ls?path=...         -> {"entries": [{"name", "type", "size"}]}
  POST /mkdir               -> {"path": "..."} -> {"ok": true}
  POST /rm                  -> {"path": "..."} -> {"ok": true}

Auth: X-Api-Key header must match API_KEY env var.
"""
import os, sys, json, base64, subprocess, shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

API_KEY = os.environ.get("REMOTE_API_KEY", "hacx_remote_2024")
PORT = int(os.environ.get("REMOTE_PORT", "7860"))
WORK_DIR = os.environ.get("WORK_DIR", "/home/runner/work")

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, code, data, ctype="application/octet-stream"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _check_auth(self):
        key = self.headers.get("X-Api-Key", "")
        if key != API_KEY:
            self._send_json(401, {"error": "unauthorized"})
            return False
        return True

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except:
            return {}

    def log_message(self, fmt, *args):
        # quieter logging
        sys.stderr.write(f"[{self.client_address[0]}] {fmt % args}\n")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        if path == "/health":
            self._send_json(200, {"ok": True, "work_dir": WORK_DIR})
            return

        if not self._check_auth():
            return

        if path == "/download":
            fpath = qs.get("path", [""])[0]
            if not fpath or not os.path.isfile(fpath):
                self._send_json(404, {"error": "file not found"})
                return
            with open(fpath, "rb") as f:
                data = f.read()
            self._send_bytes(200, data)
            return

        if path == "/ls":
            dirpath = qs.get("path", [WORK_DIR])[0]
            if not os.path.isdir(dirpath):
                self._send_json(404, {"error": "dir not found"})
                return
            entries = []
            for name in sorted(os.listdir(dirpath)):
                full = os.path.join(dirpath, name)
                if os.path.isdir(full):
                    entries.append({"name": name, "type": "dir", "size": 0})
                else:
                    entries.append({"name": name, "type": "file", "size": os.path.getsize(full)})
            self._send_json(200, {"entries": entries, "path": dirpath})
            return

        self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if not self._check_auth():
            return
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == "/run":
            cmd = body.get("cmd", "")
            cwd = body.get("cwd", WORK_DIR)
            timeout = body.get("timeout", 300)
            env = os.environ.copy()
            extra_env = body.get("env", {})
            env.update(extra_env)
            if not cmd:
                self._send_json(400, {"error": "missing cmd"})
                return
            try:
                result = subprocess.run(
                    cmd, shell=True, cwd=cwd,
                    capture_output=True, text=True,
                    timeout=timeout, env=env,
                )
                self._send_json(200, {
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "exit_code": result.returncode,
                    "cmd": cmd,
                })
            except subprocess.TimeoutExpired:
                self._send_json(408, {"error": "timeout", "timeout": timeout, "cmd": cmd})
            except Exception as e:
                self._send_json(500, {"error": str(e), "cmd": cmd})
            return

        if path == "/upload":
            fpath = body.get("path", "")
            b64data = body.get("b64", "")
            if not fpath or not b64data:
                self._send_json(400, {"error": "missing path or b64"})
                return
            try:
                os.makedirs(os.path.dirname(fpath), exist_ok=True)
                data = base64.b64decode(b64data)
                with open(fpath, "wb") as f:
                    f.write(data)
                self._send_json(200, {"ok": True, "size": len(data), "path": fpath})
            except Exception as e:
                self._send_json(500, {"error": str(e)})
            return

        if path == "/mkdir":
            dirpath = body.get("path", "")
            if not dirpath:
                self._send_json(400, {"error": "missing path"})
                return
            os.makedirs(dirpath, exist_ok=True)
            self._send_json(200, {"ok": True, "path": dirpath})
            return

        if path == "/rm":
            rmpath = body.get("path", "")
            if not rmpath:
                self._send_json(400, {"error": "missing path"})
                return
            if os.path.isdir(rmpath):
                shutil.rmtree(rmpath)
            elif os.path.isfile(rmpath):
                os.remove(rmpath)
            else:
                self._send_json(404, {"error": "not found"})
                return
            self._send_json(200, {"ok": True, "path": rmpath})
            return

        self._send_json(404, {"error": "not found"})

def main():
    os.makedirs(WORK_DIR, exist_ok=True)
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Remote runner API on 0.0.0.0:{PORT}")
    print(f"Work dir: {WORK_DIR}")
    print(f"Auth key: {API_KEY}")
    server.serve_forever()

if __name__ == "__main__":
    main()
