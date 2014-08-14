import pyglet
import util

class LayeredSprite(object):
    def __init__(self,name='GenericSprite',batch=None, start_order=0):
        self.batch = batch if batch is not None else util.default_batch
        self.layer = dict()
        self.order = start_order
        self.name=name                
        #print 'New sprite', self.name, self.batch,util.default_batch
        
    def add_layer_sprite(self,name,sprite):
        sprite.batch = self.batch
        if name not in self.layer: 
            self.order += 1        
        else:
            self.layer[name].delete()
        self.layer[name]=sprite
        self.layer[name].group = pyglet.graphics.OrderedGroup(self.order, parent = util.parent_group)
    
    def add_layer(self,name,image):
        sprite = util.image_to_sprite(image)#pyglet.sprite.Sprite(image)
        sprite.x= -10000
        self.add_layer_sprite(name, sprite)   
        
    def delete(self):
        for l in self.layer.values():
            l.delete()    
        
    def update_sprite(self,x,y,rot=0):
        for l in self.layer.values():
            #if 'Module' is self.name:
            #    print x,y,rot, l.image.anchor_x,l.image.anchor_y
            l.x = x
            l.y = y    
            l.rotation = rot
            
    def set_position(self,*args,**kwargs):
        self.update_sprite(*args,**kwargs)        
            
    def draw(self):
        for l in sorted(self.layer.values(), key=lambda s: s.group):
            l.draw()
            
    def contains(self,x,y):
        for l in self.layer.values():
            if l.visible and l.contains(x,y):
                return True
        return False            
                      
                        
