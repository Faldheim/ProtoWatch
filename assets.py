import machine
import pyb # import ADC, Pin, Timer
import framebuf
import time
import math
import ssd1306
import pixel

# Draw the basic shape of ProtoWatch
def initialize(display):
    rtc = pyb.RTC()
    date = rtc.datetime()

    # Background Box
    display.fill(0)
    display.fill_rect(0,0,126,62,1)
    display.fill_rect(2,2,122,58,0)
    display.hline(0,11,126,1)
    display.vline(42,0,11,1)
    display.vline(99,0,11,1)

    # ProtoWatch initial values
    draw_time(display,date[4],date[5])
    draw_bpm(display,0)
    draw_pixel(display,pixel.PIXEL_HEART_8x8_ALT,108,3)

    display.show()

# Draw a blinking heart
def draw_heart_beat(display,pos_x=108,pos_y=3):
    draw_pixel(display,pixel.PIXEL_HEART_8x8,pos_x,pos_y)
    display.show()
    draw_pixel(display,pixel.PIXEL_HEART_8x8_ALT,pos_x,pos_y)
    display.show()

# Draw heartbeat sensor curve
def draw_curve(display,values,pos_y):
    mod = 120 # (pos_x_min = 2 - pos_x_max = 123)
    scale = 46 # (pos_y_min = 12 - pos_y_max = 58)
    # Clear the sweep screen
    # if pos_x == 0:
    #     display.fill_rect(2,12,120,46,0)
    draw_sweep(display,values,pos_y,scale)

def draw_sweep(display,values,pos_y,scale):
    max_ = max(values) + 10
    min_ = min(values) - 10
    for x in range(len(values)):
        sweep = [0] * scale
        t1 = (values[x] - min_) / (max_ - min_)
        t2 = int(t1 * scale)
        sweep[min(scale - 1, t2)] = 1

        for y in range(scale):
            display.pixel(x + 2,pos_y + y,sweep[y])

def draw_bpm(display,bpm,pos_x=43,pos_y=3):
    display.fill_rect(pos_x,pos_y,56,8,0)
    display.text('BPM:{0:03d}'.format(bpm), pos_x, pos_y)

def draw_time(display,hours,minutes,pos_x=2,pos_y=3):
    display.fill_rect(pos_x,pos_y,40,8,0)
    hours_format = '{0:02d}'.format(hours)
    minutes_format = '{0:02d}'.format(minutes)
    display.text(f"{hours_format}:{minutes_format}",pos_x,pos_y)

def draw_pixel(display,pixel,pos_x,pos_y):
    for y in range(len(pixel)):
        for x in range(len(pixel[y])):
            display.pixel(pos_x + x, pos_y + y, pixel[y][x])

def change_time(display,rtc,sw1,sw2,sw3):
    date = rtc.datetime()
    time_ = [date[4], date[5]]
    pos = 0
    
    display.fill(0)
    pos_x = 40
    pos_y = 10
    draw_pixel(display, pixel.DIGITS[time_[0] // 10], pos_x, pos_y)
    draw_pixel(display, pixel.DIGITS[time_[0] % 10], pos_x + 11, pos_y)
    draw_pixel(display, pixel.PIXEL_COLON, pos_x + 22, pos_y)
    draw_pixel(display, pixel.DIGITS[time_[1] // 10], pos_x + 26, pos_y)
    draw_pixel(display, pixel.DIGITS[time_[1] % 10], pos_x + 37, pos_y)
    display.show()

    time.sleep(0.5)
    while 1:
        # Validation
        if sw1.value() != 1:
            rtc.datetime((date[0],date[1],date[2],date[3],time_[0],time_[1],0,date[7]))
            initialize(display)
            time.sleep(0.5)
            break
        # Change category
        if sw2.value() != 1:
            pos = (pos + 1) % 2
            time.sleep(0.5)
        # Change value
        if sw3.value() != 1:
            time_[pos] += 1
            if pos == 0:
                time_[pos] %= 24
                time.sleep(0.1)
            else:
                time_[pos] %= 60
                time.sleep(0.2)
        display.fill(0)

        # Draw indicator
        pos_x = 47
        pos_y = 2
        display.fill_rect(2,2,124,10,0)
        draw_pixel(display, pixel.PIXEL_INDIC, pos_x + pos * 26, pos_y)

        # Draw time
        pos_x = 40
        pos_y = 10
        draw_pixel(display, pixel.DIGITS[time_[0] // 10], pos_x, pos_y)
        draw_pixel(display, pixel.DIGITS[time_[0] % 10], pos_x + 11, pos_y)
        draw_pixel(display, pixel.PIXEL_COLON, pos_x + 22, pos_y)
        draw_pixel(display, pixel.DIGITS[time_[1] // 10], pos_x + 26, pos_y)
        draw_pixel(display, pixel.DIGITS[time_[1] % 10], pos_x + 37, pos_y)
        
        # Draw buttons informations
        pos_x = 40
        pos_y = 35
        draw_pixel(display, pixel.PIXEL_BUTTON, pos_x, pos_y)
        draw_pixel(display, pixel.PIXEL_VALID, pos_x, pos_y + 10)
        draw_pixel(display, pixel.PIXEL_BUTTON, pos_x + 20, pos_y)
        draw_pixel(display, pixel.PIXEL_HORIZ, pos_x + 20, pos_y + 10)
        draw_pixel(display, pixel.PIXEL_BUTTON, pos_x + 40, pos_y)
        draw_pixel(display, pixel.PIXEL_VERTI, pos_x + 40, pos_y + 10)
        display.show()

def precise_bpm(display,sw1,sw2,sw3):
    sample_size = 20
    sum_ = 0
    sample = [0] * sample_size
    pos = 0
    now = time.time_ns()
    while 1:
        if sw1.value() != 1:
            initialize(display)
            time.sleep(0.5)
            break
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
        display.fill(0)
        display.text(str(reader),0,0)
        display.show()
        print(int(reader))