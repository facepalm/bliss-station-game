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
import random, math, uuid
import util
import logging

class Station():
    def __init__(self,initial_module=None, name=None, logger=None):
        self.modules=dict()
        self.id = str(uuid.uuid4())   
        self.exterior_objects=[]
        self.resources=ResourceBundle()
        self.paths=nx.Graph()
        self.tasks=TaskTracker()
        self.actors=dict()
        self.name = name if name else "GenericStation"
        self.logger = logging.getLogger(logger.name + '.' + self.name) if logger else util.generic_logger        
        
        self.docked_stations = []

        self.location = 'LEO'
        self.position = 'Approach'
        
        if initial_module: self.dock_module(None,None,initial_module,None)                        
                       
    def dock_module(self, my_module, my_dock, module, mod_dock, instant = False):        
        if module and not self.modules:
            self.modules[module.id]=module
            module.station = self
            module.refresh_station()
            self.paths = module.paths.copy()
            self.position = 'Docked'
            return
            
        if not my_module: my_module = random.choice( [ self.modules[m] for m in self.modules if self.modules[m].get_random_dock() ] )    
        if not my_module.id in self.modules: assert False, "Requested module not part of station"
        if module.id in self.modules: assert False, "Requested new module already part of station"
                
        if not my_dock: my_dock = my_module.get_random_dock()                 
        if not mod_dock: mod_dock = module.get_random_dock(side_port_allowed=False)                                        
                
        #attempt docking
        assert module.dock(mod_dock, my_module, my_dock)
        
        if module.station != self and not module.station in self.docked_stations:
            #merge stations
            other_station = module.station
            
            n=self.paths.nodes()
            e=self.paths.edges(data=True)
            
            self.paths.add_nodes_from(other_station.paths.nodes())
            self.paths.add_edges_from(other_station.paths.edges(data=True))
            other_station.paths.add_nodes_from(n)
            other_station.paths.add_edges_from(e)
            
            self.docked_stations.append(other_station)
            other_station.docked_stations.append(self)
                
        module.connect(mod_dock, my_module, my_dock, instant)        
        
        #remove if hanging outside
        if module in self.exterior_objects: self.exterior_objects.remove(module)
        
        #merge resources
        self.resources.grow()
        
        self.modules[module.id]=module  
        self.logger.info(''.join(["Modules berthed: ",my_module.short_id,'(',my_dock,')',' to ',module.short_id,'(',mod_dock,')']))
        
    def join_station(self, other_station):          
        if not other_station in self.docked_stations:
            self.logger.warning('Attempting to join two stations that are apparently not docked.')
            
        for m in other_station.modules.keys():
            other_station.modules[m].station = self
            other_station.modules[m].refresh_station()
            if not m in self.modules:
                self.modules[m] = other_station.modules[m]
            else:
                self.modules[other_station.modules[m].id] = other_station.modules[m]
            other_station.modules.pop(m)
                    
        for a in other_station.actors.keys():
            other_station.actors[a].station = self
            self.actors[a] = other_station.actors[a]
            self.actors[a].refresh_station()
            other_station.actors.pop(a)
            
        if other_station in self.docked_stations: 
            self.docked_stations.remove(other_station)


    def percolate_location(self,init_mod):
        self.reset_module_touches()
        init_mod.percolate_location()
        
    
    def split_station(self, docking_ring):
        '''Splits off the module WITH the given docking ring into a new station, percolates it to connected modules'''
        if not docking_ring or not docking_ring.installed or not docking_ring.docked: return
        self.reset_module_touches()
        docking_ring.docked.touched = True
        new_station_list = docking_ring.installed.percolate()
        if len(new_station_list) == len(self.modules.values()) -1:
            self.logger.warning(''.join(["Attempting to split a doubly or-higher connected module from station"])) 
            pass
            
        #Validate new station
        for n in new_station_list:
            if n.manifest and not n.manifest.satisfied:
                self.logger.info("Station splitting failed: at least one split module has unsatisfied manifest!")
                return False    
            
        new_station = Station(None, "Return Station", self.logger)
        new_station.position='Docked'
        self.docked_stations.append(new_station)
        new_station.docked_stations.append(self)
        new_station.paths.add_nodes_from(self.paths.nodes())
        new_station.paths.add_edges_from(self.paths.edges(data=True))
                     
        util.scenario.add_station(new_station)
        
        for a in self.actors.keys():
            if self.get_module_from_loc(self.actors[a].location) in new_station_list:
                self.actors[a].station = new_station
                new_station.actors[a] = self.actors[a]
                self.actors[a].refresh_station()
                self.actors.pop(a)
        
        for m in new_station_list:
            m.station = new_station
            new_station.modules[m.id] = m
            m.refresh_station()
            self.modules.pop(m.id)
                                                            
        self.logger.info(''.join(["Successfully split station! New station: ",util.short_id(new_station.id)]))
        
        return new_station

    def undock_station(self,other_station):
        if other_station == self: return
        if other_station in self.docked_stations: 
            self.docked_stations.remove(other_station)
        else:
            return
        
        #prune nodes, edges
        for n in self.paths.nodes(): 
            if self.get_module_from_loc(n) == None:
                self.paths.remove_node(n)
        for e in self.paths.edges():
            if not (e[0] in self.paths and e[1] in self.paths):
                self.paths.remove_edge(e)
                
        other_station.undock_station(self)
        
    def reset_module_touches(self):
        for m in self.modules.values():
            m.touched=False

    def get_safe_distance_orient(self):
        return np.array([-30,-30+60*random.random(),0]), np.array([ -math.pi +2*math.pi*random.random(), 0 ])

    def position_at_safe_distance(self,module):
        station=None
        if isinstance(module, Station):
            station = module
            module = module.modules.values()[0]
        #TODO calculate boundary of station, multiply by 1.25
        safe_location, safe_orient = self.get_safe_distance_orient()
        
        module.location = 2*safe_location
        module.orientation = safe_orient
        
        if station is not None:
            station.percolate_location(module)
        
        if not module.station: self.exterior_objects.append(module)
        module.refresh_image()                
        
        
    def begin_docking_approach(self,module,dock=None):                
        dock_comp, d, d = self.search( EquipmentFilter( target='Docking Computer' ) )
        if not dock_comp:
            #TODO fail more gracefully
            assert False, 'Docking initialized with no active docking computer!  WTF mang?'
        dock_comp.dock_module([module,dock],[None,None])

    def begin_undocking_approach(self,module,dock=None):                
        dock_comp, d, d = self.search( EquipmentFilter( target='Docking Computer' ) )
        if not dock_comp:
            #TODO fail more gracefully
            assert False, 'Undocking initialized with no active docking computer!  WTF mang?'
        dock_comp.undock_module([module,dock])

    def get_random_dock(self, side_port_allowed = True, modules_to_exclude=[]):
        hits=[]
        for m in [n for n in self.modules.values() if not n in modules_to_exclude]:
            d = m.get_random_dock( side_port_allowed )
            if d: hits.append( [ m, d ] )    
        random.shuffle(hits)  
        hits.sort(key=lambda tup: tup[0], reverse=True)
        return hits[0] if hits else [None, None]              
        
        
    def search(self, filter_, modules_to_exclude=[]):
        hits=[]
        if [m for m in self.modules.values() if not m in modules_to_exclude] == []:
            return [None, None, None]        
        for m in [n for n in self.modules.values() if not n in modules_to_exclude]:
            [obj, loc, score] = m.search(filter_)
            hits.append( [ obj, loc, score ] )
        random.shuffle(hits)    
        hits.sort(key=lambda tup: tup[2], reverse=True)
        #print hits
        return hits[0] if hits and hits[0][2] else [None, None, None]
        
        
    def random_location(self, modules_to_exclude=[]):        
        if [m for m in self.modules.values() if not m in modules_to_exclude] == []:
            return [None, None, None]
        module = random.choice([m for m in self.modules.values() if not m in modules_to_exclude])
        return None, module.filterNode( module.node('Inside') ), None
        
    def update(self,dt):
        self.resources.update(dt)
        self.tasks.update(dt)
        #print [[t.name,str(t.touched)] for t in self.tasks.tasks]
        for m in self.modules.keys():
            if m in self.modules: self.modules[m].update(dt)     

        for a in self.actors.values():
            a.update(dt)       
            
    def loc_to_xyz(self,loc, percolate=True):
        [ node, name ] = separate_node(loc)
        module = self.get_module_from_loc(loc, percolate)
        if name == "Inside": return module.location
        return module.getXYZ(module.nodes[loc])
        
    def xyz_to_module(self, xyz):
        pass      #needs collision detection
        
    def get_module_from_loc(self, loc, percolate=True):
        [ node, name ] = separate_node( loc )
        module = [ self.modules[ m ] for m in self.modules if self.modules[ m ].id == node ]        
        if not module: 
            if percolate:
                for s in self.docked_stations:
                    new_loc = s.get_module_from_loc(loc,False)
                    if new_loc != None: return new_loc
            return None
        return module[ 0 ]
        
    def draw(self, window):
        if not window: return self.logger.warning("Requested draw to Nonetype.")
        for m in self.exterior_objects:
            m.draw(window)
        for m in self.modules.values():
            m.draw(window)
        for a in self.actors:
            self.actors[a].update_location()
                    
                                      
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
