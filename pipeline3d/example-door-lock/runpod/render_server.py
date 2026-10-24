# Runs inside a Runpod GPU pod. Stdlib only.
# 1) installs Blender (BLENDER_URL) + ffmpeg/X libs, 2) accepts an upload of the .blend, 3) renders with OptiX,
# 4) encodes frames to MP4, 5) serves status and the result. Every request needs header X-Token == $RENDER_TOKEN.
import http.server, json, os, shutil, subprocess, threading, time

TOKEN = os.environ["RENDER_TOKEN"]
BLENDER_URL = os.environ["BLENDER_URL"]
FPS = os.environ.get("FPS", "30")
W = "/workspace"; os.makedirs(W, exist_ok=True)
BLEND, FRAMES, OUT, LOG = f"{W}/scene.blend", f"{W}/frames", f"{W}/render.mp4", f"{W}/render.log"
state = {"phase": "installing", "error": None, "started": None, "finished": None}

def sh(cmd):
    with open(LOG, "a") as lf:
        lf.write(f"\n$ {cmd}\n"); lf.flush()
        return subprocess.run(cmd, shell=True, stdout=lf, stderr=subprocess.STDOUT).returncode

def install():
    try:
        sh("apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg wget xz-utils libxi6 libxkbcommon0 "
           "libsm6 libxrender1 libgl1 libxxf86vm1 libxfixes3 libegl1 >/dev/null")
        if sh(f"wget -q -O /tmp/blender.tar.xz '{BLENDER_URL}' && mkdir -p /opt/blender && "
              f"tar -xf /tmp/blender.tar.xz -C /opt/blender --strip-components=1") != 0:
            raise RuntimeError("blender download failed")
        sh("/opt/blender/blender --version | head -1")
        state["phase"] = "ready"
    except Exception as e:
        state["phase"] = "error"; state["error"] = str(e)

def render():
    state["phase"] = "rendering"; state["started"] = time.time()
    shutil.rmtree(FRAMES, ignore_errors=True); os.makedirs(FRAMES)
    rc = sh(f"/opt/blender/blender -b {BLEND} -o {FRAMES}/f_ -F PNG -a -- --cycles-device OPTIX")
    n = len([f for f in os.listdir(FRAMES) if f.endswith('.png')])
    if rc != 0 or n == 0:
        state["phase"] = "error"; state["error"] = f"blender rc={rc}, frames={n}"; return
    state["phase"] = "encoding"
    rc = sh(f"ffmpeg -nostdin -y -framerate {FPS} -start_number 1 -i {FRAMES}/f_%04d.png -c:v libx264 -crf 14 "
            f"-preset slow -pix_fmt yuv420p -movflags +faststart {OUT}")
    state["phase"] = "done" if rc == 0 else "error"; state["finished"] = time.time()
    if rc != 0: state["error"] = f"ffmpeg rc={rc}"

class H(http.server.BaseHTTPRequestHandler):
    def _ok(self):
        if self.headers.get("X-Token") != TOKEN:
            self.send_response(403); self.end_headers(); return False
        return True
    def _json(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_GET(self):
        if not self._ok(): return
        if self.path == "/status":
            n = len([f for f in os.listdir(FRAMES) if f.endswith('.png')]) if os.path.isdir(FRAMES) else 0
            tail = open(LOG).read()[-600:] if os.path.exists(LOG) else ""
            return self._json({**state, "frames": n, "log_tail": tail})
        if self.path == "/result" and state["phase"] == "done":
            self.send_response(200); self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(os.path.getsize(OUT))); self.end_headers()
            with open(OUT, "rb") as f: shutil.copyfileobj(f, self.wfile)
            return
        self._json({"error": "not found or not ready"}, 404)
    def do_PUT(self):
        if not self._ok(): return
        if self.path != "/scene": return self._json({"error": "bad path"}, 404)
        n = int(self.headers["Content-Length"]); left = n
        with open(BLEND, "wb") as f:
            while left > 0:
                chunk = self.rfile.read(min(1 << 20, left)); f.write(chunk); left -= len(chunk)
        self._json({"received": n})
    def do_POST(self):
        if not self._ok(): return
        if self.path == "/start" and state["phase"] == "ready" and os.path.exists(BLEND):
            threading.Thread(target=render, daemon=True).start(); return self._json({"started": True})
        self._json({"error": f"cannot start in phase {state['phase']}"}, 409)
    def log_message(self, *a): pass

threading.Thread(target=install, daemon=True).start()
http.server.ThreadingHTTPServer(("0.0.0.0", 8000), H).serve_forever()
