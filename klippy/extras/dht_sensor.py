# sensor_dht.py - Support for DHT11/DHT22 temperature and humidity sensors
#
# Requires the Adafruit_DHT Python library.
#
# Install with: pip install Adafruit_DHT
#
# Place this file in the "klipper/klippy/extras/" directory and reference
# it in the "printer.cfg" file.

import logging
import Adafruit_DHT

class DHTSensor:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.name = config.get_name().split()[-1]
        self.pin = config.get("pin")
        self.sensor_type = config.get("dht_type", default="DHT22")
        self.report_time = config.getfloat("report_time", 2.0, above=0.1)

        # Map sensor type string to Adafruit_DHT constant
        if self.sensor_type.upper() == "DHT11":
            self.dht_sensor = Adafruit_DHT.DHT11
        elif self.sensor_type.upper() == "DHT22":
            self.dht_sensor = Adafruit_DHT.DHT22
        else:
            raise ValueError(f"Unknown dht_type: {self.sensor_type}")

        self.humidity = None
        self.temperature = None
        self.next_report_time = 0

        self.printer.register_event_handler("klippy:ready", self.start_reading)

    def start_reading(self):
        reactor = self.printer.get_reactor()
        self.timer = reactor.register_timer(self._read_sensor)

    def _read_sensor(self, eventtime):
        # Skip reading if we're not yet ready for the next report
        if eventtime < self.next_report_time:
            return eventtime + self.report_time

        self.next_report_time = eventtime + self.report_time
        try:
            # Read sensor data
            humidity, temperature = Adafruit_DHT.read_retry(self.dht_sensor, self.pin)

            if humidity is not None and temperature is not None:
                self.humidity = humidity
                self.temperature = temperature
            else:
                logging.warning(f"{self.name}: Failed to read from sensor on pin {self.pin}")
        except Exception as e:
            logging.error(f"{self.name}: Error reading DHT sensor: {e}")

        return self.next_report_time

    def get_status(self, eventtime):
        # Return sensor data as status
        return {
            "temperature": self.temperature,
            "humidity": self.humidity,
        }

def load_config(config):
    # Enregistrer le capteur en tant que capteur de température
    ptemperature = config.get_printer().load_object(config, "temperature_sensor")
    ptemperature.add_sensor_factory("DHTSensor", DHTSensor)
