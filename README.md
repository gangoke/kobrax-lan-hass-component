# Kobra X Home Assistant Component

Home Assistant HACS integration for controlling and monitoring an Anycubic Kobra X through KX-Bridge.

Architecture:

- printer <-> KX-Bridge-Release <-> this integration <-> Home Assistant

## Features

- Auto-discovered status from KX-Bridge `/api/state`
- Core printer sensors (state, temperatures, progress, file, layer/time data)
- Light control
- Print speed mode selection
- Service calls for print speed mode and target temperatures (nozzle/bed)
- Printer action buttons (pause, resume, cancel)
- Camera stream entity using the printer RTSP URL from KX-Bridge, with bridge MJPEG proxy fallback
- Camera snapshot fallback using `/api/camera/snapshot`
- Card-compat alias entities for `kobrax-lan-card` (for example `job_state`, `job_progress`, `printer_online`, `target_nozzle_temperature`)

## Prerequisites

1. KX-Bridge must be running and reachable from Home Assistant.
2. Verify KX-Bridge is accessible at `http://<bridge-host>:7125`.

## Installation (HACS)

1. Add this repository as a custom repository in HACS with category `Integration`.
2. Install the integration.
3. Restart Home Assistant.
4. Add integration `Kobra X` from Settings -> Devices & Services.

## Configuration

The config flow asks for:

- Host: KX-Bridge host and port (example: `192.168.1.50:7125`)
- Printer name: Friendly display name

## Notes

- This integration talks to KX-Bridge HTTP endpoints and does not connect directly to the printer.
- Keep KX-Bridge and Home Assistant on the same trusted network.
- Native WebRTC is not implemented in this integration. If you want WebRTC in Home Assistant, point `go2rtc` or a WebRTC-capable HA add-on at the camera entity's RTSP source.

## Frontend Card Source

The source-of-truth for the Kobrax LAN card is in:

- custom_components/kobrax_lan/frontend_panel

Build output from that folder creates:

- dist/kobrax-lan-card.js

The separate `kobrax-lan-hass-card` repository is the HACS distribution repo for the built artifact.
