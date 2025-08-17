# app.py
import threading, queue, time, json
from collections import deque
from flask import Flask, Response, send_from_directory, jsonify
import serial

SERIALS = [
    {"name": "up",   "port": "COM2", "baud": 9600},  # gemelo de COM1
    {"name": "down", "port": "COM4", "baud": 9600},  # gemelo de COM3
]

HIST_LEN = 300  # ~10 min a 2 s/lectura
app = Flask(__name__)

# Estado actual
state = {
    "up":   {"t": None, "h": None},
    "down": {"t": None, "h": None},
    "ts": None
}

# Historial por cuarto
history = {
    "up":   {"ts": deque(maxlen=HIST_LEN), "t": deque(maxlen=HIST_LEN), "h": deque(maxlen=HIST_LEN)},
    "down": {"ts": deque(maxlen=HIST_LEN), "t": deque(maxlen=HIST_LEN), "h": deque(maxlen=HIST_LEN)},
}

bus = queue.Queue(maxsize=400)

def _push_history(name, t_val=None, h_val=None):
    now = time.time()
    if t_val is not None:
        history[name]["ts"].append(now)
        history[name]["t"].append(float(t_val))
        # si solo llega T, replicamos timestamp para H para mantener largo parejo
        if len(history[name]["h"]) < len(history[name]["t"]):
            history[name]["h"].append(history[name]["h"][-1] if history[name]["h"] else None)
    if h_val is not None:
        # si llega H primero, también guardamos ts
        if len(history[name]["ts"]) == 0 or len(history[name]["h"]) == len(history[name]["ts"]):
            history[name]["ts"].append(now)
        history[name]["h"].append(float(h_val))
        if len(history[name]["t"]) < len(history[name]["h"]):
            history[name]["t"].append(history[name]["t"][-1] if history[name]["t"] else None)

def parse_line(name, line):
    # Formatos: UP:T:25.6 | UP:H:62.3 | DOWN:T:... | DOWN:H:...
    parts = line.strip().split(":")
    if len(parts) >= 3:
        kind = parts[1].upper()
        val = parts[2]
        if kind == "T":
            state[name]["t"] = val
            _push_history(name, t_val=val)
        elif kind == "H":
            state[name]["h"] = val
            _push_history(name, h_val=val)

def reader(name, port, baud):
    while True:
        try:
            with serial.Serial(port, baud, timeout=1) as ser:
                while True:
                    raw = ser.readline().decode(errors="ignore").strip()
                    if not raw:
                        continue
                    parse_line(name, raw)
                    state["ts"] = time.time()
                    try:
                        bus.put_nowait(json.dumps(state))
                    except queue.Full:
                        pass
        except Exception:
            time.sleep(1)  # reintenta si el COM aún no está

@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/stream")
def stream():
    def gen():
        yield f"data: {json.dumps(state)}\n\n"
        while True:
            yield f"data: {bus.get()}\n\n"
    return Response(gen(), mimetype="text/event-stream")

@app.route("/history")
def get_history():
    # devolvemos arrays simples (timestamps en ms para Chart.js)
    def pack(room):
        ts = list(history[room]["ts"])
        return {
            "ts": [int(x*1000) for x in ts],
            "t":  list(history[room]["t"]),
            "h":  list(history[room]["h"]),
        }
    return jsonify({"up": pack("up"), "down": pack("down")})

if __name__ == "__main__":
    for s in SERIALS:
        threading.Thread(target=reader, args=(s["name"], s["port"], s["baud"]), daemon=True).start()
    app.run(host="127.0.0.1", port=5000, debug=False)
