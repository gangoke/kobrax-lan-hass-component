# Kobra X LAN for Home Assistant

Home Assistant integration for monitoring and controlling an Anycubic Kobra X through KX-Bridge.

This project was coded with AI assistance and should be reviewed before use in production.

Architecture:

- printer <-> [KX-Bridge](https://gitea.it-drui.de/viewit/KX-Bridge-Release) <-> this integration <-> Home Assistant

## Requirements

- Running and reachable [KX-Bridge-Release](https://gitea.it-drui.de/viewit/KX-Bridge-Release)
- Bridge endpoint accessible from Home Assistant at `http://<bridge-host>:7125`

## Installation

### Option 1: HACS

1. In HACS, add this repository as a custom repository (category: Integration):
   `https://github.com/gangoke/kobrax-lan-hass-component`
2. Install Kobra X LAN from HACS.
3. Restart Home Assistant.
4. Go to Settings -> Devices & Services -> Add Integration.
5. Search for Kobra X LAN.

### Option 2: Manual (local custom_components)

1. Copy the `kobrax_lan` folder into your Home Assistant `custom_components` directory:
   `<config>/custom_components/kobrax_lan`
3. Restart Home Assistant.
4. Add Kobra X LAN from Settings -> Devices & Services.

## Configuration

The config flow asks for:

- Host: KX-Bridge host and port (example: `192.168.1.50:7125`)
- Printer name: Friendly display name in Home Assistant

## Entity Overview

| Platform | Key Entities |
| --- | --- |
| Binary Sensor | Online, Printing, Light State |
| Sensor | State, Print State, Progress, Hotend Temperature, Target Hotend Temperature, Bed Temperature, Target Bed Temperature, Filename, Current Layer, Total Layers, Remaining Time, Print Duration, Skip Object Count, Skipped Object Count, Filament Mode, ACE Unit Count, Bridge Version, Latest Available Version, Slot 1..Slot 19, ACE 1..4 Dryer Status, ACE 1..4 Dryer Humidity, ACE 1..4 Dryer Current Temperature, ACE 1..4 Dryer Target Temperature, ACE 1..4 Dryer Remaining Time |
| Button | Pause Print, Resume Print, Cancel Print, Connect Bridge, Disconnect Bridge, Refresh Skip State, Apply Update (KX-Bridge) |
| Switch | ACE 1..4 Auto Fill, ACE 1..4 Dryer |
| Number | ACE 1..4 Dryer Target Temperature, ACE 1..4 Dryer Duration |
| Select | Print speed |
| Light | Printer light |
| Camera | Printer camera |
| Image | G-code thumbnail |

Slot and ACE entities are pre-created and automatically enabled/disabled based on detected slot mode and ACE unit count from KX-Bridge.

## Notes

- This integration communicates with KX-Bridge HTTP endpoints and does not connect directly to the printer.
- Keep KX-Bridge and Home Assistant on a trusted local network.
- Camera streaming prefers the bridge H.264 endpoint (`/api/camera/h264`, MPEG-TS passthrough) on newer bridge releases, with RTSP/MJPEG fallback for older releases.
- Native WebRTC is not implemented. For WebRTC in Home Assistant, point `go2rtc` (or another WebRTC-capable add-on) to the camera source you prefer (H.264 bridge endpoint or RTSP).
