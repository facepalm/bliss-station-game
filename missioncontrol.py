from cargo_modules import DragonCargoModule
from generic_module import DestinyModule
import manifest
from station import Station  
import util
import filtering
import numpy as np
from human import Human
import random
import logging
from equipment_science import Experiment


'''Mission Control organization.  Totally not NASA, you guys.  Totally.'''

class MissionControl(object):
    def __init__(self, scenario=None, logger=None):
        self.counter=0
        self.logger=logger
        self.loggername = self.logger.name if self.logger else ''
        self.scenario=scenario
        self.vessel_queue=[]
        
        self.player_nasa_funds = 1000000000
        self.pork = 0.25
        self.base_budget=2000000000
        self.yearly_budget=2000000000
        
        self.time_elapsed = 0.0
        self.local_economy = 1.0 #1.0 = business as usual.  Higher is better.
        self.stored_science = 0
        self.science_quota = 1000 #abstract science units the station must produce yearly to remain at current budget
        
        self.protected_years = 5 #Years set aside in initial plan to build station
        
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        #d.pop('scenario') #TODO return scenario when we can pickle it
        return d    
        
    def __setstate__(self, d):
        self.__dict__.update(d)   
        self.logger = logging.getLogger(self.loggername) if self.loggername else util.generic_logger
        
        
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
        
        #unload scientific equipment
        for m in station.modules.values():
            for e in m.equipment: #TODO AH, clutter!
                if e[3] and isinstance(e[3],Experiment):
                    util.universe.science.process_experiment(e[3])
                    self.logger.info("Science added!")
        self.scenario.remove_station(station)
        
    
        
    def yearly_update(self):
        #economic growth?
        growth = 1+0.5*random.random() if random.random() > 0.5*self.local_economy else 1-0.25*random.random()
        self.local_economy *= growth
        
        strikes=0
        if growth < 1: strikes += 1
        if self.stored_science < self.science_quota/2:
            strikes += 2
            self.science_quota *= 0.75
        elif self.stored_science < self.science_quota:
            strikes += 1
            self.science_quota *= 0.95
        else:
            strikes -= 1
            self.science_quota *= 1.1
        self.stored_science = 0
        
        if self.protected_years > 0:
            if strikes > 0: strikes = 0
            self.protected_years -= 1
        
        self.base_budget *= 1 - 0.05*strikes        
        self.yearly_budget = self.base_budget * (1-self.pork)                                                                
            
        
    def update(self,dt):
        self.player_nasa_funds += dt*self.yearly_budget/util.seconds(1,'year')
        if self.time_elapsed//util.seconds(1,'year') != (dt+self.time_elapsed)//util.seconds(1,'year'):
            #we're at a year boundary.  Recompute budget
            self.yearly_update()
        self.time_elapsed += dt
        
        
    
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
                                               
        
if __name__ == "__main__":    
    mc=MissionControl()
    for i in range(100):
        mc.stored_science = 1000+11000 * random.random()
        mc.yearly_account()
        print mc.base_budget
