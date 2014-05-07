from generic_module import DestinyModule
from zvezda import ZvezdaModule
from docking_modules import UnityModule
from cargo_modules import DragonCargoModule
from module_resources import ResourceBundle
from tasks import TaskTracker
from station import Station        
from actor import Robot
from human import Human        
import util
import logging
import pyglet
from pyglet.gl import *  
from pyglet import clock
from scenario import ScenarioMaster

util.GRAPHICS = 'pyglet'

def load_image(filename, anchor_x=None, anchor_y=None):
    img = pyglet.image.load(filename).get_texture(rectangle=True)
    img.anchor_x = anchor_x if anchor_x else img.width // 2
    img.anchor_y = anchor_y if anchor_y else img.height // 2 
    return img
    
util.load_image = load_image      
    
def make_solid_image(width,height,color=(128,128,128,128), anchor_x = None, anchor_y = None):
    img = pyglet.image.SolidColorImagePattern(color).create_image(util.ZOOM*width,util.ZOOM*height).get_texture(rectangle=False)   
    img.anchor_x = anchor_x if anchor_x else img.width // 2
    img.anchor_y = anchor_y if anchor_y else img.height // 2 
    return img
    
util.make_solid_image = make_solid_image

def load_sprite(filename, anchor_x=None, anchor_y=None):
    img = pyglet.image.load(filename).get_texture(rectangle=True)
    img.anchor_x = anchor_x if anchor_x else img.width // 2
    img.anchor_y = anchor_y if anchor_y else img.height // 2 
    sprite = pyglet.sprite.Sprite(img)
    return sprite
    
util.load_sprite = load_sprite

def image_to_sprite(image, x=0, y=0, rot=0, batch=None):
    sprite = pyglet.sprite.Sprite(image,x=util.ZOOM*x,y=util.ZOOM*y)
    sprite.rotation= 90+1 * 180/3.14159 * rot
    return sprite
    
util.image_to_sprite = image_to_sprite
    
                                      
if __name__ == "__main__":
    from time import sleep    

    
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

    scenario = ScenarioMaster(scenario='BERTNERNIE',logger=logger)

    @window.event
    def on_draw():

    #    background.blit_tiled(0, 0, 0, window.width, window.height)
        window.clear()
        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        glOrtho(-window.width//2,window.width//2,-window.height//2,window.height//2,0,1);
        glMatrixMode(GL_MODELVIEW);

        scenario.get_station().draw(window)

        
    #clock.set_fps_limit(30)
    clock.schedule_interval(scenario.status_update,1)
    clock.schedule_interval(scenario.system_tick,0.050)
    
    window.set_visible()
    pyglet.app.run()

    
