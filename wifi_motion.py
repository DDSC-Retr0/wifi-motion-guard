#!/usr/bin/env python3
"""
wifi_motion.py — Passive WiFi Motion Detector
================================================
Detects motion by monitoring RSSI fluctuations across WiFi access points.
Logs events and writes live data to data/live.json for the dashboard.

Usage:
    sudo python3 wifi_motion.py --interface wlan0 --threshold 8

Requirements:
    pip install -r requirements.txt
"""

import subprocess
import re
import time
import json
import os
import argparse
import logging
import statistics
from datetime import datetime
from pathlib import Path

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("motion_log.txt"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
LIVE_FILE = DATA_DIR / "live.json"
EVENTS_FILE = DATA_DIR / "events.json"

BASELINE_WINDOW = 30        # seconds of readings to establish idle baseline
COOLDOWN_SECS   = 5         # minimum seconds between consecutive motion events
SAMPLE_RATE_HZ  = 10        # target samples per second

# ── RSSI Readers ─────────────────────────────────────────────────────────────

def read_rssi_iwconfig(interface: str) -> float | None:
    """Read RSSI via iwconfig (Linux, requires wireless-tools)."""
    try:
        out = subprocess.check_output(
            ["iwconfig", interface],
            stderr=subprocess.DEVNULL
        ).decode()
        match = re.search(r"Signal level=(-\d+)\s*dBm", out)
        if match:
            return float(match.group(1))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def read_rssi_iw(interface: str) -> float | None:
    """Read RSSI via `iw dev` (more modern, Linux)."""
    try:
        out = subprocess.check_output(
            ["iw", "dev", interface, "link"],
            stderr=subprocess.DEVNULL
        ).decode()
        match = re.search(r"signal:\s*(-\d+)\s*dBm", out)
        if match:
            return float(match.group(1))
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def read_rssi_mock(interface: str) -> float:
    """Simulated RSSI for testing without hardware."""
    import math, random
    t = time.time()
    base = -62
    noise = random.gauss(0, 1.5)
    # occasional motion-like drop
    motion = -15 * max(0, math.sin(t / 20) ** 8)
    return base + noise + motion


def get_rssi(interface: str, mock: bool = False) -> float | None:
    if mock:
        return read_rssi_mock(interface)
    val = read_rssi_iwconfig(interface)
    if val is None:
        val = read_rssi_iw(interface)
    return val


# ── Motion Detector ──────────────────────────────────────────────────────────

class MotionDetector:
    def __init__(self, interface: str, threshold_db: float, mock: bool = False):
        self.interface   = interface
        self.threshold   = threshold_db
        self.mock        = mock
        self.history     : list[float] = []
        self.events      : list[dict]  = []
        self.last_trigger: float       = 0
        self.in_motion   : bool        = False
        self.total_events: int         = 0

    @property
    def baseline(self) -> float | None:
        if len(self.history) < 5:
            return None
        return statistics.mean(self.history[-BASELINE_WINDOW * SAMPLE_RATE_HZ:])

    def tick(self):
        rssi = get_rssi(self.interface, self.mock)
        if rssi is None:
            log.warning("Could not read RSSI from %s", self.interface)
            return

        self.history.append(rssi)
        if len(self.history) > BASELINE_WINDOW * SAMPLE_RATE_HZ * 2:
            self.history.pop(0)

        baseline = self.baseline
        if baseline is None:
            return

        deviation = abs(rssi - baseline)
        now = time.time()

        # Variance over last 10 samples
        recent = self.history[-10:]
        variance = max(recent) - min(recent) if len(recent) >= 2 else 0

        motion_detected = (
            deviation >= self.threshold or
            variance  >= self.threshold * 1.2
        )

        if motion_detected and not self.in_motion and (now - self.last_trigger) > COOLDOWN_SECS:
            self.in_motion    = True
            self.last_trigger = now
            self.total_events += 1
            event = {
                "id":        self.total_events,
                "timestamp": datetime.now().isoformat(),
                "rssi":      rssi,
                "baseline":  round(baseline, 2),
                "deviation": round(deviation, 2),
                "variance":  round(variance, 2),
                "zone":      "Living Room",   # TODO: map to floor plan zone
            }
            self.events.append(event)
            if len(self.events) > 200:
                self.events.pop(0)
            log.info("🚨 MOTION DETECTED | RSSI %.1f dBm | Δ%.1f dB | Var %.1f dB",
                     rssi, deviation, variance)
            self._save_events()

        elif not motion_detected and self.in_motion:
            self.in_motion = False
            log.info("✓  Motion ended")

        self._write_live(rssi, baseline, deviation, variance, motion_detected)

    def _write_live(self, rssi, baseline, deviation, variance, motion):
        payload = {
            "timestamp":     datetime.now().isoformat(),
            "rssi":          rssi,
            "baseline":      round(baseline, 2),
            "deviation":     round(deviation, 2),
            "variance":      round(variance, 2),
            "in_motion":     motion,
            "total_events":  self.total_events,
            "history_tail":  self.history[-50:],
        }
        try:
            with open(LIVE_FILE, "w") as f:
                json.dump(payload, f)
        except OSError as e:
            log.error("Could not write live data: %s", e)

    def _save_events(self):
        try:
            with open(EVENTS_FILE, "w") as f:
                json.dump(self.events, f, indent=2)
        except OSError as e:
            log.error("Could not save events: %s", e)


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="WiFi Motion Guard — passive RSSI detector")
    p.add_argument("--interface",  "-i", default="wlan0",     help="WiFi interface name")
    p.add_argument("--threshold",  "-t", type=float, default=8.0, help="Deviation threshold (dBm)")
    p.add_argument("--mock",       "-m", action="store_true",  help="Use simulated RSSI (no hardware needed)")
    p.add_argument("--rate",       "-r", type=float, default=10.0, help="Sample rate in Hz")
    return p.parse_args()


def main():
    args = parse_args()
    log.info("WiFi Motion Guard starting up")
    log.info("Interface : %s", args.interface)
    log.info("Threshold : %.1f dBm deviation", args.threshold)
    log.info("Rate      : %.1f Hz", args.rate)
    log.info("Mock mode : %s", args.mock)
    log.info("─" * 50)

    detector = MotionDetector(
        interface  = args.interface,
        threshold_db = args.threshold,
        mock       = args.mock,
    )

    interval = 1.0 / args.rate

    try:
        while True:
            t0 = time.time()
            detector.tick()
            elapsed = time.time() - t0
            sleep_for = max(0, interval - elapsed)
            time.sleep(sleep_for)
    except KeyboardInterrupt:
        log.info("Stopped. Total events detected: %d", detector.total_events)


if __name__ == "__main__":
    main()
