
from general import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from filtering import Searcher
import random
from tasks import Task
            
class Workshop(Equipment):
    '''Progenitor class for machine shop bits'''
    
    configuration = 'Workbench' #space suitable for building small equipment from parts
    
    def __init__(self):
        self.img="images/glitch-assets/tinkertool/tinkertool__x1_iconic_png_1354832369.png"
    
        super(Workshop, self).__init__()              
        self.idle_draw = 0.200 #kW                
        self.name = "Workshop"        

    def update(self,dt):            
        super(Workshop, self).update(dt)
                               
    def refresh_image(self):     
        super(Workshop, self).refresh_image() 
        if self.sprite is None: return        
        self.sprite.add_layer('Workshop',util.load_image(self.img))
        self.sprite.layer['Workshop'].scale = 0.8                            
    

class WorkbenchRack(Rack, Workshop):
    def __init__(self):
        
        Workshop.__init__(self) 
        Rack.__init__(self)                    
        
        self.name = "Workbench InnaBox"
        
    def update(self,dt):            
        Workshop.update(self,dt)
        Rack.update(self,dt)              
        
    def build_equipment_task(self,equip):
        if not equip or not hasattr(equip,'recipe') or not equip.recipe: return False
        pass  

