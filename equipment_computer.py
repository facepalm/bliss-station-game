
from equipment import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from tasks import Task
from filtering import Searcher
     
class Computer(Equipment):
    '''Progenitor class for non-moving computery bits'''
    
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/placeholder_computer.tif"
        super(Computer, self).__init__()              
        self.idle_draw = 0.100 #kW

    def update(self,dt):            
        super(Computer, self).update(dt)

class DockingComputer(Computer, Rack):
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/docking_computer.tif"
        super(DockingComputer, self).__init__()              
        self.idle_draw = 0.200 #kW
        self.docking_item = None #The thing doing the docking or undocking
        self.docking_target = None #The dock where it will be docking to
        self.docking_task = None
        
    def dock_module(self,item=None,target=None):
        if not item: return False
        if not self.installed: return False
        if self.docking_task and not self.docking_task.ended(): return False
        self.docking_item = item
        self.docking_target = target if target else self.installed.station
        self.docking_task = Task("Dock module", owner = self, timeout=None, task_duration = util.seconds(4,'hours'), severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
        #self.installed.station.tasks.add_task(self.docking_task)    
            
            
#class DockingPath():
#    def __            
            
        
util.equipment_targets['Docking Computer'] = DockingComputer
