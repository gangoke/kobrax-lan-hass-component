# Kobra X Home Assistant Component

Home Assistant HACS integration for controlling and monitoring an Anycubic Kobra X through KX-Bridge.

This project was coded with AI assistance and should be reviewed before use in production.

Architecture:

- printer <-> [KX-Bridge-Release](https://gitea.it-drui.de/viewit/KX-Bridge-Release) <-> this integration <-> Home Assistant

## Features

- Auto-discovered status from KX-Bridge `/api/state`
- Core printer sensors (state, temperatures, progress, file, layer/time data)
- Light control
- Print speed mode selection
- Printer action buttons (pause, resume, cancel, connect, disconnect)
- Camera stream entity using the printer RTSP URL from KX-Bridge, with bridge MJPEG proxy fallback
- Camera snapshot fallback using `/api/camera/snapshot`
- G-code thumbnail image entity from the active print job

## Available Entities

### Binary Sensors

- `Online`
- `Printing`
- `Light State`

### Sensors

- `State`
- `Print State`
- `Progress`
- `Hotend Temperature`
- `Target Hotend Temperature`
- `Bed Temperature`
- `Target Bed Temperature`
- `Filename`
- `Current Layer`
- `Total Layers`
- `Remaining Time`
- `Print Duration`
- `Filament Slot 1 Color` / `Filament Slot 1 Type`
- `Filament Slot 2 Color` / `Filament Slot 2 Type`
- `Filament Slot 3 Color` / `Filament Slot 3 Type`
- `Filament Slot 4 Color` / `Filament Slot 4 Type`

The filament slot entities are created from the AMS slot data reported by KX-Bridge. If the bridge does not report a slot count, the integration falls back to 4 slots.

### Buttons

- `Pause Print`
- `Resume Print`
- `Cancel Print`
- `Connect Bridge`
- `Disconnect Bridge`

### Select

- `Print Speed`

### Light

- `Light`

### Camera

- `Camera`

### Image

- `GCode Thumbnail`

## Prerequisites

1. [KX-Bridge-Release](https://gitea.it-drui.de/viewit/KX-Bridge-Release) must be running and reachable from Home Assistant.
2. Verify [KX-Bridge-Release](https://gitea.it-drui.de/viewit/KX-Bridge-Release) is accessible at `http://<bridge-host>:7125`.

## Installation (HACS)

1. Add this repository as a custom repository in HACS with category `Integration`.

   ```https://github.com/gangoke/kobrax-lan-hass-component```
   
2. Install the integration.
3. Restart Home Assistant.
4. Add integration `Kobra X LAN` from Settings -> Devices & Services.

## Configuration

The config flow asks for:

- Host: KX-Bridge host and port (example: `192.168.1.50:7125`)
- Printer name: Friendly display name

## Notes

- This integration talks to KX-Bridge HTTP endpoints and does not connect directly to the printer.
- Keep KX-Bridge and Home Assistant on the same trusted network.
- Native WebRTC is not implemented in this integration. If you want WebRTC in Home Assistant, point `go2rtc` or a WebRTC-capable HA add-on at the camera entity's RTSP source.
