
from general import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from filtering import Searcher
import random
     
class MysteryBoxRack(Rack):
    '''Mysterious box of boxy mystery.  Dare you enter its magical realm?'''
    
    def __init__(self):
        super(MysteryBoxRack, self).__init__()         
        
    def update(self,dt):
        super(MysteryBoxRack, self).update(dt)        
        if self.installed and not self.task or self.task.task_ended():
            #work on the box    
            self.task = Task(''.join(['Stare at Mystery Box']), owner = self, timeout=86400, task_duration = 86400, severity='LOW', fetch_location_method=Searcher(self,self.installed.station).search )
            self.installed.station.tasks.add_task(self.task)
            
class Experiment(Equipment):
    '''Progenitor class for experimental sciency bits'''
    
    def __init__(self):
        self.img=random.choice(["images/glitch-assets/element_green/element_green__x1_1_png_1354832187.png",
        "images/glitch-assets/element_blue/element_blue__x1_1_png_1354832189.png",
        "images/glitch-assets/element_red/element_red__x1_1_png_1354832185.png",
        "images/glitch-assets/element_shiny/element_shiny__x1_1_png_1354832191.png"])
    
        super(Experiment, self).__init__()              
        self.idle_draw = 0.200 #kW
        
        self.raw_unfiltered_SCIENCE = 0.0
        self.capacity_for_SCIENCE = util.seconds(3,'months')
        self.no_more_SCIENCE = False
        
        self.name = "Experiment"        
        self.field = 'Physics'
        self.level = 1


    def update(self,dt):            
        super(Experiment, self).update(dt)
        
        if self.no_more_SCIENCE or self.installed is None or not self.powered: return
        self.raw_unfiltered_SCIENCE += dt*random.random()
        if self.raw_unfiltered_SCIENCE >= self.capacity_for_SCIENCE:
            self.no_more_SCIENCE = True
                
    def science_percentage(self):
        return self.raw_unfiltered_SCIENCE/self.capacity_for_SCIENCE       
                
    def refresh_image(self):     
        super(Experiment, self).refresh_image() #diabolic_acid__x1_1_png_1354832222.png
        if self.sprite is None: return
        
        self.sprite.add_layer('Experiment',util.load_image(self.img))

class ExperimentRack(Rack, Experiment):
    def __init__(self):
        
        Experiment.__init__(self) 
        Rack.__init__(self)            
        self.idle_draw = 2.0 * random.random() #kW
        
        self.name = "Experiment"
        
    '''def refresh_image(self):     
        Rack.refresh_image(self)
        Experiment.refresh_image(self)        
        if self.sprite is None: return
        self.sprite.add_layer('Biology Experiment',util.load_image("images/glitch-assets/element_green/element_green__x1_1_png_1354832187.png"))
        self.sprite.layer['Experiment'].visible = False
        '''
        
    def update(self,dt):            
        Experiment.update(self,dt)
        Rack.update(self,dt)              
