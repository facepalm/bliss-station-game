import pyglet
import util

class LayeredSprite(object):
    def __init__(self,name='GenericSprite',batch=None):
        self.batch = batch if batch else util.station_batch
        self.layer = dict()
        self.order = 0
        
    def add_layer_sprite(self,name,sprite):
        sprite.batch = self.batch
        if name not in self.layer: self.order += 1        
        self.layer[name]=sprite
        self.layer[name].group = pyglet.graphics.OrderedGroup(self.order, parent = util.parent_group)
    
    def add_layer(self,name,image):
        sprite = pyglet.sprite.Sprite(image)
        if name not in self.layer: self.order += 1 
        sprite.batch = self.batch
        sprite.group = pyglet.graphics.OrderedGroup(self.order, parent = util.parent_group)
        self.layer[name]=sprite    
        
    def update_sprite(self,x,y,rot):
        for l in self.layer.values():
            l.x = x
            l.y = y    
            l.rotation = rot
                      
                        
