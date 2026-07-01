import json

import os

import signal

import sys

import threading

from datetime import datetime

from pathlib import Path



import paho.mqtt.client as mqtt

import requests

from dotenv import load_dotenv



from logging_config import setup_logging

from signal_cache import CachedSignalValue

from signal_cache import SignalValueCache

from snapshot import post_snapshot



load_dotenv(Path(__file__).resolve().parent / ".env")



logger = setup_logging()



BASE_URL = os.getenv("BASE_URL")

MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP")

MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))

EMAIL = os.getenv("EMAIL")

PASSWORD = os.getenv("PASSWORD")

TOPIC = os.getenv("TOPIC")

SNAPSHOT_INTERVAL_SECONDS = float(os.getenv("SNAPSHOT_INTERVAL_SECONDS", "2"))



REQUIRED_ENV_VARS = (

    "BASE_URL",

    "MQTT_BROKER_IP",

    "EMAIL",

    "PASSWORD",

    "TOPIC",

)



HEADERS_LOCK = threading.Lock()

HEADERS: dict[str, str] = {}



signal_cache = SignalValueCache()

tag_map: dict[str, dict] = {}

_stop_event = threading.Event()

_poster_thread: threading.Thread | None = None





def require_env():

    missing = [name for name in REQUIRED_ENV_VARS if not os.getenv(name)]

    if missing:

        logger.error("Missing required environment variables: %s", ", ".join(missing))

        logger.error(

            "Create a .env file in this directory or set variables before starting."

        )

        sys.exit(1)





def get_headers() -> dict[str, str]:

    with HEADERS_LOCK:

        return dict(HEADERS)





def refresh_headers() -> None:

    global HEADERS



    logger.info("Refreshing backend authentication token")



    response = requests.post(

        f"{BASE_URL}/auth/login",

        json={

            "email": EMAIL,

            "password": PASSWORD,

        },

        timeout=30,

    )

    response.raise_for_status()



    with HEADERS_LOCK:

        HEADERS = {

            "Authorization": f"Bearer {response.json()['access_token']}",

        }



    logger.info("Authentication token refreshed")





def login():

    logger.info("Authenticating with backend at %s", BASE_URL)

    refresh_headers()

    logger.info("Authentication successful")





def normalize_wincc_tag(item_id: str) -> str:

    return item_id.replace(

        "S7HMI030.WinCC.SUN_POLY2_SRV::",

        "S7HMI030.WinCC.",

    )





def load_signal_catalog() -> dict[str, dict]:

    logger.info("Fetching signal catalog from %s", BASE_URL)



    response = requests.get(

        f"{BASE_URL}/signal-catalog?limit=104",

        headers=get_headers(),

        timeout=30,

    )

    response.raise_for_status()



    catalog = response.json()

    logger.info("Loaded %d signals from catalog", len(catalog))



    catalog_map = {}

    for signal in catalog:

        catalog_map[signal["wincc_tag"]] = {

            "id": signal["id"],

            "factor": signal["factor"],

        }



    return catalog_map





def load_cache_from_latest_timeseries(catalog_map: dict[str, dict]) -> int:

    logger.info("Loading latest signal values from %s", BASE_URL)



    response = requests.get(

        f"{BASE_URL}/signal-timeseries/latest",

        headers=get_headers(),

        timeout=60,

    )

    response.raise_for_status()



    latest_values = response.json()

    cache_values: dict[str, CachedSignalValue] = {}



    for row in latest_values:

        wincc_tag = row.get("wincc_tag")

        if not wincc_tag or wincc_tag not in catalog_map:

            continue



        timestamp = parse_message_timestamp(row.get("timestamp"))

        cache_values[wincc_tag] = CachedSignalValue(

            value_raw=float(row["value_raw"]),

            value_scaled=float(row["value_scaled"]),

            quality=row.get("quality") or "GOOD",

            updated_at=timestamp,

        )



    loaded_count = signal_cache.initialize(cache_values)

    logger.info(

        "Signal cache initialized | loaded=%d | catalog=%d | api_rows=%d",

        loaded_count,

        len(catalog_map),

        len(latest_values),

    )



    return loaded_count





def parse_message_timestamp(raw_timestamp) -> datetime:

    if isinstance(raw_timestamp, str) and raw_timestamp:

        try:

            return datetime.fromisoformat(raw_timestamp.replace("Z", "+00:00"))

        except ValueError:

            pass



    return datetime.utcnow()





