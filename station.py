#from pygraph.classes.graph import graph
import networkx as nx
import numpy as np

from filtering import EquipmentFilter
from generic_module import DestinyModule, separate_node
from zvezda import ZvezdaModule
from docking_modules import UnityModule
from cargo_modules import DragonCargoModule
from module_resources import ResourceBundle
from tasks import TaskTracker
import random, math
import util
import logging

class Station():
    def __init__(self,initial_module=None, name=None, logger=None):
        self.modules=dict()
        self.exterior_objects=[]
        self.resources=ResourceBundle()
        self.paths=nx.Graph()
        self.tasks=TaskTracker()
        self.actors=dict()
        self.name = name if name else "GenericStation"
        self.logger = logging.getLogger(logger.name + '.' + self.name) if logger else util.generic_logger        
        
        if initial_module: self.berth_module(None,None,initial_module,None)                        
                       
    def berth_module(self, my_module, my_dock, module, mod_dock, instant = False):        
        if module and not self.modules:
            self.modules[module.id]=module
            module.station = self
            module.refresh_equipment()
            self.paths = module.paths.copy()
            return
        if not my_module: my_module = random.choice( [ self.modules[m] for m in self.modules if self.modules[m].get_random_dock() ] )    
        if not my_module.id in self.modules: assert False, "Requested module not part of station"
        if module.id in self.modules: assert False, "Requested new module already part of station"
                
        if not my_dock: my_dock = my_module.get_random_dock()                 
        if not mod_dock: mod_dock = module.get_random_dock(side_port_allowed=False)                                        
                
        #attempt docking
        assert module.berth(mod_dock, my_module, my_dock, instant)
        
        #remove if hanging outside
        if module in self.exterior_objects: self.exterior_objects.remove(module)
        
        #merge resources
        self.resources.grow()
        
        self.modules[module.id]=module  
        self.logger.info(''.join(["Modules berthed: ",my_module.short_id,'(',my_dock,')',' to ',module.short_id,'(',mod_dock,')']))
        
        
    def begin_docking_approach(self,module):
        #TODO calculate boundary of station, multiply by 1.25
        safe_location = np.array([-30,-30+60*random.random(),0])
        
        module.location = safe_location
        module.orientation = np.array([ math.pi/4, 0 ])
        
        self.exterior_objects.append(module)
        module.refresh_image()
        
        #TODO add docking task
        dock_comp, d, d = self.search( EquipmentFilter( target='Docking Computer' ) )
        if not dock_comp:
            #TODO fail more gracefully
            assert False, 'Docking initialized with no active docking computer!  WTF mang?'
        dock_comp.dock_module(module)

            
        
    def search(self, filter_):
        hits=[]
        for m in self.modules.values():
            [obj, loc, score] = m.search(filter_)
            hits.append( [ obj, loc, score ] )
        random.shuffle(hits)    
        hits.sort(key=lambda tup: tup[2], reverse=True)
        #print hits
        return hits[0] if hits and hits[0][2] else [None, None, None]
        
    def random_location(self):
        module = random.choice(self.modules.values())
        return None, module.filterNode( module.node('Inside') ), None
        
    def update(self,dt):
        self.resources.update(dt)
        self.tasks.update(dt)
        for m in self.modules:
            self.modules[m].update(dt)     
        for a in self.actors:
            self.actors[a].update(dt)       
            
    def loc_to_xyz(self,loc):
        [ node, name ] = separate_node(loc)
        module = [self.modules[m] for m in self.modules if self.modules[m].id == node]
        if not module: return None
        module = module[0]
        if name == "Inside": return module.location
        return module.getXYZ(module.nodes[loc])
        
    def xyz_to_module(self, xyz):
        pass      #needs collision detection
        
    def get_module_from_loc(self, loc):
        [ node, name ] = separate_node( loc )
        module = [ self.modules[ m ] for m in self.modules if self.modules[ m ].id == node ]        
        if not module: return None
        return module[ 0 ]
        
    def draw(self, window):
        if not window: return self.logger.warning("Requested draw to Nonetype.")
        for m in self.exterior_objects:
            m.draw(window)
        for m in self.modules.values():
            m.draw(window)
        for a in self.actors:
            self.actors[a].draw(window)
                    
        
                                      
if __name__ == "__main__":
    from time import sleep    

    modA  = DestinyModule()
    modDock = UnityModule()    
    modB = ZvezdaModule()
    modDrag = DragonCargoModule()
    
    station = Station(modDock)
    station.berth_module(modDock,'CBM0',modA, None)
    station.berth_module(modDock,'CBM3',modB, None)    
    station.berth_module(modA,None,modDrag, None)
    #modA.berth('CBM0', modB, 'CBM0')
    for m in station.modules.values(): print m.id, m.location
    for i in range(1,10000):
        station.update(1/2.0)
        sleep(1/2.0)
        print station.resources.resources['Electricity'].previously_available , station.resources.resources['Electricity'].available
        print modA.equipment['starboard5'][3].charge
