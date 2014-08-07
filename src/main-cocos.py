import util

import lib2d
import math
import logging
import cocos

from scenario import ScenarioMaster                     

util.GRAPHICS = 'cocos2d'     
    
def make_solid_sprite(width,height,color=(128,128,128,128), anchor_x = None, anchor_y = None, x=0,y=0,rot=0,batch=None):
    #l= cocos.layer.util_layers.ColorLayer(color[0],color[1],color[2],color[3],width,height)
    l= cocos.sprite.Sprite("images/Blank.tif")
        
    l.color=(color[0],color[1],color[2])
    #if anchor_x is not None and anchor_y is not None:
    #    l.anchor = (anchor_x,anchor_y)
    #else:
    l.anchor_x = 5#width/2 if anchor_x is None else anchor_x
    l.anchor_y = 5#height/2 if anchor_y is None else anchor_y
    
    l.scale_x = 1.0*width/1000
    l.scale_y = 1.0*height/1000
    
    l.position = (x,y)
    l.rotation= -1 * 180/math.pi * rot
    return l
    
util.make_solid_sprite = make_solid_sprite


def load_sprite(filename, anchor_x=None, anchor_y=None):
    pass
    
util.load_sprite = load_sprite

def new_Layer():
    return cocos.layer.Layer()
    
util.Layer = new_Layer

class GameLayer(cocos.layer.Layer):
    def __init__(self):
        super( GameLayer, self ).__init__()    
        label = cocos.text.Label('A derp derpderp',
                          font_name='Times New Roman',
                          font_size=32,
                          anchor_x='center', anchor_y='center')
        label.position = 320,240  
        self.add(label)                
    
def cocos_debug(dt,station=None):
    if station is None: return
    print station.name, station.sprite.children    
                          
                                      
if __name__ == "__main__":    
    cocos.director.director.init()
    cocos.director.director.set_show_FPS(True)
    
    logger=logging.getLogger("Universe")
    logger.setLevel(logging.DEBUG)
    #DEBUG INFO WARNING ERROR CRITICAL
    #create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)#INFO
    #create formatter
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    #add formatter to ch
    ch.setFormatter(formatter)
    #add ch to logger
    logger.addHandler(ch)

    scenario = ScenarioMaster(scenario='DOCKINGTEST',logger=logger)

    game_layer = GameLayer()   
    
    game_layer.position = 320,240
    
    game_layer.add(scenario.get_stations()[0].sprite)
    
    main_scene = cocos.scene.Scene (game_layer)
    
    main_scene.schedule_interval(scenario.status_update,1)
    #main_scene.schedule_interval(scenario.system_tick,0.10)
    #main_scene.schedule_interval(cocos_debug,1,station=scenario.get_stations()[0])
    
    cocos.director.director.run (main_scene)


    
