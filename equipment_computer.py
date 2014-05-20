
from equipment import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from tasks import Task
from filtering import Searcher
import numpy as np
from scipy.interpolate import UnivariateSpline
import random, math
from generic_module import absolute_xyz
     
class Computer(Equipment):
    '''Progenitor class for non-moving computery bits'''
    
    def __init__(self):
        super(Computer, self).__init__()              
        self.idle_draw = 0.100 #kW

    def update(self,dt):            
        super(Computer, self).update(dt)
        
    def refresh_image(self):     
        super(Computer, self).refresh_image()
        self.sprite.add_layer('Computer',util.load_image("images/computer_40x40.png"))

class DockingComputer(Computer, Rack):
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/docking_computer.tif"
        super(DockingComputer, self).__init__()              
        self.idle_draw = 0.200 #kW
        self.docking_mode = 'DOCK'
        self.docking_item = None #The thing doing the docking or undocking (THEM)
        self.docking_target = None #The (module,dock) where it will be docking to (US)
        self.docking_path = None #The path object that will interpolate its journey
        self.docking_task = None
        self.docking_duration = util.seconds(2,'minutes')
    
    def refresh_image(self):     
        super(DockingComputer, self).refresh_image()
        self.sprite.add_layer('DockingComputer',util.load_image("images/smalldockingsymbol_40x40.png"))
        
    def dock_module(self,item=[None,None],target=[None, None]):
        if not item[0]: return False
        if not self.installed: return False
        if self.docking_task and not self.docking_task.ended(): return False                       
        #TODO check for fuel, engines, etc on item
        
        self.docking_item = item
        self.docking_target = target
        
        if not self.docking_target[0]: 
            mods = self.installed.station.modules     
            self.docking_target[0] = random.choice( [ mods[m] for m in mods if mods[m].get_random_dock() ] )    
        if not self.docking_target[1]: self.docking_target[1] = self.docking_target[0].get_random_dock()                 
        if self.docking_item[0] and not self.docking_item[1]: 
            self.docking_item[1] = self.docking_item[0].get_random_dock(side_port_allowed=False)                                        
        
        self.docking_path = FlightPath(self.docking_target[0], self.docking_target[1], self.docking_item[0], self.docking_item[1],self.docking_duration, FlightType='DOCK')
        
        self.docking_task = Task("Dock module", owner = self, timeout=None, task_duration = self.docking_duration, severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
        self.installed.station.tasks.add_task(self.docking_task)    

    def undock_module(self, item=[None,None]):
        if not item[0]: return False
        if not self.installed: return False
        if self.docking_task and not self.docking_task.ended(): return False                       
        #TODO check for fuel, engines, etc on item
        
        self.docking_item = item
        self.docking_target = target
        
        if self.docking_item[0] and not self.docking_item[1]: 
            self.docking_item[1] = self.docking_item[0].get_random_dock(side_port_allowed=False)                                        
        
        #TODO finish this method
        
        '''if not self.docking_target[0]: 
            mods = self.installed.station.modules     
            self.docking_target[0] = random.choice( [ mods[m] for m in mods if mods[m].get_random_dock() ] )    
        if not self.docking_target[1]: self.docking_target[1] = self.docking_target[0].get_random_dock()                 
        
        self.docking_path = FlightPath(self.docking_target[0], self.docking_target[1], self.docking_item[0], self.docking_item[1],self.docking_duration, FlightType='DOCK')
        
        self.docking_task = Task("Dock module", owner = self, timeout=None, task_duration = self.docking_duration, severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
        self.installed.station.tasks.add_task(self.docking_task)    
        '''

    def task_finished(self,task):
        if not task or not self.installed: return
        if task.name == "Dock module":
            self.installed.station.berth_module(self.docking_target[0], self.docking_target[1], self.docking_item[0], self.docking_item[1])        
            
    def task_work_report(self,task,dt):
        if task.name.startswith('Dock module'):
            self.docking_item[0].location, self.docking_item[0].orientation = self.docking_path.get_time_point(task.task_duration - task.task_duration_remaining)
            self.docking_item[0].refresh_image()
            
                
            
class FlightPath():
    def __init__(self, *args, **kwargs):
        self.duration = None
        self.start_coords = [None,None]
        self.start_orient = [None,None]
        self.end_coords = [None,None,None]
        self.end_orient = [None,None,None]
        
        if 'FlightType' in kwargs and kwargs['FlightType']=='DOCK':
            self.init_dock(*args, **kwargs)
                
    def calculate_path(self):
        if not (self.duration and self.start_coords.any() and self.end_coords.any() and self.start_orient.any() and self.end_orient.any()):
            #TODO log this
            assert False, "Flight path requested with incomplete information!"
        self.x = np.array( [0, self.duration/4, 3*self.duration/4, self.duration] )
        x=self.x
        w=np.array([1,10,10,5])
        self.c0 = UnivariateSpline(x, np.array([self.start_coords[0], self.start_coords[0]+10*math.cos(self.start_orient[0]), self.end_coords[0]-30*math.cos(self.end_orient[0]), self.end_coords[0]]), w=w,k=2, s=0)
        self.c1 = UnivariateSpline(x, np.array([self.start_coords[1], self.start_coords[1]+10*math.sin(self.start_orient[0]), self.end_coords[1]-30*math.sin(self.end_orient[0]), self.end_coords[1]]), w=w,k=2, s=0)
        self.c2 = UnivariateSpline(x, np.array([self.start_coords[2], self.start_coords[2], self.end_coords[2], self.end_coords[2]]), w=w,k=2, s=0)
            
        self.o0 = UnivariateSpline(x, np.array([self.start_orient[0], self.start_orient[0], self.end_orient[0], self.end_orient[0]]), w=w,k=2, s=0)
        self.o1 = UnivariateSpline(x, np.array([0,0,0,0]), w=w,k=2, s=0)    
            
        
    def init_dock(self,mod_dock, dock_dock, mod_docker, dock_docker, duration, **kwargs):
        self.duration=duration
        self.start_coords = mod_docker.location
        self.start_orient = mod_docker.orientation
        self.start_orient %= 2*math.pi
        
        self.end_orient = ( mod_dock.orientation + mod_dock.equipment[dock_dock][1] - mod_docker.equipment[dock_docker][1] ) + np.array([math.pi, 0])
        self.end_orient %= 2*math.pi
        
        loc_offset = absolute_xyz(np.array([0,0,0]), mod_docker.equipment[dock_docker][0], self.end_orient, mod_docker.size)
        
        self.end_coords = mod_dock.getXYZ(mod_dock.equipment[dock_dock][0]) - loc_offset
        
        self.calculate_path()        
        
    def get_time_point(self,t=0):
        return [np.array([self.c0(t), self.c1(t), self.c2(t)]), np.array([self.o0(t), self.o1(t)]) ]
        
util.equipment_targets['Docking Computer'] = DockingComputer
