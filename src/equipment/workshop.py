
from general import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from filtering import Searcher
import random
from tasks import Task
            
class Workshop(Equipment):
    '''Progenitor class for machine shop bits'''
    
    def __init__(self):
        self.img="images/glitch-assets/tinkertool/tinkertool__x1_iconic_png_1354832369.png"
    
        super(Workshop, self).__init__()              
        self.idle_draw = 0.200 #kW                
        self.name = "Workshop"        

    def update(self,dt):            
        super(Workshop, self).update(dt)
                               
    def refresh_image(self):     
        super(Workshop, self).refresh_image() #diabolic_acid__x1_1_png_1354832222.png
        if self.sprite is None: return        
        self.sprite.add_layer('Workshop',util.load_image(self.img))
        self.sprite.layer['Workshop'].scale = 0.8                            
    

class WorkshopRack(Rack, Workshop):
    def __init__(self):
        
        Workshop.__init__(self) 
        Rack.__init__(self)                    
        
        self.name = "Workshop InnaBox"
        
    def update(self,dt):            
        Workshop.update(self,dt)
        Rack.update(self,dt)              

