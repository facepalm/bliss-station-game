
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
import mission
     
class Computer(Equipment):
    '''Progenitor class for non-moving computery bits'''
    
    def __init__(self):
        super(Computer, self).__init__()              
        self.idle_draw = 0.200 #kW

    def update(self,dt):            
        super(Computer, self).update(dt)
        
    def refresh_image(self):     
        super(Computer, self).refresh_image()
        if self.sprite is None: return
        self.sprite.add_layer('Computer',util.load_image("images/computer_40x40.png"))

class MissionComputer(Computer, Rack):
    def __init__(self, scenario=None):
        super(MissionComputer, self).__init__()              
        self.idle_draw = 1.000 #kW
        self.scenario=scenario
        
        self.mission = None
        self.objective = None
        self.objective_timer = 30
        self.objective_tick = 30
    
    def refresh_image(self):     
        super(MissionComputer, self).refresh_image()
        if self.sprite is None: return
        self.sprite.add_layer('DockingComputer',util.load_image("images/smallmissionsymbol_40x40.png"))
        
    def update(self,dt):            
        super(MissionComputer, self).update(dt)                
        if not self.installed or not self.mission: return
        if not self.objective:             
            self.mission = None
            return
                
        if self.objective.completed and (not self.task or self.task.task_ended()):     
            #print self.objective.name
            self.logger.info(''.join(['Mission objective completed: ',self.objective.name,' Updating mission...']))
            self.task = Task(''.join(['Update Mission']), owner = self, timeout=None, task_duration = 30, severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
            self.installed.station.tasks.add_task(self.task) 
            self.objective_timer = 30
        
        self.objective_tick -= dt        
        if self.objective_tick < 0:
            self.objective_tick = self.objective_timer           
            if not self.objective.completed:                 
                self.objective.carry_out(station=self.installed.station, scenario=self.scenario)
                self.objective_timer += 30
            else:
                self.objective_timer = 30            
            
    def generate_mission(self, selection='New Module', target_id = '', module_id = ''):
        new_miss = mission.Mission()
        new_miss.load_mission( selection=selection, target_id=target_id, module_id=module_id)
        self.new_mission(new_miss)       
            
    def new_mission(self,mission):
        if not mission or (self.task and not self.task.task_ended()) or not self.installed: return
        self.task = Task(''.join(['Log Mission']), owner = self, timeout=None, task_duration = 30, severity='HIGH', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)            
        self.task.mission=mission
        self.installed.station.tasks.add_task(self.task)       
        
    def task_finished(self,task):
        super(MissionComputer, self).task_finished(task)  
        if not task or not self.installed: return
        if task.name == "Log Mission":
            self.mission = self.task.mission 
            self.objective = self.mission.current_objective()
        elif task.name == "Update Mission":                              
            self.objective = self.mission.current_objective()
            if not self.objective: return
            self.objective.carry_out(station=self.installed.station, scenario=self.scenario)
            self.logger.info(''.join(['Mission updated.  Current objective: ',self.objective.name]))
            
        self.update(0)
    

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
        if self.sprite is None: return
        self.sprite.add_layer('DockingComputer',util.load_image("images/smalldockingsymbol_40x40.png"))
        
    def dock_module(self,item=[None,None],target=[None, None]):
        if not item[0]: return False
        if not self.installed: return False
        if self.docking_task and not self.docking_task.task_ended(): return False                       
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
        return True

    def undock_module(self, item=[None,None]):
        if not item[0]: return False
        if not self.installed: return False
        if self.docking_task and not self.docking_task.task_ended(): return False                       
        #TODO check for fuel, engines, etc on item
        
        self.docking_item = item
        
        if self.docking_item[0] and not self.docking_item[1]: 
            self.docking_item[1] = self.docking_item[0].get_neighbor_dock(self.installed.station) #TODO this WILL crash, implement when it does
        #check for hatches closed, start tasks if necessary
        dock = self.docking_item[0].equipment[self.docking_item[1]][3]
        if dock.docked:
            self.docking_item[0].disconnect(self.docking_item[1], dock.partner)    
            return False

        
        #undock stations
        self.installed.station.undock_station(self.docking_item[0].station)
        
        #start motion
        new_loc, new_orient = self.installed.station.get_safe_distance_orient()
        new_loc *= 2
        self.docking_path = FlightPath(self.docking_item[0], self.docking_item[1], new_loc, new_orient,self.docking_duration, FlightType='UNDOCK')
        
        self.docking_task = Task("Undock module", owner = self, timeout=None, task_duration = self.docking_duration, severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
        self.installed.station.tasks.add_task(self.docking_task)    
        
        return True

    def task_finished(self,task):
        super(DockingComputer, self).task_finished(task)       
        if not task or not self.installed: return
        if task.name == "Dock module":
            self.docking_item[0].location, self.docking_item[0].orientation = self.docking_path.get_time_point(task.task_duration)
            self.docking_item[0].station.percolate_location(self.docking_item[0])
            self.docking_item[0].refresh_image()
            
            self.installed.station.dock_module(self.docking_target[0], self.docking_target[1], self.docking_item[0], self.docking_item[1])        
            self.docking_item[0].station.position='Docked'
        if task.name == "Undock module":            
            self.docking_item[0].station.position='Approach'
            
            
    def task_work_report(self,task,dt):
        if task.name.startswith('Dock module') or task.name.startswith('Undock module'):
            self.docking_item[0].location, self.docking_item[0].orientation = self.docking_path.get_time_point(task.task_duration - task.task_duration_remaining)
            self.docking_item[0].station.percolate_location(self.docking_item[0])
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
        elif 'FlightType' in kwargs and kwargs['FlightType']=='UNDOCK':
            self.init_undock(*args, **kwargs)
                
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
        
    def init_undock(self,mod_dock, dock_dock, loc, orient, duration, **kwargs):
        self.duration=duration
        self.start_coords = mod_dock.location
        self.start_orient = mod_dock.orientation
        self.start_orient %= 2*math.pi
        
        self.end_orient = orient        
        self.end_coords = loc
        self.calculate_path()    
        
    def get_time_point(self,t=0):
        return [np.array([self.c0(t), self.c1(t), self.c2(t)]), np.array([self.o0(t), self.o1(t)]) ]
        
util.equipment_targets['Docking Computer'] = DockingComputer
util.equipment_targets['Mission Computer'] = MissionComputer
