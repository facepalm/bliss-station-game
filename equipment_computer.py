
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
        self.docking_target = None #The (module,dock) where it will be docking to
        self.docking_path = None #The path object that will interpolate its journey
        self.docking_task = None
        
    def dock_module(self,item=None,target=(None, None)):
        if not item: return False
        if not self.installed: return False
        if self.docking_task and not self.docking_task.ended(): return False
        self.docking_item = item
        self.docking_target = target
        self.docking_task = Task("Dock module", owner = self, timeout=None, task_duration = util.seconds(4,'minutes'), severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
        self.installed.station.tasks.add_task(self.docking_task)    

    def task_finished(self,task):
        if not task or not self.installed: return
        if task.name == "Dock module":
            self.installed.station.berth_module(self.docking_target[0], self.docking_target[1], self.docking_item, None)        
                
            
class DockingPath():
    def __init__(self, start_coords, start_orient, end_coords, end_orient):
        pass
            
        
util.equipment_targets['Docking Computer'] = DockingComputer
