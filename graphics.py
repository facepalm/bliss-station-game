import pyglet
import util

class LayeredSprite(object):
    def __init__(self,name='GenericSprite',batch=None):
        self.batch = batch if batch else util.station_batch
        self.layer=dict()
        
    def add_layer_sprite(self,name,sprite):
        sprite.batch = self.batch
        self.layer[name]=sprite
    
    def add_layer(self,name,image):
        sprite = pyglet.sprite.Sprite(image)
        sprite.batch = self.batch
        self.layer[name]=sprite    
        
    def update_sprite(self,x,y,rot):
        for l in self.layer.values():
            l.x = x
            l.y = y    
            l.rotation = rot
                      
                        
