from cargo_modules import DragonCargoModule
import manifest
from station import Station  
import util
import filtering
import numpy as np

'''Mission Control'''

class MissionControl(object):
    def __init__(self, scenario=None, logger=None):
        self.counter=0
        self.logger=logger
        self.scenario=scenario
        self.vessel_queue=[]
        
        
    def send_resupply_vessel(self, station="", extras=[]):
        if not self.scenario: return None
        if not station and self.scenario.stations: 
            station = self.scenario.stations.keys()[0]
        
        modDrag = DragonCargoModule()      
        modDrag.setup_simple_resupply()      
        modDrag.location = np.array([ -100000 , 0 , 0 ])
        
        self.counter += 1
        
        newStation = Station(modDrag,'ResupplyStation', self.logger)
        vessel = VesselPlan( station = newStation, target_station_id = station )
        self.vessel_queue.append( vessel )                                   
        
        return newStation
        

    def accept_vessel(self,station=None):        
        if not station: return
        
        #calculate station value (if possible/necessary)
        
        self.scenario.remove_station(station)
        
    def update(self,dt):
        #check vessel queue for active vessel
        for v in self.vessel_queue:
            if v.financing <= 0:
                if v.design <= 0:
                    if v.construction <= 0:
                        if v.launch_prep <= 0:
                            station = self.scenario.add_station(v.station)  
                            self.scenario.stations[v.target_id].position_at_safe_distance(v.station)
                            self.vessel_queue.remove(v)
                            
                            if v.autodock:
                                miss_comp, d, d = self.scenario.stations[v.target_id].search( filtering.EquipmentFilter( target='Mission Computer' ) )
                                modDock = v.station.modules.values()[0]
                                miss_comp.generate_mission(selection='New Module', target_id = v.station.id, module_id = modDock.id)
                        else:
                            v.launch_prep -= dt                
                    else:
                        v.construction -= dt    
                else:
                    v.design -= dt
            else:
                v.financing -= dt
        
class VesselPlan(object):
    def __init__(self, station = None, target_station_id=None, autodock = True):
        self.financing = util.seconds(30,'seconds')
        self.design = util.seconds(30,'seconds')
        self.construction = util.seconds(30,'minutes')
        self.launch_prep = util.seconds(30,'seconds')      
        
        self.station = station
        self.target_id = target_station_id
        self.autodock = autodock
                                               
        
      
