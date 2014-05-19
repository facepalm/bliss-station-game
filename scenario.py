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
        current_scenario=Scenario(scenario,logger)        
        
        self.station = current_scenario.station  
          
        #modA.berth('CBM0', modB, 'CBM0')
        for m in self.station.modules.values(): print m.short_id, m.location, m.orientation    
        
        self.time_elapsed=0
    
    def get_station(self):
        return self.station
        
    def status_update(self,dt):
        print
        #print round(util.TIME_FACTOR*tot_time),': Human task:', None if not ernie.task else (ernie.task.name,ernie.task.location,ernie.task.severity)
        util.generic_logger.info('System time:%d' %(int(util.TIME_FACTOR*self.time_elapsed)))
        #for m in station.modules.values():
        #    logger.debug(''.join([m.short_id,' O2:', str(m.atmo.partial_pressure('O2')), ' CO2:',str(m.atmo.partial_pressure('CO2'))]))
        #util.generic_logger.info(' '.join(['Electricity','Available:',station.resources.resources['Electricity'].status()]))
        for a in self.station.actors:
            self.station.actors[a].log_status()
        #ernie.log_status()
        #bert.log_status()    


    def system_tick(self,dt):    
        self.station.update(dt*util.TIME_FACTOR)
        self.time_elapsed += dt

                                          
class Scenario():
    def __init__(self,name='DEFAULT',logger=util.generic_logger):
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

        elif name == 'DOCKINGTEST':
            '''Ernie, in a station badly needing resupply, gets a Dragon shipment.
                He installs a docking computer, docks Dragon, unloads food, loads waste, undocks Dragon, Dragon reenters'''
   
            modB   = ZvezdaModule()
            modB.equipment['Toilet1'][3].tank.add(clutter.Clutter( "Solid Waste", 500.0, 714.0 ))
            self.station = Station(modB, "Docker Station", logger)
            
            modDrag = DragonCargoModule()
            modDrag.setup_simple_resupply()
            #modDrag.stowage.add(clutter.Clutter('Solid Waste', 1.5, 714.0 ))
            
            modDrag.manifest = manifest.Manifest(modDrag)
            modDrag.manifest.new_item(tasktype='Unload', taskamt = 'All', itemtype = 'Clutter', subtype = 'Any')
            modDrag.manifest.new_item(tasktype='Load', taskamt = 'All', itemtype = 'Clutter', subtype = 'Solid Waste')
                       
            #TODO: position Dragon on "docking" approach, add docking task
            self.station.begin_docking_approach(modDrag)
            print modDrag.location, modDrag.orientation
            
            ernie = Human('Ernest',station=self.station,logger=self.station.logger)
            self.station.actors[ernie.id] = ernie
            ernie.location = modB.node('hall0')
            ernie.xyz = modB.location
                                    
        else: #'DEFAULT'
            modDock = UnityModule()                   
            self.station = Station(modDock, 'NewbieStation',logger)
            
