## Imports

import machine
import pyb # import ADC, Pin, Timer
import framebuf
import time
import ssd1306
import assets
import game

## ------------------------

# led_blue = pyb.LED(1)

delay = 0.5

rtc = pyb.RTC()
rtc.datetime([2023,1,1,5,0,0,0,0])

# I2C
# PA15 Soft I2C_SCL
# PC10 Soft I2C_SDA
i2c = machine.SoftI2C(scl=machine.Pin('A15'), sda=machine.Pin('C10'))

# Buttons SW{X}
sw1, sw2, sw3 = pyb.Pin('SW1', pyb.Pin.IN), pyb.Pin('SW2', pyb.Pin.IN), pyb.Pin('SW3', pyb.Pin.IN)

sw1.init(pyb.Pin.IN, pyb.Pin.PULL_UP, af = -1)
sw2.init(pyb.Pin.IN, pyb.Pin.PULL_UP, af = -1)
sw3.init(pyb.Pin.IN, pyb.Pin.PULL_UP, af = -1)

sw1_old_value, sw2_old_value, sw3_old_value = 1, 1, 1

# Power Display
machine.Pin('C13', machine.Pin.OUT).low() #mettre courant entrant
machine.Pin('A8', machine.Pin.OUT).high() #mettre courant sortant

# Display
display = ssd1306.SSD1306_I2C(128, 64, i2c)
pyb.Pin(pyb.Pin.cpu.C2, mode=pyb.Pin.IN)

assets.initialize(display=display)

## Get ECG analog value


# Here we get the value of our sensor's default value
sleep_value = 0
for i in range(1000):
    val = pyb.ADC('A0').read()
    sleep_value += val
sleep_value /= 1000

## --------------------------------------------------------
##          Not in detecting finger
## --------------------------------------------------------
display.text("PLEASE",40,18)
display.text("PLACE YOUR",24,26)
display.text("FINGER",40,34)
display.text("ON THE SENSOR",12,42)
sweep_pos = 0
# Did not detect anything with the sensor
while pyb.ADC('A0').read() < sleep_value * 2:
    sw1_value = sw1.value()
    sw2_value = sw2.value()
    sw3_value = sw3.value()

    if sw1_value != sw1_old_value:
        if sw1_value == 0:
            game.play(display)
            assets.initialize(display)
            display.text("PLEASE",40,18)
            display.text("PLACE YOUR",24,26)
            display.text("FINGER",40,34)
            display.text("ON THE SENSOR",12,42)
            time.sleep(0.5)
    # Detect button press to change time
    if sw2_value != sw2_old_value:
        if sw2_value == 0:
            assets.change_time(display,rtc,sw1,sw2,sw3)
            display.text("PLEASE",40,18)
            display.text("PLACE YOUR",24,26)
            display.text("FINGER",40,34)
            display.text("ON THE SENSOR",12,42)
    if sw3_value != sw3_old_value:
        if sw3_value == 0:
            assets.precise_bpm(display,sw1,sw2,sw3)
    # Display time
    date = rtc.datetime()
    assets.draw_time(display,date[4],date[5])

    sweep_pos = (sweep_pos + 1) % 120

    # Display BPM
    assets.draw_bpm(display,0)

    display.show()

## --------------------------------------------------------
##          Detecting finger
## --------------------------------------------------------
display.fill_rect(2,12,120,46,0)

display.text("FINGER",40,18)
display.text("DETECTED",32,26)
display.text("PLEASE",40,34)
display.text("WAIT",48,42)
display.show()
time.sleep(0.5)

display.fill_rect(2,12,120,46,0)
display.show()

sweep_values = [0] * 120

launch_time = time.time()
sweep_pos = 0
sample_size = 20
sum_ = 0
sample = [0] * sample_size
pos = 0
now = time.time_ns()
last_beat = 0
beat_list_by_second = [0]*60
beat_second = launch_time
at = 0
beat_nb = 0
date = rtc.datetime()
prev_date = date

while 1:
    sw1_value = sw1.value()
    sw2_value = sw2.value()
    sw3_value = sw3.value()
    if sw1_value != sw1_old_value:
        if sw1_value == 0:
            sweep_pos, sum_, pos = 0, 0, 0
            sample = [0] * sample_size
            launch_time = time.time()
            now = time.time_ns()
            last_beat = 0

            beat_list_by_second = [0] * 60
            beat_second = now
            at = 0
            beat_nb = 0
    if sw2_value != sw2_old_value:
        if sw2_value == 0:
            assets.change_time(display,rtc,sw1,sw2,sw3)
    if sw3_value != sw3_old_value:
        if sw3_value == 0:
            assets.precise_bpm(display,sw1,sw2,sw3)

    start = time.time_ns()
    n = 0
    reader = 0
    
    while now < start + 1 * (10 ** 6):
        val = pyb.ADC('A0').read()
        # print(val)
        reader += val
        n += 1
        now = time.time_ns()
        
    # print(n)
    reader /= n if n > 0 else 1
    sum_ -= sample[pos]
    sum_ += reader

    sample[pos] = reader
    sweep_values[sweep_pos] = reader
    #print(int(reader))

    if reader > sleep_value * 2:
        #print(abs(sample[pos - 1] - sample[pos]) / sample[pos] * 1000)
        if abs(sample[pos - 1] - sample[pos]) / sample[pos] * 1000 > 5:
            if time.time_ns() - last_beat > 300 * 10 ** 6:
                last_beat = time.time_ns()
                assets.draw_heart_beat(display)
                current_time = time.time()
                if beat_nb == 0 and current_time != beat_second:
                    beat_second = time.time()
                beat_nb += 1
                beat_list_by_second[(current_time - launch_time) % 60] += beat_nb
    
    current_time = time.time()
    if current_time != beat_second:
        beat_second = time.time()
        beat_nb = 0
        beat_list_by_second[(current_time - launch_time) % 60] = beat_nb
        if at < 59:
            at += 1
    
    

    to_display = False
    date = rtc.datetime()
    if date != prev_date:
        to_display = True
        prev_date = date
        assets.draw_time(display,date[4],date[5])
    if sweep_pos == 119:
        to_display = True
        beat_quantity = sum(beat_list_by_second)
        bpm = int(beat_quantity * 60 / (at + 1))
        beat_quantity = 0
        assets.draw_bpm(display, bpm)
        assets.draw_curve(display,sweep_values,12)
    sweep_pos = (sweep_pos + 1) % 120
    pos += 1
    pos %= sample_size

    if to_display:
        display.show()