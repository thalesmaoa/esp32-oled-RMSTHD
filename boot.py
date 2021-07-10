""" IoT SaGuard v1.0
Important notes:
Since this probram uses MQTT and alloc memory for a lot of computations. I use gc in order do avoid
memory allocation problem
Thales Maia - 5 jul 2021 """

import gc
gc.enable()
gc.collect()

from micropython import const
from micropython import alloc_emergency_exception_buf
alloc_emergency_exception_buf(100)
gc.collect()

# In order to optimize heap allocation, declare variables
sr = const(1024) # Size of the ringbuffer = int(freq_sample/freq_grid*n_cycles)

# oLed screen size
oled_width = const(128)
oled_height = const(64)

# Offset and calibration values for ADC read - Values received
offset_A = const(2057)
offset_B = const(2057)
offset_C = const(2057)
max_A = const(900)
max_B = const(900)
max_C = const(900)

px_s = 0 # Aux variable that shows that the program is running

# MQTT variables
SERVER = b'192.168.200.254'
client_id = b'saguard-01'
topic_sub = b'saguard/+'
gc.collect()

# Create ringbuffer to store voltages
Va = [0]*sr
Vb = [0]*sr
Vc = [0]*sr
Vsag = [0]*sr
gc.collect()

from ulab import numpy as np
gc.collect()

from ulab import scipy as spy
gc.collect()

# Y = np.zeros(_sr)
# Va_np = np.zeros(sr)
# Vb_np = np.zeros(sr)
# Vc_np = np.zeros(sr)
# # Y = np.zeros(sr)
# gc.collect()

# Load libs
from machine import I2C
gc.collect()

from machine import Pin
gc.collect()

from machine import UART
gc.collect()

from time import sleep_ms, sleep
gc.collect()

from mqtt_as import MQTTClient
gc.collect()

from config import config
gc.collect()

import uasyncio as asyncio
gc.collect()

# Importa a biblioteca para usar o visor
import ssd1306
gc.collect()

# OLED LED is connected to pin 16
p16 = Pin(16, Pin.OUT)
p16.value(1) # resets screen

# Start UART
uart_esp32 = UART(2)                           # init with given baudrate
uart_esp32.init(115200, bits=8, parity=None, stop=1, tx=17, rx=23, timeout=5000) # init with given parameters

# Search for oLED
i2c = I2C(1, scl=Pin(15), sda=Pin(4), freq=400000)
assert 60 in i2c.scan(), "No OLED display detected!"

# Create screen object
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c, 60)
gc.collect()