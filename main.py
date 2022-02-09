from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from paho.mqtt import client as mqtt_client
import random
import _thread

app = FastAPI()

# ------------------------------------------------------- MQTT STUFF ----------------------------------------------------

broker = 'localhost'
port = 1883
client_id = f'python-mqtt-{random.randint(0, 1000)}'
client_id_subscribe = f'python-mqtt-{random.randint(0, 1000)}'
client = None
clientSubscribe = None

# The data for subscribed topics change
data_global_temperature = 0
data_global_humidity = 0

data_fan_on_temperature: int = 0
data_fan_alert_temperature: int = 0
data_fan_on_humidity: int = 0
data_heat_on_temperature: int = 0
data_heat_on_humidity: int = 0
data_illumination: int = 0
data_lights_r: int = 0
data_lights_g: int = 0
data_lights_b: int = 0

def connect_mqtt(to_subscribe):
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    # Set Connecting Client ID
    if to_subscribe:
        global client_id_subscribe
        while client_id_subscribe == client_id:
            client_id_subscribe = f'python-mqtt-{random.randint(0, 1000)}'
        global clientSubscribe
        clientSubscribe = mqtt_client.Client(client_id_subscribe)
        clientSubscribe.on_connect = on_connect
        clientSubscribe.connect(broker, port)
        return clientSubscribe
    else:
        global client
        client = mqtt_client.Client(client_id)
        # client.username_pw_set(username, password)
        client.on_connect = on_connect
        client.connect(broker, port)
        return client


def publish(topic, msg):
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Sending '{msg}' to topic '{topic}'")
    else:
        print(f"Failed to send message to topic '{topic}'")


def subscribe():
    def on_message(client, userdata, msg):
        the_msg = msg.payload.decode()
        the_topic = msg.topic
        print(f"Received '{the_msg}' from '{the_topic}' topic")
        if the_topic == "/fan/threshold/temperature":
            global data_fan_on_temperature
            data_fan_on_temperature = the_msg
        if the_topic == "/fan/threshold/humidity":
            global data_fan_on_humidity
            data_fan_on_humidity = the_msg
        if the_topic == "/heat/threshold/temperature":
            global data_heat_on_temperature
            data_heat_on_temperature = the_msg
        if the_topic == "/heat/threshold/humidity":
            global data_heat_on_humidity
            data_heat_on_humidity = the_msg
        if the_topic == "/illumination":
            global data_illumination
            data_illumination = the_msg
        if the_topic == "/lights/r":
            global data_lights_r
            data_lights_r = the_msg
        if the_topic == "/lights/g":
            global data_lights_g
            data_lights_g = the_msg
        if the_topic == "/lights/b":
            global data_lights_b
            data_lights_b = the_msg
        if the_topic == "/temperature":
            global data_global_temperature
            data_global_temperature = the_msg
        if the_topic == "/humidity":
            global data_global_humidity
            data_global_humidity = the_msg
        if the_topic == "/fan/alert":
            global data_fan_alert_temperature
            data_fan_alert_temperature = the_msg

    clientSubscribe.subscribe("#")
    clientSubscribe.on_message = on_message

def parallel_thread():
    global clientSubscribe
    clientSubscribe = connect_mqtt(True)
    subscribe()
    clientSubscribe.loop_forever()


def run():
    global client
    client = connect_mqtt(False)
    client.loop_start()
    _thread.start_new_thread(parallel_thread, ())

run()


# ------------------------------------------------------- THE API ----------------------------------------------------

# Условные действия

class TemperatureAndHumidity(BaseModel):
    temperature: int
    humidity: int

@app.put("/fan/threshold")
def put_fan_threshold(data: TemperatureAndHumidity):
    publish("/fan/threshold/temperature", data.temperature)
    publish("/fan/threshold/humidity", data.humidity)
    global data_fan_on_temperature
    data_fan_on_temperature = data.temperature
    global data_fan_on_humidity
    data_fan_on_humidity = data.humidity
    return {"status": "ok"}

class Temperature(BaseModel):
    temperature: int

@app.put("/fan/alert")
def put_fan_alert(data: Temperature):
    publish("/fan/alert", data.temperature)
    global data_fan_alert_temperature
    data_fan_alert_temperature = data.temperature
    return {"status": "ok"}

@app.put("/heat/threshold")
def put_heat_threshold(data: TemperatureAndHumidity):
    publish("/heat/threshold/temperature", data.temperature)
    publish("/heat/threshold/humidity", data.humidity)
    global data_heat_on_temperature
    data_heat_on_temperature = data.temperature
    global data_heat_on_humidity
    data_heat_on_humidity = data.humidity
    return {"status": "ok"}

# Показания датчиков

@app.get("/temperature")
def get_temperature():
    return {
        "status": "ok",
        "data": {
            "temperature": data_global_temperature
        }
    }


@app.get("/humidity")
def get_humidity():
    return {
        "status": "ok",
        "data": {
            "humidity": data_global_humidity
        }
    }

# Свет

@app.get("/illumination")
def get_humidity():
    return {
        "status": "ok",
        "data": {
            "illumination": data_illumination
        }
    }

@app.get("/lights")
def get_humidity():
    return {
        "status": "ok",
        "data": {
            "r": data_lights_r,
            "g": data_lights_g,
            "b": data_lights_b
        }
    }


class RBGValues(BaseModel):
    r: int
    g: int
    b: int

@app.put("/lights")
def put_lights(data: RBGValues):
    publish("/lights/r", data.r)
    publish("/lights/g", data.g)
    publish("/lights/b", data.b)
    global data_lights_r
    global data_lights_g
    global data_lights_b
    data_lights_r = data.r
    data_lights_g = data.g
    data_lights_b = data.b
    return {"status": "ok"}
