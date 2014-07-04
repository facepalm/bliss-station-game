from cargo_modules import DragonCargoModule
from generic_module import DestinyModule
import manifest
from station import Station  
import util
import filtering
import numpy as np
from human import Human

'''Mission Control organization.  Totally not NASA, you guys.  Totally.'''

class MissionControl(object):
    def __init__(self, scenario=None, logger=None):
        self.counter=0
        self.logger=logger
        self.scenario=scenario
        self.vessel_queue=[]
        
        self.player_nasa_funds = 1000000000
        self.pork = 0.5
        self.missioncontrol_budget = 0.005
        self.yearly_budget=2000000000
        
    def get_available_missions(self):
        out=dict()        
        out["Recruit Astronauts(3) (100M)"]=[100000000,self.send_3man_crew]
        out["Resupply Mission (50M)"]=[50000000,self.send_resupply_vessel]  
        out["Add Destiny Module (200M)"]=[200000000,self.send_destiny]
        return out
        
    def send_resupply_vessel(self, station="", extras=[]):
        newStation = self.send_module(cost=50000000)
        newStation.modules.values()[0].setup_simple_resupply()
        return newStation
        
    def send_3man_crew(self, station="", extras=[]):        
        newStation = self.send_module(cost=100000000)
        Human('Alex',station = newStation)
        Human('Bert',station = newStation)
        Human('Charlie',station = newStation)
        return newStation             
        
    def send_destiny(self, station="", extras=[]):
        modDest = DestinyModule()     
        newS = self.send_module(module=modDest,cost=200000000)     
        return newS
        
    def send_module(self, module=None, station="", extras=[],cost=200000000):
        if not self.scenario: return None
        if not station and self.scenario.stations: 
            station = self.scenario.focus_station.id
                                   
        
        modDrag = DragonCargoModule() 
        modDrag.location = np.array([ -100000 , 0 , 0 ]) 
        newStation = Station(modDrag,'AddStation', self.logger) 
        self.counter += 1                        
        
        if module: 
            module.location = np.array([ -100000 , 0 , 0 ])               
            newStation.dock_module(None,None,module, None, True)                      
        vessel = VesselPlan( station = newStation, target_station_id = station )
        self.vessel_queue.append( vessel )                                   
        
        self.player_nasa_funds -= cost      
        return newStation

    def accept_vessel(self,station=None):        
        if not station: return
        
        #calculate station value (if possible/necessary)
        
        self.scenario.remove_station(station)
        
    def add_science(self,field='Astronomy', amt=0):
        self.logger.info('New astro data: '+str(amt))
        
    def update(self,dt):
        self.player_nasa_funds += dt*self.yearly_budget/util.seconds(1,'year')
    
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
                                miss_comp, d, d = self.scenario.stations[v.target_id].search( filtering.EquipmentFilter( target='Mission Computer', is_installed=True ) )
                                modDock = [m for m in v.station.modules.values() if isinstance(m,DragonCargoModule)][0]
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
        self.construction = 0#util.seconds(30,'minutes')
        self.launch_prep = util.seconds(30,'seconds')      
        
        self.station = station
        self.target_id = target_station_id
        self.autodock = autodock
                                               
        
      
