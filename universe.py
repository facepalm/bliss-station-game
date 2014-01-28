from generic_module import DestinyModule
from zvezda import ZvezdaModule
from docking_modules import UnityModule
from cargo_modules import DragonCargoModule
from module_resources import ResourceBundle
from tasks import TaskTracker
from station import Station        
from actor import Robot
from human import Human        
import util
import logging
                                      
if __name__ == "__main__":
    from time import sleep    

    logger=logging.getLogger("Universe")
    logger.setLevel(logging.DEBUG)
    #DEBUG INFO WARNING ERROR CRITICAL
    #create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    #create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    #add formatter to ch
    ch.setFormatter(formatter)
    #add ch to logger
    logger.addHandler(ch)

    modA  = DestinyModule()
    modDock = UnityModule()    
    modB   = ZvezdaModule()
    modDrag = DragonCargoModule()
    modDrag.setup_simple_resupply()
           
    station = Station(modDock, 'NewbieStation', logger)
    station.berth_module(modDock,'CBM0',modA, None, True)
    station.berth_module(modDock,'CBM3',modB, None, True)    
    station.berth_module(modA,None,modDrag, None, True)
    
    '''rob = Robot('Robby')     
    rob.station = station
    station.actors[rob.id]=rob
    rob.location = modB.node('hall0')
    rob.xyz = modB.location'''
    
    ernie= Human('Bela Lugosi',station=station,logger=station.logger)
    station.actors[ernie.id] = ernie
    ernie.location = modA.node('hall0')
    ernie.xyz = modA.location
    
    ernie.needs['WasteCapacityLiquid'].amt=0.1
    ernie.needs['Food'].set_amt_to_severity('HIGH')
    ernie.nutrition = [0.5, 0.5, 0.5, 0.5, 0.5]
    #modB.equipment['Electrolyzer'][3].broken=True
    
      
    #modA.berth('CBM0', modB, 'CBM0')
    #for m in station.modules.values(): print m.short_id, m.location
    #for n in station.paths.edges(data=True): print n
    for i in range(1,10000):
        station.update(util.TIME_FACTOR/20.0)
        sleep(1/20.0)
        #print 'Robot task:', None if not rob.task else (rob.task.name,rob.location,rob.task.severity)
        #print 'robot tasks:', [t.name for t in rob.my_tasks.tasks]
        print
        print util.TIME_FACTOR*i/20.0,': Human task:', None if not ernie.task else (ernie.task.name,ernie.task.location,ernie.task.severity)
        for m in station.modules.values():
            logger.debug(''.join([m.short_id,' O2:', str(m.atmo.partial_pressure('O2')), ' CO2:',str(m.atmo.partial_pressure('CO2'))]))
        ernie.log_status()
        #print modB.equipment['Water1'][3].available_space
        #print 'human tasks:', [[t.name, t.severity] for t in ernie.my_tasks.tasks]        
        #print 'station tasks:', [[t.name, t.severity] for t in station.tasks.tasks]
        #print 'Dragon free storage: ',modDrag.stowage.contents
        #print station.resources.resources['Electricity'].previously_available , station.resources.resources['Electricity'].available
        #print station.tasks.tasks
        #print modA.equipment['starboard5'][3].charge