def on_message(client, userdata, msg):

    try:

        payload = json.loads(msg.payload.decode())



        item_id = payload.get("itemID")

        timestamp = payload.get("timestamp")

        value = payload.get("value")

        quality = payload.get("quality")



        if not item_id:

            logger.warning(

                "Skipping message without itemID. topic=%s",

                msg.topic,

            )

            return



        item_id = normalize_wincc_tag(item_id)



        if item_id not in tag_map:

            logger.warning(

                "Unknown tag. topic=%s tag=%s",

                msg.topic,

                item_id,

            )

            return



        try:

            raw_value = float(value)

        except (ValueError, TypeError):

            logger.warning(

                "Invalid numeric value. topic=%s value=%s",

                msg.topic,

                value,

            )

            return



        factor = tag_map[item_id]["factor"]

        scaled_value = raw_value * factor

        updated_at = parse_message_timestamp(timestamp)



        signal_cache.update(

            wincc_tag=item_id,

            value_raw=raw_value,

            value_scaled=scaled_value,

            quality=quality,

            updated_at=updated_at,

        )



        logger.debug(

            "Cache updated | tag=%s raw=%s scaled=%s cached_signals=%d",

            item_id,

            raw_value,

            scaled_value,

            signal_cache.count(),

        )



    except json.JSONDecodeError:

        logger.exception(

            "Invalid JSON payload on topic=%s",

            msg.topic,

        )



    except Exception:

        logger.exception(

            "MQTT callback error on topic=%s",

            msg.topic,

        )





def on_connect(client, userdata, flags, rc, properties=None):

    if rc == 0:

        logger.info("Connected to MQTT broker (rc=%s)", rc)

        client.subscribe(TOPIC, qos=1)

        logger.info("Subscribed to topic=%s qos=1", TOPIC)

    else:

        logger.error("MQTT connection failed (rc=%s)", rc)





def on_disconnect(client, userdata, rc, properties=None):

    logger.warning("Disconnected from MQTT broker (rc=%s)", rc)





def snapshot_poster_loop() -> None:

    logger.info(

        "Snapshot poster started | interval=%ss | posts only when cache changed",

        SNAPSHOT_INTERVAL_SECONDS,

    )



    while not _stop_event.wait(SNAPSHOT_INTERVAL_SECONDS):

        if not signal_cache.is_dirty():

            logger.debug("Skipping snapshot — no new MQTT updates since last post")

            continue



        if signal_cache.count() == 0:

            logger.debug("Skipping snapshot — cache is empty")

            continue



        success = post_snapshot(

            cache=signal_cache,

            tag_map=tag_map,

            base_url=BASE_URL,

            get_headers=get_headers,

            refresh_headers=refresh_headers,

        )



        if success:

            signal_cache.clear_dirty()





def start_snapshot_poster() -> threading.Thread:

    global _poster_thread



    _stop_event.clear()

    _poster_thread = threading.Thread(

        target=snapshot_poster_loop,

        name="snapshot-poster",

        daemon=True,

    )

    _poster_thread.start()

    return _poster_thread





def shutdown(mqtt_client: mqtt.Client | None = None) -> None:

    logger.info("Shutting down subscriber...")



    _stop_event.set()

    if _poster_thread is not None and _poster_thread.is_alive():

        _poster_thread.join(timeout=SNAPSHOT_INTERVAL_SECONDS + 2)



    if mqtt_client is not None:

        try:

            mqtt_client.disconnect()

            logger.info("Disconnected from MQTT broker")

        except Exception:

            logger.exception("Error while disconnecting MQTT client")



    logger.info("Subscriber stopped successfully")





def main():

    global tag_map



    mqtt_client = None



    try:

        logger.info("Starting MQTT subscriber")

        require_env()

        logger.info("Log directory: %s", os.getenv("LOG_DIR", "logs"))

        logger.info("MQTT broker: %s:%s", MQTT_BROKER_IP, MQTT_BROKER_PORT)

        logger.info("Subscribe topic: %s", TOPIC)

        logger.info(

            "Snapshot mode: post every %ss when cache has new MQTT updates",

            SNAPSHOT_INTERVAL_SECONDS,

        )



        login()

        tag_map = load_signal_catalog()

        load_cache_from_latest_timeseries(tag_map)

        start_snapshot_poster()



        mqtt_client = mqtt.Client()

        mqtt_client.on_connect = on_connect

        mqtt_client.on_disconnect = on_disconnect

        mqtt_client.on_message = on_message



        logger.info("Connecting to MQTT broker %s:%s", MQTT_BROKER_IP, MQTT_BROKER_PORT)



        mqtt_client.connect(

            MQTT_BROKER_IP,

            MQTT_BROKER_PORT,

            60,

        )



        def handle_exit_signal(signum, frame):

            raise KeyboardInterrupt



        signal.signal(signal.SIGINT, handle_exit_signal)

        if hasattr(signal, "SIGTERM"):

            signal.signal(signal.SIGTERM, handle_exit_signal)



        mqtt_client.loop_forever()



    except KeyboardInterrupt:

        logger.info("Shutdown requested (Ctrl+C)")

    finally:

        shutdown(mqtt_client)





if __name__ == "__main__":

    try:

        main()

    except KeyboardInterrupt:

        logger.info("Shutdown requested (Ctrl+C)")

    sys.exit(0)


