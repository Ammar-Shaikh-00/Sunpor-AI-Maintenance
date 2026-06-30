import json
import os
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from signal_definitions import SIGNAL_GENERATORS

load_dotenv(Path(__file__).resolve().parent / ".env")

MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
TOPIC = os.getenv("TOPIC", "EX10/live")
PUBLISH_INTERVAL_SECONDS = float(os.getenv("PUBLISH_INTERVAL_SECONDS", "2"))
COV_SIGNALS_PER_TICK = int(os.getenv("COV_SIGNALS_PER_TICK", "5"))
QUALITY = os.getenv("QUALITY", "GOOD")
USE_POLY2_PREFIX = os.getenv("USE_POLY2_PREFIX", "false").lower() == "true"


def format_item_id(wincc_tag: str) -> str:
    if not USE_POLY2_PREFIX:
        return wincc_tag

    return wincc_tag.replace(
        "S7HMI030.WinCC.",
        "S7HMI030.WinCC.SUN_POLY2_SRV::",
    )


def build_payload(item_id: str, value: float) -> dict:
    return {
        "itemID": format_item_id(item_id),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "value": value,
        "quality": QUALITY,
    }


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[MQTT] Connected to {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    else:
        print(f"[MQTT] Connection failed (rc={rc})")


def on_disconnect(client, userdata, rc, properties=None):
    print(f"[MQTT] Disconnected (rc={rc})")


def pick_cov_tags(all_tags: list[str], count: int, tick: int) -> list[str]:
    if count >= len(all_tags):
        return all_tags

    rng = random.Random(tick)
    return rng.sample(all_tags, count)


def main():
    if not SIGNAL_GENERATORS:
        print("[ERROR] No signal definitions configured")
        sys.exit(1)

    print("SUNPOR MQTT simulator")
    print(f"  broker   : {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
    print(f"  topic    : {TOPIC}")
    print(f"  interval : {PUBLISH_INTERVAL_SECONDS}s")
    print(f"  cov/tick : {COV_SIGNALS_PER_TICK} of {len(SIGNAL_GENERATORS)} signals")
    print(f"  format   : itemID + timestamp + value + quality (subscriber-compatible)")

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    client.loop_start()

    all_tags = list(SIGNAL_GENERATORS.keys())
    tick = 0

    try:
        while True:
            tick += 1
            changed_tags = pick_cov_tags(all_tags, COV_SIGNALS_PER_TICK, tick)

            for tag in changed_tags:
                value = SIGNAL_GENERATORS[tag](tick)
                payload = build_payload(tag, value)
                result = client.publish(
                    TOPIC,
                    json.dumps(payload),
                    qos=1,
                )

                print(
                    f"[PUBLISH] tick={tick} rc={result.rc} tag={tag} value={value}"
                )

            time.sleep(PUBLISH_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[MQTT] Stopping simulator...")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
