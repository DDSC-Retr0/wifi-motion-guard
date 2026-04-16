#  WiFi Motion Guard

> **Passive whole-home motion detection using WiFi signal disruption — no extra hardware required.**

![License](https://img.shields.io/badge/license-MIT-00e5ff?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10%2B-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20Raspberry%20Pi-lightgrey?style=flat-square)
![Status](https://img.shields.io/badge/status-active-39ff7e?style=flat-square)

---

## How It Works

When a person moves through a room, their body **absorbs and reflects** 2.4 GHz / 5 GHz radio waves. This causes tiny but measurable drops and fluctuations in the **RSSI (Received Signal Strength Indicator)** between your router and connected devices.

WiFi Motion Guard monitors these fluctuations in real time. When a deviation exceeds your configured threshold, a motion event is logged and displayed on the live dashboard.

```
Router ──── WiFi signal ────► Monitor device
                │
          Person walks by
                │
        Signal drops ~10 dBm
                │
           Motion detected

## Features

-  **Live dashboard** — real-time RSSI stream across 3 access points
-  **Interactive floor plan** — draw your house layout with room & wall tools, place AP nodes
-  **Zone grid map** — 24-zone heatmap showing signal disruption intensity per room
-  **Event log** — timestamped detection history
-  **Configurable thresholds** — sensitivity, sampling rate, cooldown, baseline window
-  **Python backend** — `wifi_motion.py` for real hardware detection
-  **Mock mode** — fully simulated for testing without a Raspberry Pi

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/DDSC-Retr0/wifi-motion-guard.git
cd wifi-motion-guard
```

### 2. Open the dashboard

Just open `index.html` in any browser — no server needed.

```bash
open index.html        # macOS
xdg-open index.html    # Linux
```

### 3. Run the Python sensor (optional, for real detection)

```bash
# Install dependencies
pip install -r requirements.txt

# Test with simulated RSSI (no hardware needed)
python3 wifi_motion.py --mock

# Run on real hardware (requires root for monitor mode)
sudo python3 wifi_motion.py --interface wlan0 --threshold 8
```

---

## Hardware Requirements

| Component | Details |
|-----------|---------|
| **WiFi adapter** | Any adapter supporting monitor mode (e.g. TP-Link TL-WN722N) |
| **OS** | Linux (Ubuntu, Raspberry Pi OS) |
| **Tools** | `wireless-tools` (`iwconfig`) or `iw` |
| **Optional** | Raspberry Pi 3/4 for dedicated 24/7 sensor |

### Recommended setup

```
[Router] ←────────────────────────────────────→ [Monitor Pi]
                    WiFi signal
                   (2.4 / 5 GHz)
```

Place your Raspberry Pi (or Linux laptop) somewhere central. The more line-of-sight paths that cross monitored rooms, the better coverage you get.

---

## Advanced: CSI Mode

For higher accuracy, use **Channel State Information (CSI)** instead of RSSI. CSI reads the full channel matrix per subcarrier — much richer signal than a single RSSI number.

| Tool | Hardware |
|------|----------|
| [nexmon_csi](https://github.com/seemoo-lab/nexmon_csi) | Raspberry Pi 3/4, Nexus 5 |
| [ESP32-CSI-Tool](https://github.com/StevenMHernandez/ESP32-CSI-Tool) | ESP32 |
| [PicoScenes](https://ps.zpj.io/) | Intel 5300, AX200 |
| [linux-80211n-csitool](https://dhalperi.github.io/linux-80211n-csitool/) | Intel 5300 |

---

## File Structure

```
wifi-motion-guard/
├── index.html          # Full dashboard (open in browser)
├── wifi_motion.py      # Python RSSI sensor backend
├── requirements.txt    # Python dependencies
├── data/
│   ├── live.json       # Written by backend, read by dashboard
│   └── events.json     # Persistent event log
└── README.md
```

---

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| **Dashboard** | Live RSSI chart, stats, AP signal bars, mini zone map |
| **Floor Plan** | Draw your house — rooms, walls, AP nodes. Motion heat overlaid live |
| **Zone Map** | 24-cell grid with colour-coded disruption intensity per zone |
| **Settings** | Threshold, sample rate, baseline window, feature toggles |

### Floor Plan Tools

| Tool | Use |
|------|-----|
| ⬛ Room | Click and drag to draw a room |
| — Wall | Click and drag to draw a wall |
| 📡 AP Node | Click to place a WiFi access point |
| 🏷 Label | Click to add a room name |

---

## Configuration

All settings are adjustable from the **Settings tab** in the UI, or via CLI flags:

```bash
python3 wifi_motion.py \
  --interface wlan0 \    # WiFi interface
  --threshold 8 \        # dBm deviation to trigger
  --rate 10 \            # samples per second
  --mock                 # use simulated signal
```

---

## Privacy

All processing happens **locally on your device**. No data is sent to any server. The dashboard reads from `data/live.json` written by the Python backend.

---

## Roadmap

- [ ] Multi-interface support (multiple adapters for triangulation)
- [ ] Zone-level motion localisation using RSSI gradient
- [ ] WebSocket live feed between Python backend and browser
- [ ] Mobile app companion
- [ ] Home Assistant / MQTT integration
- [ ] Notification webhooks (Telegram, Slack, email)

---

## License

MIT — free to use, modify, and distribute.

---

<p align="center">
  Built with passive RF sensing · No cameras · No microphones · Just WiFi
</p>
