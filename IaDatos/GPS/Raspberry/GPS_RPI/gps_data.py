class GPSData:

    def __init__(
        self,
        lat=0.0,
        lon=0.0,
        alt=0.0,
        speed=0.0,
        accuracy=0.0,
        heading=0.0,
        packet=0,
        valid=False,
    ):

        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.speed = speed
        self.accuracy = accuracy
        self.heading = heading
        self.packet = packet
        self.valid = valid

    @classmethod
    def from_json(cls, datos):

        return cls(
            lat=datos.get("lat", 0.0),
            lon=datos.get("lon", 0.0),
            alt=datos.get("alt", 0.0),
            speed=datos.get("speed", 0.0),
            accuracy=datos.get("accuracy", 0.0),
            heading=datos.get("heading", 0.0),
            packet=datos.get("packet", 0),
            valid=datos.get("valid", False),
        )