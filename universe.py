from generic_module import DestinyModule
from zvezda import ZvezdaModule
from docking_modules import UnityModule
from cargo_modules import DragonCargoModule
from module_resources import ResourceBundle
from tasks import TaskTracker
from station import Station        
from actor import Robot
from human import Human        
                                      
if __name__ == "__main__":
    from time import sleep    

    modA  = DestinyModule()
    modDock = UnityModule()    
    modB   = ZvezdaModule()
    modDrag = DragonCargoModule()
    modDrag.setup_simple_resupply()
           
    station = Station(modDock)
    station.berth_module(modDock,'CBM0',modA, None)
    station.berth_module(modDock,'CBM3',modB, None)    
    station.berth_module(modA,None,modDrag, None)
    
    '''rob = Robot('Robby')     
    rob.station = station
    station.actors[rob.id]=rob
    rob.location = modB.node('hall0')
    rob.xyz = modB.location'''
    
    ernie= Human('Ernesto')
    ernie.station = station
    station.actors[ernie.id] = ernie
    ernie.location = modA.node('hall0')
    ernie.xyz = modA.location
    
    ernie.needs['WasteCapacityLiquid'].amt=0.1
    ernie.needs['Water'].amt=0.1
    
      
    #modA.berth('CBM0', modB, 'CBM0')
    for m in station.modules.values(): print m.id, m.location
    #for n in station.paths.edges(data=True): print n
    for i in range(1,10000):
        station.update(24*1/20.0)
        sleep(1/20.0)
        #print 'Robot task:', None if not rob.task else (rob.task.name,rob.location,rob.task.severity)
        #print 'robot tasks:', [t.name for t in rob.my_tasks.tasks]
        print 'Human task:', None if not ernie.task else (ernie.task.name,ernie.task.location,ernie.task.severity)
        print 'human tasks:', [[t.name, t.severity] for t in ernie.my_tasks.tasks]        
        print 'station tasks:', [[t.name, t.severity] for t in station.tasks.tasks]
        #print 'Dragon free storage: ',modDrag.stowage.contents
        #print station.resources.resources['Electricity'].previously_available , station.resources.resources['Electricity'].available
        #print station.tasks.tasks
        #print modA.equipment['starboard5'][3].charge
