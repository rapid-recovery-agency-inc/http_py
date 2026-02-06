MIN_LATITUDE = -90.0
MAX_LATITUDE = 90.0
MIN_LONGITUDE = -180.0
MAX_LONGITUDE = 180.0


def check_latitude(value: float) -> None:
    if value < MIN_LATITUDE or value > MAX_LATITUDE:
        msg = "Latitude must be between -90 and 90."
        raise ValueError(msg)


def check_longitude(value: float) -> None:
    if value < MIN_LONGITUDE or value > MAX_LONGITUDE:
        msg = "Longitude must be between -180 and 180."
        raise ValueError(msg)
