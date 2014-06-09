from generic_module import DestinyModule
from zvezda import ZvezdaModule
from docking_modules import UnityModule
from cargo_modules import DragonCargoModule
from module_resources import ResourceBundle
from tasks import TaskTracker
from station import Station        
from actor import Robot
from human import Human        
import missioncontrol
import mission
import clutter
import manifest
import util
import logging
import filtering

class ScenarioMaster():

    def __init__(self,scenario='DEFAULT',logger=util.generic_logger):
        self.current_scenario=DockingScenario(scenario,logger)                 
        util.scenario = self.current_scenario
    
    def get_stations(self):
        return self.current_scenario.get_stations()
        
    def status_update(self,dt):
        self.current_scenario.status_update(dt)   

    def system_tick(self,dt):    
        self.current_scenario.system_tick(dt)    
        
    def get_station(self,name=None):
        return self.current_scenario.get_station(name)    

                                          
class Scenario(object):
    def __init__(self,name='DEFAULT',logger=util.generic_logger):
        self.time_elapsed=0
        self.stations=dict()
        self.modules=dict()
        self.actors=dict()
        self.logger=logger
        
        self.mission_control = missioncontrol.MissionControl(self,self.logger)
        
        
        if name=='BERTNERNIE':

            modA  = DestinyModule()
            modDock = UnityModule()    
            modB   = ZvezdaModule()
            modDrag = DragonCargoModule()
            modDrag.setup_simple_resupply()
                   
            station = Station(modDock, "BnE Station", logger)
            station.dock_module(None,None,modB, None, True)
            station.dock_module(None,None,modA, None, True)    
            station.dock_module(None,None,modDrag, None, True)
            
            '''rob = Robot('Robby')     
            rob.station = station
            station.actors[rob.id]=rob
            rob.location = modB.node('hall0')
            rob.xyz = modB.location'''
            
            ernie = Human('Ernest',station=station,logger=self.logger)
            station.actors[ernie.id] = ernie
            ernie.location = modA.node('hall0')
            ernie.xyz = modA.location
            
            bert = Human('Bertholomew',station=station,logger=self.logger)
            station.actors[bert.id] = bert
            bert.location = modB.node('hall0')
            bert.xyz = modB.location
            
            ernie.needs['WasteCapacityLiquid'].amt=0.1
            ernie.needs['Food'].set_amt_to_severity('HIGH')
            ernie.nutrition = [0.5, 0.5, 0.5, 0.5, 0.5]
            #modB.equipment['Electrolyzer'][3].broken=True
             
             
                                    
        elif name=='DEFAULT':
            modDock = UnityModule()                   
            station = Station(modDock, 'NewbieStation',logger)
            self.add_station(station)
            
    def system_tick(self,dt):    
        for s in self.stations.values():
            s.update(dt*util.TIME_FACTOR)       
        self.time_elapsed += dt   
        
    def status_update(self,dt):
        print      
        util.generic_logger.info('System time:%d' %(int(util.TIME_FACTOR*self.time_elapsed)))
        for a in self.actors.values():
            a.log_status()

    def get_stations(self):
        return self.stations.values()
        
    def get_station(self,name=None):
        stations = [s for s in self.get_stations() if s.name == name]
        if stations: return stations[0]
        return None        
        
    def add_station(self,station=None):
        if not station: return    
        self.stations[station.id]=station
        for m in station.modules.values():
            self.modules[m.id]=m
        for m in station.actors.values():
            self.actors[m.id]=m
        
    def remove_station(self,station=None):
        if not station: return    
        for m in station.actors.values():
            if m.id in self.actors.keys(): 
                m.sprite.delete()
                self.actors.pop(m.id)
        for m in station.modules.values():
            for e in m.equipment.values():
                if e[3]: 
                    e[3].sprite.delete()
            if m.id in self.modules.keys(): self.modules.pop(m.id)            
        if station.id in self.stations.keys(): self.stations.pop(station.id)

                
        
        
class DockingScenario(Scenario):
    def __init__(self,name='DOCKING',logger=util.generic_logger):
        super(DockingScenario, self).__init__(name=name, logger=logger) 

        '''Ernie, in a station badly needing resupply, gets a Dragon shipment.
           He installs a docking computer, docks Dragon, unloads food, loads waste, undocks Dragon, Dragon reenters'''
   
        modB   = ZvezdaModule()
        modB.equipment['Toilet1'][3].tank.add(clutter.Clutter( "Solid Waste", 500.0, 714.0 ))
        modB.stowage.add(clutter.Clutter('Solid Waste', 1.5, 714.0 ))   
            
        station = Station(modB, "Docker Station", logger)
            
        ernie = Human('Ernest',station = station, logger = station.logger)
        station.actors[ernie.id] = ernie
        ernie.location = modB.node('hall0')
        ernie.xyz = modB.location
            
        self.add_station(station)
            
        newStation = self.mission_control.send_resupply_vessel(station.id)
        modDock = newStation.modules.values()[0]
        modD = DestinyModule()
        newStation.dock_module(None,None,modD, None, True)
        
        miss_comp, d, d = station.search( filtering.EquipmentFilter( target='Mission Computer' ) )
        miss_comp.scenario=self
        new_miss = mission.Mission()
        new_miss.load_mission(selection='New Module', target_id = newStation.id, module_id = modDock.id)
        miss_comp.new_mission(new_miss)
        
                                  
                        
