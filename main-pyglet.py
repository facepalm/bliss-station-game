import util

import math
import logging
import pyglet
import gui_pyglet
import json

pyglet.options['debug_gl'] = False

from pyglet import clock
from pyglet.window import mouse
from scenario import ScenarioMaster               
      
from pyglet import gl as gl     

import universe
import globalvars as gv
import os

import pickle

util.GRAPHICS = 'pyglet'
user_zoom = 2
user_x = 0
user_y = 0

class CollideSprite(pyglet.sprite.Sprite):
    def __init__(self, *args, **kwargs):
        super( CollideSprite, self ).__init__(*args, **kwargs)
        
    def contains(self,x,y):
        x += user_x
        y += user_y
        x *= user_zoom
        y *= user_zoom
        #TODO transform (x,y) to image coordinate space (rotate about .anchor)
        theta = math.pi * (self.rotation) / (180.0)
        x -= self.x
        y -= self.y              
        x1 = math.cos(theta)*x - math.sin(theta)*y
        y1 = math.sin(theta)*x + math.cos(theta)*y
        #print self.image.anchor_x
        x1 += self.image.anchor_x if not isinstance (self.image,pyglet.image.Animation) else self.image.frames[0].image.anchor_x
        y1 += self.image.anchor_y if not isinstance (self.image,pyglet.image.Animation) else self.image.frames[0].image.anchor_y
        if x1 >= 0 and x1 <= self.width:
            if y1 >= 0 and y1 <= self.height:                
                return True
        return False

def load_image(filename, anchor_x=None, anchor_y=None):
    gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE ) 
    gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE )    
    img = pyglet.image.load(filename)#.get_texture(rectangle=True)
    img.anchor_x = anchor_x if anchor_x is not None else img.width // 2
    img.anchor_y = anchor_y if anchor_y is not None else img.height // 2 
    return img
    
util.load_image = load_image      
    
def make_solid_image(width,height,color=(128,128,128,128), anchor_x = None, anchor_y = None):
    img = pyglet.image.SolidColorImagePattern(color).create_image(width,height)#.get_texture(rectangle=False)   
    img.anchor_x = anchor_x if anchor_x is not None else img.width // 2
    img.anchor_y = anchor_y if anchor_y is not None else img.height // 2 
    return img
    
util.make_solid_image = make_solid_image

def load_sprite(filename, anchor_x=None, anchor_y=None):
    gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE ) 
    gl.glTexParameteri( gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE )
    img = pyglet.image.load(filename)#.get_texture(rectangle=True)
    img.anchor_x = anchor_x if anchor_x is not None else img.width // 2
    img.anchor_y = anchor_y if anchor_y is not None else img.height // 2 
    sprite = CollideSprite(img)
    
    return sprite
    
util.load_sprite = load_sprite

def image_to_sprite(image, x=0, y=0, rot=0, batch=None):
    sprite = CollideSprite(image,x=gv.config['ZOOM']*x,y=gv.config['ZOOM']*y)
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

    config = pyglet.gl.Config(sample_buffers=1, samples=4)
    window = pyglet.window.Window(800, config=config, visible=False, resizable=True)    
    gui = gui_pyglet.gui(window=window)

    def contact_mission_control():
        gui.create_mission_control_dialog()
    util.contact_mission_control = contact_mission_control    
    
    @window.event
    def on_key_press(symbol, modifiers):
        if symbol == pyglet.window.key.ESCAPE:
            gui.create_escape_menu()
            return pyglet.event.EVENT_HANDLED
    
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

    skip=False
    if gv.config['AUTOLOAD']:
        try:
            util.autoload()
            
            skip=True
        except Exception,e: 
            print str(e)
            logger.critical(' Defaulting to new save')
            
    if not skip:             
        util.universe = universe.Universe()
        util.universe.generate_background('LEO')
        gv.scenario = ScenarioMaster(scenario='STRESSTEST',logger=logger)
        #gv.scenario = ScenarioMaster(scenario='LORKHAN',logger=logger)       
        util.universe.scenario = gv.scenario
                
        util.autosave()
        
    gui.scenario = util.universe.scenario
    gui.window = window

    # Update as often as possible (limited by vsync, if not disabled)
    window.register_event_type('on_update')
    def update(dt):
        window.dispatch_event('on_update', dt)
    pyglet.clock.schedule(update)

    @window.event
    def on_mouse_scroll(x, y, scroll_x, scroll_y):
        flick_zoom(scroll_y)
        
    def flick_zoom(tot):
        global user_zoom
        global user_x
        global user_y
        
        big_cap = 5.0
        sml_cap = 0.5
        step = 0.1
        
        if abs(tot) < 1:
            return        
        if user_zoom > sml_cap and user_zoom < big_cap:
            user_x *=  1 + step if tot > 0 else 1 - step
            user_y *= 1 + step if tot > 0 else 1 - step
        user_zoom *= 1 - step if tot > 0 else 1 + step
        user_zoom = min( big_cap , max( sml_cap , user_zoom ) )        
        flick_zoom(tot + (1 if tot < 0 else -1))
     
    @window.event       
    def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
        if buttons & mouse.LEFT:
            global user_x
            global user_y
            user_x -= dx
            user_y -= dy

    @window.event
    def on_draw():
        #background.blit_tiled(0, 0, 0, window.width, window.height)
        window.clear()
        util.universe.draw_background()
        
        gl.glMatrixMode(gl.GL_PROJECTION);
        gl.glLoadIdentity();        
        gl.glOrtho(-user_zoom*(window.width//2 - user_x), user_zoom*(window.width//2 + user_x), -user_zoom*(window.height//2 - user_y), user_zoom*(window.height//2 + user_y),0,1)
        gl.glMatrixMode(gl.GL_MODELVIEW);                
        
        
        for s in util.universe.scenario.get_stations():
            s.draw(window)
            
        util.station_batch.draw()
        util.actor_batch.draw()
        
        gl.glMatrixMode(gl.GL_PROJECTION);
        gl.glLoadIdentity();        
        gl.glOrtho(0,window.width,0,window.height,0,1);                
        gl.glMatrixMode(gl.GL_MODELVIEW); 
        gui.batch.draw()
        
        
        
    #clock.set_fps_limit(30)
    clock.schedule_interval(util.universe.scenario.status_update,1)
    clock.schedule_interval(util.universe.scenario.system_tick,0.0250)
    clock.schedule_interval(util.universe.update,0.02)
    
    window.push_handlers(gui)
    
    window.set_visible()
    pyglet.app.run()

    
