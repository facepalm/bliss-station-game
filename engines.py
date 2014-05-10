
from equipment import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from filtering import Searcher
     
class Engine(Machinery):
    '''Ancestor to all modern rocket engines, the Engine is best known for its crummy Isp rating'''
    
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/placeholder_engine.tif"
        super(Engine, self).__init__()
        self.in_vaccuum=True #default for rocket engines         
        self.Isp = 300
        self.fuel = 'Kerosene'
        self.oxid = 'LOX'
        
    def update(self,dt):
        super(Engine, self).update(dt)        
        #if self.installed and not self.task or self.task.task_ended():
        #    #work on the box    
        #    self.task = Task(''.join(['Stare at Mystery Box']), owner = self, timeout=86400, task_duration = 86400, severity='LOW', fetch_location_method=Searcher(self,self.installed.station).search )
        #    self.installed.station.tasks.add_task(self.task)
        
class Merlin_A(Engine):
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/merlin_engine.tif"
        super(Merlin_A, self).__init__()              
        self.Isp = 450
        

class KeroseneTank(Storage):
    def __init__(self):   
        if not hasattr(self,'imgfile'): self.imgfile = "images/flammable_fuel.tif"
        super(KeroseneTank, self).__init__()         
        self.filter = ClutterFilter(['Kerosene'])
        self.stowage.capacity = 2.0

class OxygenTank(Storage):
    def __init__(self):   
        if not hasattr(self,'imgfile'): self.imgfile = "images/cryo_storage.tif"
        super(OxygenTank, self).__init__()         
        self.filter = ClutterFilter(['LOX'])
        self.stowage.capacity = 2.0
        
