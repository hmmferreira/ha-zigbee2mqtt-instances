#!/usr/bin/env python3
"""Generate extra Zigbee2MQTT app instances from the official stable app.

Downloads the official app definition from zigbee2mqtt/hassio-zigbee2mqtt and
writes one copy per instance number. Each copy runs the same released image
and version as the official app; only what must differ to run side by side is
changed (name, slug, default data_path, host port, links).

Standard library only. Output is deterministic, so re-running without an
upstream change produces no diff.

Usage: python3 scripts/sync.py [--upstream-ref master]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import urllib.request

UPSTREAM_REPO = "zigbee2mqtt/hassio-zigbee2mqtt"
UPSTREAM_DIR = "zigbee2mqtt"
THIS_REPO = "hmmferreira/ha-zigbee2mqtt-instances"
INSTANCES = (2, 3, 4)
EXPECTED_IMAGE = "ghcr.io/zigbee2mqtt/zigbee2mqtt-{arch}"
BINARY_FILES = ("icon.png", "logo.png")
TEXT_FILES = ("CHANGELOG.md", "DOCS.md")

ROOT = pathlib.Path(__file__).resolve().parent.parent


def fetch(ref: str, name: str) -> bytes:
    url = f"https://raw.githubusercontent.com/{UPSTREAM_REPO}/{ref}/{UPSTREAM_DIR}/{name}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read()


def check_upstream(cfg: dict) -> None:
    """Fail loudly if the upstream app changed shape in a way we don't handle."""
    problems = []
    if cfg.get("slug") != "zigbee2mqtt":
        problems.append(f"slug is {cfg.get('slug')!r}")
    if cfg.get("image") != EXPECTED_IMAGE:
        problems.append(f"image is {cfg.get('image')!r} (expected a prebuilt image)")
    if not cfg.get("version"):
        problems.append("no version")
    if "data_path" not in cfg.get("options", {}):
        problems.append("options.data_path missing")
    unknown_ports = set(cfg.get("ports", {})) - {"8485/tcp", "8099/tcp"}
    if unknown_ports:
        problems.append(f"new ports {sorted(unknown_ports)}: decide how to map them")
    if problems:
        sys.exit("Upstream app changed, refusing to generate:\n  - " + "\n  - ".join(problems))


def instance_config(upstream: dict, n: int) -> dict:
    cfg = json.loads(json.dumps(upstream))  # deep copy, keeps key order
    cfg["name"] = f"Zigbee2MQTT #{n}"
    cfg["slug"] = f"zigbee2mqtt_{n}"
    cfg["panel_title"] = f"Zigbee2MQTT #{n}"
    cfg["description"] = (
        f"Extra instance #{n} of the official stable Zigbee2MQTT app, "
        "for an additional Zigbee coordinator"
    )
    cfg["url"] = f"https://github.com/{THIS_REPO}/tree/main/zigbee2mqtt-{n}"
    # Separate data folder, or the instances would share configuration and database.
    cfg["options"]["data_path"] = f"/config/zigbee2mqtt_{n}"
    # The official app publishes the socat port on host port 8485; only one app can.
    cfg["ports"] = {port: None for port in cfg["ports"]}
    # Keys set to their Supervisor default; dropping them changes nothing and keeps the linter quiet.
    for key, default in (("boot", "auto"), ("startup", "application")):
        if cfg.get(key) == default:
            del cfg[key]
    return cfg


DOCS_PREAMBLE = """\
# Zigbee2MQTT #{n}

This is an **extra instance** of the official, stable Zigbee2MQTT app, so you can run
one Zigbee2MQTT per coordinator (for example one per floor, or one for a garage).
It runs the same released image and version as the official app
(`ghcr.io/zigbee2mqtt/zigbee2mqtt-{{arch}}`, version `{version}`).

## Before you start

- **Use a unique MQTT base topic.** Set `mqtt.base_topic` in this instance's
  `configuration.yaml` (or in the app options) to something other than
  `zigbee2mqtt`, e.g. `zigbee2mqtt_{n}`. Two instances on the same base topic
  will fight over the same devices.
- **One coordinator per instance.** Point `serial.port` at the coordinator for
  this network (USB path, or `tcp://<ip>:<port>` for a network coordinator).
- **Data lives in `/config/zigbee2mqtt_{n}`** by default (the `data_path` option),
  separate from the official app's `/config/zigbee2mqtt`.
- **Different Zigbee channel** from your other networks helps avoid interference.
- The socat port (8485) is not published on the host. If you use socat, map a
  free host port in the app's Network settings.

## Moving an existing network to this instance

Stop the old Zigbee2MQTT first (only one program may talk to a coordinator), then
copy `configuration.yaml`, `database.db` and `coordinator_backup.json` into this
instance's data folder before the first start. Keep the same `base_topic` and
the Home Assistant entities stay the same. No re-pairing is needed.

---

The rest of this page is the official app's documentation.

"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--upstream-ref", default="master")
    args = parser.parse_args()

    upstream = json.loads(fetch(args.upstream_ref, "config.json"))
    check_upstream(upstream)
    blobs = {name: fetch(args.upstream_ref, name) for name in BINARY_FILES + TEXT_FILES}

    for n in INSTANCES:
        out = ROOT / f"zigbee2mqtt-{n}"
        out.mkdir(exist_ok=True)
        cfg = instance_config(upstream, n)
        (out / "config.json").write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n")
        for name in BINARY_FILES:
            (out / name).write_bytes(blobs[name])
        (out / "CHANGELOG.md").write_bytes(blobs["CHANGELOG.md"])
        docs = DOCS_PREAMBLE.format(n=n, version=upstream["version"]) + blobs["DOCS.md"].decode()
        (out / "DOCS.md").write_text(docs)
        (out / "README.md").write_text(
            f"# Zigbee2MQTT #{n}\n\n"
            f"Extra instance of the official stable Zigbee2MQTT app, version `{upstream['version']}`.\n"
            "See [DOCS.md](DOCS.md).\n"
        )

    (ROOT / "UPSTREAM_VERSION").write_text(upstream["version"] + "\n")
    print(upstream["version"])


if __name__ == "__main__":
    main()
