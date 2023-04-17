import machine
import pyb # import ADC, Pin, Timer
import framebuf
import time
import ssd1306
import assets
import random
import pixel

class Dino():
    def __init__(self, pos=[10,22]):
        self.pos = pos
        self.hitbox = (8,12)
        self.alive = True
        self.up = False
        return

    def jump(self):
        self.pos[1] -= 10
        self.up = True
        
    def land(self):
        self.pos[1] += 10
        self.up = False

    def hit(self,obs):
        return self.pos[0]+self.hitbox[0] >= obs.pos[0] and self.pos[0] <= obs.pos[0] and self.pos[1]+self.hitbox[1] >= obs.pos[1] and self.pos[1] <= obs.pos[1]
    
    def isAlive(self):
        return self.alive
    
class Cactus():
    def __init__(self, pos=[128,28]):
        self.pos = pos
        self.hitbox = (5,8)

def play(display):
    display.fill(0)
    time.sleep(1.)
    sw1, sw2, sw3 = pyb.Pin('SW1', pyb.Pin.IN), pyb.Pin('SW2', pyb.Pin.IN), pyb.Pin('SW3', pyb.Pin.IN)

    sw1.init(pyb.Pin.IN, pyb.Pin.PULL_UP, af = -1)
    sw2.init(pyb.Pin.IN, pyb.Pin.PULL_UP, af = -1)
    sw3.init(pyb.Pin.IN, pyb.Pin.PULL_UP, af = -1)

    sw1_old_value, sw2_old_value, sw3_old_value = 1, 1, 1
    dino = Dino()
    obstacles = []
    first_obs_time = time.time() + 4
    last_obs_time = 0
    jump_time = 0
    last_move = 0
    while dino.isAlive():
        sw1_value = sw1.value()
        sw2_value = sw2.value()
        now = time.time()
        if sw1_value != sw1_old_value:
            if sw1_value == 0:
                return
        if sw2_value != sw2_old_value:
            if sw2_value == 0 and jump_time < now and not dino.up:
                dino.jump()
                jump_time = time.time() + 2

        if jump_time < now and dino.up:
            dino.land()
        
        # Spawns cactus
        if first_obs_time < now and last_obs_time < now:
            last_obs_time = time.time() + random.randint(4,8)
            new_cactus = Cactus([128,28])
            obstacles.append(new_cactus)
        
        # Cactus movement and despawn
        if last_move < time.time_ns():
            last_move = time.time_ns() + 50 * 10 ** 6
            for i in range(len(obstacles)):
                if obstacles[i].pos[0] < 0:
                    obstacles.pop(i)
                    break
                if dino.hit(obstacles[i]):
                    return
                obstacles[i].pos[0] -= 1
        
        # Draw
        display.fill(0)
        assets.draw_pixel(display,pixel.PIXEL_DINO,dino.pos[0],dino.pos[1])
        for cactus in obstacles:
            assets.draw_pixel(display,pixel.PIXEL_CACTUS,cactus.pos[0],cactus.pos[1])
        display.show()

    return