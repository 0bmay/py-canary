import json
import logging
import re
import sys

from canary.api import Api

LIVE_STREAM = True


def read_settings():
    with open("./canary_login.json") as openfile:
        # Reading from json file
        json_object = json.load(openfile)
        try:
            if json_object["token"] == "":
                json_object["token"] = None
        except KeyError:
            json_object["token"] = None
        return json_object


if __name__ == "__main__":

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    # set logging level

    settings = read_settings()

    if settings["username"] == "change me" or settings["password"] == "change me":
        print("Please change the login credentials from 'change me' to your info.")
        sys.exit(1)

    canary = Api(username=settings["username"], password=settings["password"])

    locations_by_id = {}
    readings_by_device_id = {}

    for location in canary.get_locations():
        location_id = location.location_id
        locations_by_id[location_id] = location

        for device in location.devices:
            logger.info(
                "device %s is a %s and is %s",
                device.name,
                device.device_type["name"],
                "online" if device.is_online else "offline",
            )
            if device.is_online:
                readings_by_device_id[device.device_id] = canary.get_latest_readings(
                    device.device_id
                )
                # below requires a new login as well, since there are new
                # cookies that need to be set.
                if LIVE_STREAM:
                    lss = canary.get_live_stream_session(device=device)
                    logger.info(
                        "device %s live stream session url = %s",
                        device.name,
                        re.sub(
                            r"watchlive/[0-9]+/[a-z0-9]+/",
                            "watchlive/--loc_id--/--hash--/",
                            lss.live_stream_url,
                        ),
                    )

    logger.info("Latest Readings by device...")
    for key in readings_by_device_id:
        for reading in readings_by_device_id[key]:
            # yes this loop is not really needed,
            # but to anonymize the device id's we need it
            for device in location.devices:
                if device.device_id == key:
                    logger.info(
                        "device %s - sensor: %s value: %s",
                        device.name,
                        reading.sensor_type.name,
                        reading.value,
                    )
