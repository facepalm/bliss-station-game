from generic_module import DestinyModule
from zvezda import ZvezdaModule
from docking_modules import UnityModule
from cargo_modules import DragonCargoModule
from module_resources import ResourceBundle
from tasks import TaskTracker
from station import Station        
from actor import Robot
from human import Human        
import clutter
import manifest
import util
import logging

class ScenarioMaster():

    def __init__(self,scenario='DEFAULT',logger=util.generic_logger):
        self.current_scenario=DockingScenario(scenario,logger)                 
    
    def get_stations(self):
        return self.current_scenario.get_stations()
        
    def status_update(self,dt):
        self.current_scenario.status_update(dt)   

    def system_tick(self,dt):    
        self.current_scenario.system_tick(dt)    

                                          
class Scenario():
    def __init__(self,name='DEFAULT',logger=util.generic_logger):
        self.time_elapsed=0
        if name=='BERTNERNIE':

            modA  = DestinyModule()
            modDock = UnityModule()    
            modB   = ZvezdaModule()
            modDrag = DragonCargoModule()
            modDrag.setup_simple_resupply()
                   
            self.station = Station(modDock, "BnE Station", logger)
            self.station.berth_module(None,None,modB, None, True)
            self.station.berth_module(None,None,modA, None, True)    
            self.station.berth_module(None,None,modDrag, None, True)
            
            '''rob = Robot('Robby')     
            rob.station = station
            station.actors[rob.id]=rob
            rob.location = modB.node('hall0')
            rob.xyz = modB.location'''
            
            ernie = Human('Ernest',station=self.station,logger=self.station.logger)
            self.station.actors[ernie.id] = ernie
            ernie.location = modA.node('hall0')
            ernie.xyz = modA.location
            
            bert = Human('Bertholomew',station=self.station,logger=self.station.logger)
            self.station.actors[bert.id] = bert
            bert.location = modB.node('hall0')
            bert.xyz = modB.location
            
            ernie.needs['WasteCapacityLiquid'].amt=0.1
            ernie.needs['Food'].set_amt_to_severity('HIGH')
            ernie.nutrition = [0.5, 0.5, 0.5, 0.5, 0.5]
            #modB.equipment['Electrolyzer'][3].broken=True
             
                                    
        else: #'DEFAULT'
            modDock = UnityModule()                   
            self.station = Station(modDock, 'NewbieStation',logger)
            
    def system_tick(self,dt):    
        self.station.update(dt*util.TIME_FACTOR)       
        self.time_elapsed += dt   
        
    def status_update(self,dt):
        print      
        util.generic_logger.info('System time:%d' %(int(util.TIME_FACTOR*self.time_elapsed)))
        for a in self.station.actors:
            self.station.actors[a].log_status()

    def get_stations(self):
        return [self.station]
        
        
class DockingScenario(Scenario):
    def __init__(self,scenario='DEFAULT',logger=util.generic_logger):
            self.time_elapsed=0
            '''Ernie, in a station badly needing resupply, gets a Dragon shipment.
                He installs a docking computer, docks Dragon, unloads food, loads waste, undocks Dragon, Dragon reenters'''
   
            modB   = ZvezdaModule()
            modB.equipment['Toilet1'][3].tank.add(clutter.Clutter( "Solid Waste", 500.0, 714.0 ))
            self.station = Station(modB, "Docker Station", logger)
            
            
            modDrag = DragonCargoModule()
            modDrag.setup_simple_resupply()
                                    
            modB.stowage.add(clutter.Clutter('Solid Waste', 1.5, 714.0 ))
                                  
            modDrag.manifest = manifest.Manifest(modDrag)
            modDrag.manifest.new_item(tasktype='Unload', taskamt = 'All', itemtype = 'Clutter', subtype = 'Any')
            modDrag.manifest.new_item(tasktype='Load', taskamt = 'All', itemtype = 'Clutter', subtype = 'Solid Waste')
            
            self.stationB=Station(modDrag,'StubStation', logger)
            
            self.station.begin_docking_approach(modDrag)
            
            rob = Robot('Robby',station = self.stationB,logger=logger)                 
            self.stationB.actors[rob.id]=rob
            rob.location = modDrag.node('store0')
            rob.xyz = modDrag.location
            rob.update_location()
                       
            #TODO: position Dragon on "docking" approach, add docking task
            
            print modDrag.location, modDrag.orientation, rob.xyz
            
            ernie = Human('Ernest',station=self.station,logger=self.station.logger)
            self.station.actors[ernie.id] = ernie
            ernie.location = modB.node('hall0')
            ernie.xyz = modB.location
            
            #for m in self.station.modules.values(): print m.short_id, m.location, m.orientation 
    
    def system_tick(self,dt):    
        self.station.update(dt*util.TIME_FACTOR)
        self.stationB.update(dt*util.TIME_FACTOR)        
        self.time_elapsed += dt  
    
    def get_stations(self):
        return [self.station, self.stationB]    
                        
