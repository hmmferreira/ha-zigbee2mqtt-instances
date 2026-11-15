# Zigbee2MQTT extra instances for Home Assistant

Run **more than one Zigbee2MQTT** on Home Assistant OS, each on the **official stable release**, so you can use one coordinator per network (per floor, an outbuilding, a garage…).

Home Assistant installs each app only once, and Zigbee2MQTT handles exactly one coordinator per instance. The usual workaround is the *Edge* app, which follows development builds and gives you only one extra instance. This repository gives you up to three extra instances of the **stable** app instead:

| App | Slug | Default data folder |
|---|---|---|
| Zigbee2MQTT #2 | `zigbee2mqtt_2` | `/config/zigbee2mqtt_2` |
| Zigbee2MQTT #3 | `zigbee2mqtt_3` | `/config/zigbee2mqtt_3` |
| Zigbee2MQTT #4 | `zigbee2mqtt_4` | `/config/zigbee2mqtt_4` |

Keep the official Zigbee2MQTT app for your first network and add these for the others.

## How it works

The official app doesn't build anything: it runs Zigbee2MQTT's published image `ghcr.io/zigbee2mqtt/zigbee2mqtt-{arch}`. Each app here is a copy of the official app definition with the **same image and version**. Only what has to differ to run side by side is changed: name, slug, default data folder, and the host port mapping (see [NOTICE](NOTICE)).

A GitHub Action checks the official app every 6 hours. When a new stable version is released, it regenerates the copies and commits, and Home Assistant offers the update like any other app. It refuses to update, and the workflow fails, if the official app changes in a way the generator doesn't understand (for example, a new port or a switch away from a prebuilt image).

## Install

1. Settings → Apps (Add-ons) → App store → ⋮ → **Repositories** → add
   `https://github.com/hmmferreira/ha-zigbee2mqtt-instances`
2. Install **Zigbee2MQTT #2**.
3. In its configuration, set at least:
   - `serial.port`: this network's coordinator (e.g. `tcp://192.168.1.50:6638` or `/dev/serial/by-id/...`)
   - `serial.adapter`: e.g. `zstack`, `ember`
   - `mqtt.base_topic`: **unique per instance**, e.g. `zigbee2mqtt_2`
4. Start it. It appears in the sidebar as *Zigbee2MQTT #2*.

Each instance's own documentation tab explains how to move an existing network (from Docker, another machine or the Edge app) without re-pairing.

## Things to know

- **One coordinator per instance, one instance per coordinator.**
- **Unique `base_topic` per instance.** Two instances on the same topic will interfere.
- Use **different Zigbee channels** for networks that are close to each other.
- Zigbee groups and direct bindings only work within one network. Use Home Assistant automations to link devices across networks.
- Each instance uses roughly 150–250 MB of RAM.

## Development

`python3 scripts/sync.py` regenerates `zigbee2mqtt-*/` from the official app. Don't edit the generated folders by hand; change the script instead.

## License

Apache License 2.0, the same as the official app this is generated from. Not affiliated with the Zigbee2MQTT project. See [NOTICE](NOTICE).
