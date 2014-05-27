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
      
