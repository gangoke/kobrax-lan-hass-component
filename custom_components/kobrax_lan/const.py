from datetime import timedelta

NAME = "Kobra X"
DOMAIN = "kobrax_lan"
MANUFACTURER = "Anycubic"

CONF_HOST = "host"
CONF_PRINTER_NAME = "printer_name"

DEFAULT_HOST = "localhost:7125"
DEFAULT_PRINTER_NAME = "Anycubic Kobra X"

UPDATE_INTERVAL = timedelta(seconds=3)
UPDATE_CHECK_INTERVAL = timedelta(hours=1)

PLATFORMS = [
    "sensor",
    "binary_sensor",
    "light",
    "select",
    "button",
    "switch",
    "number",
    "camera",
    "image",
]
