
from general import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from filtering import Searcher
import random
from tasks import Task
     
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
        self.capacity_for_SCIENCE = random.random()*util.seconds(6,'months')
        self.no_more_SCIENCE = False
        
        self.name = "Experiment"        
        self.field = random.choice(util.universe.science.field.keys())
        self.level = util.universe.science.field[self.field].level['Knowledge']


    def update(self,dt):            
        super(Experiment, self).update(dt)
        
        if self.no_more_SCIENCE or self.installed is None or not self.powered: return

        if not (self.task and self.task.active):
            self.raw_unfiltered_SCIENCE += dt

        if self.raw_unfiltered_SCIENCE >= self.capacity_for_SCIENCE:
            self.no_more_SCIENCE = True
            
        if (not self.task or not self.task.active) and random.random() < 0.0005*dt:
            sev = random.random()
            if sev < 0.99:
                self.task = Task('Science: '+random.choice(['push buttons','twiddle knobs','record numbers','adjust display','tweak results']), owner = self, timeout=None, task_duration = util.seconds(2,'minutes'), severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)    
            else:
                self.task = Task(''.join(['Science: extinguish fire!']), owner = self, timeout=util.seconds(30,'minutes'), task_duration = util.seconds(5,'minutes'), severity='HIGH', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
            
            self.installed.station.tasks.add_task(self.task)        
    
        
                
    def science_percentage(self):
        return self.raw_unfiltered_SCIENCE/self.capacity_for_SCIENCE       
                
    def refresh_image(self):     
        super(Experiment, self).refresh_image() #diabolic_acid__x1_1_png_1354832222.png
        if self.sprite is None: return
        
        self.sprite.add_layer('Experiment',util.load_image(self.img))
                        
    def task_failed(self,task):
        super(Experiment, self).task_finished(task) 
        if not task: return
        if task.name in ['Science: extinguish fire!']:
            self.no_more_SCIENCE = True
    

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

