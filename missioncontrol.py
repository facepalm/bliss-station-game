from cargo_modules import DragonCargoModule
import manifest
from station import Station  


'''Mission Control'''

class MissionControl(object):
    def __init__(self, scenario=None, logger=None):
        self.counter=0
        self.logger=logger
        self.scenario=scenario
        
    def send_resupply_vessel(self, station="", extras=[]):
        if not self.scenario: return None
        if not station and self.scenario.stations: 
            station = self.scenario.stations.keys()[0]
        
        modDrag = DragonCargoModule()      
        modDrag.setup_simple_resupply()      
        
        self.counter += 1
        
        
        newStation = Station(modDrag,'ResupplyStation', self.logger)
        
        modDrag.manifest = manifest.Manifest(modDrag)
        modDrag.manifest.new_item(tasktype='Unload', taskamt = 'All', itemtype = 'Clutter', subtype = 'Any')
        modDrag.manifest.new_item(tasktype='Load', taskamt = 'All', itemtype = 'Clutter', subtype = 'Solid Waste')                        
        
        self.scenario.add_station(newStation)                    
        
        self.scenario.stations[station].position_at_safe_distance(modDrag)
        self.scenario.stations[station].begin_docking_approach(modDrag)
        
        return newStation
        

    def accept_vessel(self,scenario=None,station=""):        
        if not scenario: return
        if not station: return
        
        #calculate station value (if possible/necessary)
        
        self.scenario.remove_station(station)
        
    def update(self,dt):
        pass        
            
            
            
            
        

class Mission(object):
    def __init__(self,selection=None):
        self.load_mission(selection)                

    def load_mission(self,selection=None):
        if not selection:
            self.current_mission = 'Standard Resupply'
            self.objectives = None
        
    def update_mission(self,scenario):
        if self.current_mission == "Standard Resupply":
            pass
                      
class Objective(object):
    def __init__(self,name='Spawn Dragon capsule', description = 'Spawns a Dragon cargo module in the local space', order = 'SpawnModule DragonResupply TROGDOR', **kwargs):
        self.name = name
        self.desc = description                     
        self.order = order
        self.completed = False
        
    def carry_out(self,scenario=None):
        if not scenario: return
        order_token = self.order.split(' ')
        if order_token[0] == 'SpawnModule': #Spawn Type Name
            spawned=None
            if order_token[1] == 'DragonResupply':
                spawned = DragonCargoModule()      
                spawned.setup_simple_resupply()      
            if spawned:
                spawned.name=order_token[2]    
                scenario.entities[order_token[2]]=spawned
        
        if order_token[0] == 'ApproachModule': #Approach moduleA to stationB
            if not isinstance(scenario.entities[order_token[2]],BasicModule): pass
        
        
        
class SpawnModuleObjective(Objective):
    def __init__(self, **kwargs):
        super(SpawnModuleObjective, self).__init__(**kwargs)  
        
        
    def carry_out(self,scenario=None):
        if not scenario: return
        order_token = self.order.split(' ')
        if not order_token[0] == 'SpawnModule':
            spawned=None
            if order_token[1] == 'DragonResupply':
                spawned = DragonCargoModule()      
                spawned.setup_simple_resupply()      
            if spawned:
                spawned.name=order_token[2]    
                scenario.modules[order_token[2]]=spawned
      
