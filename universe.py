import util
import math

class Universe(object):
    def __init__(self):
        self.background = []
        self.background_loc='LEO'
        self.time = 0
        
    def update(self,dt):
        dt = dt*util.TIME_FACTOR
        self.time += dt
        if self.background_loc == 'LEO':
            #in LEO, orbital period  = 90 minutes = 5400 sec
            width = self.background[0].width            
            orbit_position = (self.time%5400)/5400.0
            day_position = (self.time%86400)/86400.0
            
            self.background[0].x = -width*orbit_position
            self.background[1].x = -width*orbit_position + 10
            
            self.background[0].y = 200*math.sin(2*math.pi*orbit_position)
            self.background[1].y = 200*math.sin(2*math.pi*orbit_position)
            
            self.background[2].x = width + self.background[0].x
            self.background[3].x = width + self.background[1].x
            self.background[2].y = self.background[0].y
            self.background[3].y = self.background[1].y
            
            self.day = max(-1,min(1,5*math.cos(2*math.pi*(day_position + orbit_position))))
            self.background[1].opacity = int(255*(self.day/2.0+0.5))
            self.background[3].opacity = self.background[1].opacity
                    
    def generate_background(self, loc="LEO"):
        self.background_loc = loc
        if loc == 'LEO':            
            self.background=[]
            self.background.append( util.load_sprite('images/Earth_at_day.png') )
            self.background.append( util.load_sprite('images/Earth_at_night.png') )
            self.background.append( util.load_sprite('images/Earth_at_day.png') )
            self.background.append( util.load_sprite('images/Earth_at_night.png') )
            #for j in self.background: j.scale=.9
        self.update(0)

    def draw_background(self):
        for l in self.background:
            l.draw()           
