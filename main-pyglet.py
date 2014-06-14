import util

import math
import logging
import pyglet

from pyglet import clock
from scenario import ScenarioMaster               
      
from pyglet import gl as gl     


util.GRAPHICS = 'pyglet'

class CollideSprite(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super( CollideSprite, self ).__init__(*args, **kwargs)
        
    def contains(self,x,y):
        #TODO transform (x,y) to image coordinate space (rotate about .anchor)
        if x >= self.x - self.width//2 and x <= self.x + self.width//2:
            if y >= self.y - self.height//2 and y <= self.y + self.height//2:
                return True
        return False

def load_image(filename, anchor_x=None, anchor_y=None):
    img = pyglet.image.load(filename)#.get_texture(rectangle=True)
    img.anchor_x = anchor_x if anchor_x else img.width // 2
    img.anchor_y = anchor_y if anchor_y else img.height // 2 
    return img
    
util.load_image = load_image      
    
def make_solid_image(width,height,color=(128,128,128,128), anchor_x = None, anchor_y = None):
    img = pyglet.image.SolidColorImagePattern(color).create_image(width,height)#.get_texture(rectangle=False)   
    img.anchor_x = anchor_x if anchor_x else img.width // 2
    img.anchor_y = anchor_y if anchor_y else img.height // 2 
    return img
    
util.make_solid_image = make_solid_image

def load_sprite(filename, anchor_x=None, anchor_y=None):
    img = pyglet.image.load(filename)#.get_texture(rectangle=True)
    img.anchor_x = anchor_x if anchor_x else img.width // 2
    img.anchor_y = anchor_y if anchor_y else img.height // 2 
    sprite = CollideSprite(img)
    
    return sprite
    
util.load_sprite = load_sprite

def image_to_sprite(image, x=0, y=0, rot=0, batch=None):
    sprite = CollideSprite(image,x=util.ZOOM*x,y=util.ZOOM*y)
    sprite.rotation= -1 * 180/math.pi * rot
    return sprite
    
util.image_to_sprite = image_to_sprite
    
def make_solid_sprite(width,height,color=(128,128,128,128), anchor_x = None, anchor_y = None, x=0,y=0,rot=0,batch=None):
    img = make_solid_image(width,height,color, anchor_x, anchor_y)
    sprite = image_to_sprite(img,x,y,rot,batch)
    return sprite
util.make_solid_sprite = make_solid_sprite
    
util.station_batch = pyglet.graphics.Batch()    
util.actor_batch = pyglet.graphics.Batch()  
util.parent_group = pyglet.graphics.Group() 
               

                                      
if __name__ == "__main__":    
    window = pyglet.window.Window(visible=False, resizable=True)    

    
    logger=logging.getLogger("Universe")
    logger.setLevel(logging.DEBUG)
    #DEBUG INFO WARNING ERROR CRITICAL
    #create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    #create formatter
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    #add formatter to ch
    ch.setFormatter(formatter)
    #add ch to logger
    logger.addHandler(ch)

    scenario = ScenarioMaster(scenario='DOCKINGTEST',logger=logger)

    @window.event
    def on_draw():
        #background.blit_tiled(0, 0, 0, window.width, window.height)
        window.clear()
        gl.glMatrixMode(gl.GL_PROJECTION);
        gl.glLoadIdentity();
        
        gl.glOrtho(-window.width//1,window.width//1,-window.height//1,window.height//1,0,1);
        gl.glMatrixMode(gl.GL_MODELVIEW);                

        for s in scenario.get_stations():
            s.draw(window)
        util.station_batch.draw()
        util.actor_batch.draw()
        
    #clock.set_fps_limit(30)
    clock.schedule_interval(scenario.status_update,1)
    clock.schedule_interval(scenario.system_tick,0.0250)
    
    window.set_visible()
    pyglet.app.run()

    
