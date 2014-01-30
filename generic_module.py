
#from pygraph.classes.graph import graph
import networkx as nx
from atmospherics import Atmosphere
from equipment import CBM, O2TankRack, FoodStorageRack, BatteryBank, MysteryBoxRack, DOCK_EQUIPMENT, GenericStorageRack, Equipment
from clutter import Stowage
import clutter

import uuid
from module_resources import ResourceBundle

import math
import numpy as np
import random
import string
import util

def absolute_xyz (location, offset, orient, size):
    loc = location
    off = offset*size
    rotmat=np.array([[math.cos(orient[0]),    math.sin(orient[0]), 0],
                     [-1*math.sin(orient[0]), math.cos(orient[0]), 0],
                     [0                     , 0                  , 1]])
    return loc+np.dot(off,rotmat)

def separate_node(node):
    if not '|' in node: return False, False
    n=node.split('|')
    return n

class BasicModule():
    '''Basic Module: literally just a tin can'''
    def __init__(self):
        self.id = str(uuid.uuid4())        
        if not hasattr(self,'size'): self.size = np.array([ 3 , 2 , 2 ])
        self.stowage = Stowage(10) #things floating around in the module
        self.exterior_stowage = Stowage(0) #things strapped to the outside of the module
        self.sprite = None 
        self.gravity = np.array([ 0 , 0 , 0 ])
        self.orientation = np.array([ math.pi/4 , 0 ])
        self.location = np.array([ 0 , 0 , 0 ])
        self.composition = {'Al' : 14500}      
        self.package_material = [] #if a list of filters, material put in this will not be removed
        self.station = None
        
        self.atmo = Atmosphere()
        self.atmo.volume= math.pi * self.size[0] * pow (self.size[1] / 2, 2)   
        self.atmo.initialize('Air')  
        
        self.equipment=dict() #miscellaneous (or unremovable) non-rack equipment
        self.paths = nx.Graph() 
        
        self.nodes=dict()
        
        if not hasattr(self,'imgfile'): self.imgfile = "module_placeholder.jpg"
        self.refresh_image()
     
    def refresh_image(self):
        self.img = util.load_image(self.imgfile)
        
        if math.sin(self.orientation[0]) < 0:
            pass#self.img = self.img.get_transform(flip_y=True)
            #TODO replace with different image altogether
        if math.cos(self.orientation[0]) < 0:
            self.img = self.img.get_transform(flip_x=True)
            
        
     
    def find_resource(self, resource_type = None, check = lambda x: True):
        if resource_type == "Equipment":
            eq=[]
            eq.extend([[self.equipment[e][3], self.node( e ) ]  for e in self.equipment.keys() if self.equipment[e][3] and check(self.equipment[e][3]) ])
            eq.extend( [ [ v, self.filterNode( self.node('Inside') ) ] for v in self.stowage.contents if check( v ) ] )
            eq.extend( [ [ v, self.node('Outside') ] for v in self.exterior_stowage.contents if check( v ) ] )
            if eq:
                random.shuffle(eq)
                return eq[0][0], eq[0][1]
            return None, None
        elif resource_type == "Equipment Slot":
            eq=[]
            eq.extend([[self.equipment[e][2], self.node( e ) ]  for e in self.equipment.keys() if not self.equipment[e][3] and check(self.equipment[e][2]) ])
            if eq:
                random.shuffle(eq)
                return eq[0][0], eq[0][1]
            return None, None        
        else:
            stuff=self.stowage.find_resource(check)
            if stuff:
                return stuff, self.filterNode( self.node('Inside') )
            return None, None
                     
    def get_living_space(self): return self.stowage.free_space       
    living_space = property(get_living_space, None, None, "Living space" ) 
    #exterior_space = self.exterior_stowage.free_space
        
    def compute_short_id(self): return string.upper(self.id[0:6])       
    short_id = property(compute_short_id, None, None, "Short ID" )     
        
    def get_mass(self): return sum([self.composition.values()])        
    mass = property(get_mass, None, None, "Total mass" )     
        
    def node(self, to_append):
        return ''.join( [ self.id, '|', to_append ] )
        
    def getXYZ(self,offset):
        return absolute_xyz(self.location, offset, self.orientation, self.size)       
        
    def filterNode(self,node):
        [ module, name ] = separate_node(node)
        if module != self.id: return None
        if name == "Inside": return random.choice(self.nodes.keys())    
        return node
        
    def update(self, dt):
        for e in self.equipment:            
            if self.equipment[e][3]: 
                self.equipment[e][3].update( dt )
        self.stowage.update(dt)
        self.exterior_stowage.update(dt)
        if 'Equipment' not in self.package_material:
            for c in self.stowage.contents:
                if isinstance(c,Equipment) and not c.installed and not c.task:
                    c.install_task(self.station)
                
        
    def get_random_dock(self):
        docks=[f for f in self.equipment.keys() if self.equipment[f][2] in DOCK_EQUIPMENT and self.equipment[f][3] and not self.equipment[f][3].docked]
        if not docks: assert False, "Module has no free dockable ports!"
        return random.choice(docks)    
            
    def get_empty_slot(self,slot_type='LSS'):
        slots = [s for s in self.equipment.keys() if ( self.equipment[s][2] == slot_type or slot_type=='ANY' ) and not self.equipment[s][3]]
        if not slots: return None
        return random.choice(slots)
            
    def uninstall_equipment(self,equip):
        for f in self.equipment.keys():
            if self.equipment[f][3] == equip:
                self.equipment[f][3] = None
                self.stowage.add( equip )
                return True
        return False                            
        
    
            
    def berth(self, my_node, neighbor, their_node, instant=False):
        if not neighbor or not my_node or not their_node: return False, "Docking cancelled: pointers missing" 
        if not my_node in self.equipment or not their_node in neighbor.equipment: return False, "Docking cancelled: wrong module, I guess?"
        if not self.equipment[my_node][2] in DOCK_EQUIPMENT or not neighbor.equipment[their_node][2] in DOCK_EQUIPMENT: return False, "Docking cancelled: requested interface(s) are not docking equipment!"
        if self.equipment[my_node][2] != neighbor.equipment[their_node][2]: return False, "Docking cancelled: incompatible docking mechanisms"
        if self.equipment[my_node][3].docked or neighbor.equipment[their_node][3].docked: return False, "Docking cancelled: at least one module already docked elsewhere"
        
        #calculate orientation
        self.orientation = ( neighbor.orientation + neighbor.equipment[their_node][1] - self.equipment[my_node][1] ) + np.array([math.pi, 0])
        
        #calculate location
        self.location=np.array([ 0,0,0 ])
        loc_offset = self.getXYZ(self.equipment[my_node][0])
        self.location = neighbor.getXYZ(neighbor.equipment[their_node][0]) - loc_offset
        self.orientation %= 2*math.pi
        
        #collision detection

        #dock, finally
        self.equipment[my_node][3].dock( neighbor, instant)
        neighbor.equipment[their_node][3].dock( self, instant )
        
        # map graphs together
        
        if neighbor.station:    
            if self.station:
                print self.station, neighbor.station
                assert False, "Station merging not in yet" #TODO replace with station merge
            else:         
                self.station = neighbor.station 
                self.station.paths.add_nodes_from(self.paths.nodes())
                self.station.paths.add_edges_from(self.paths.edges(data=True))
                self.station.paths.add_edge(self.node(my_node),neighbor.node(their_node),weight=1)
                self.refresh_equipment()
                
        else:             
            neighbor.station = self.station
                                    
            if self.station:
                self.station.paths.add_nodes_from(neighbor.paths.nodes())
                self.station.paths.add_edges_from(neighbor.paths.edges(data=True))
                self.station.paths.add_edge(self.node(my_node),neighbor.node(their_node),weight=1)
                neighbor.refresh_equipment()
            
        neighbor.refresh_image()    
        self.refresh_image()
            
        return True        
        
    def add_edge(self,one,two):
        delta = self.nodes[two] - self.nodes[one] #numpy vector subtraction, I hope
        delta *= self.size
        mag = abs( np.sqrt( np.vdot( delta , delta ) ) )
        self.paths.add_edge(one,two,weight=mag)
        
    def add_edge_list(self,edges):
        for e in range(1,len(edges)):            
            self.add_edge( self.node( edges[ e - 1 ] ), self.node( edges[ e ] ) )
        
    def add_equipment(self, eq_node, eq_obj, eq_coords, hall_node, eq_orientation=np.array([ 0 , 0]), eq_type='MISC' ):
        node_coords = self.nodes[ self.node( hall_node ) ] + 0.8 * ( eq_coords - self.nodes[ self.node( hall_node ) ] ) 
        self.nodes[self.node(eq_node)] = node_coords
        self.add_edge( self.node(hall_node), self.node(eq_node) )
        self.equipment[ eq_node ] = [ eq_coords, eq_orientation, eq_type, eq_obj]

    def refresh_equipment(self):
        for e in self.equipment:            
            if self.equipment[e][3]: 
                self.equipment[e][3].refresh_station()
                
    def draw(self,window):
        zoom=11
        self.img.blit(zoom*self.location[0]+window.width // 2, zoom*self.location[1]+window.height // 2, 0)
        pass                

class BasicStationModule(BasicModule):
    """ Basic as ISS modules get, this is pretty much a tube with CBM docks at each end """
    def __init__(self):
        BasicModule.__init__(self)         
                                                            
        self.equipment['CBM1']= [ np.array([ 1 , 0 , 0 ]), np.array([0 , 0]), 'CBM', CBM().install(self)]
        self.equipment['CBM0']= [ np.array([ -1 , 0 , 0 ]), np.array([math.pi , 0]), 'CBM', CBM().install(self)]
        #[location orientation type obj]       
        
        self.nodes={self.node('CBM0') : np.array([ -0.95, 0 , 0 ]),                    
                    self.node('CBM1') : np.array([ 0.95, 0 , 0 ])}        
        
        self.paths.add_nodes_from(self.nodes.keys())
                                                             
                                      
class DestinyModule(BasicStationModule):
    """ Modeled using the ISS Destiny module, this is a large module with
        plenty of equipment space and fore/aft docks. """
    def __init__(self):   
        self.size = np.array([ 8.53 , 4.27 , 4.27 ])
        BasicStationModule.__init__(self) 
        
        
        
        new_nodes={ self.node('hall0'): np.array([ -0.75, 0 , 0 ]),
                    self.node('hall1'): np.array([ -0.45, 0 , 0 ]),
                    self.node('hall2'): np.array([ -0.15, 0 , 0 ]),
                    self.node('hall3'): np.array([ 0.15, 0 , 0 ]),
                    self.node('hall4'): np.array([ 0.45, 0 , 0 ]),
                    self.node('hall5'): np.array([ 0.75, 0 , 0 ])}
                    
        self.add_edge(self.node('CBM0'),self.node('CBM1'))               
        # merging n dicts with a generator comprehension
        self.nodes = dict(i for iterator in (self.nodes, new_nodes) for i in iterator.iteritems())                    
                    
        self.paths.add_nodes_from([f for f in self.nodes.keys() if not f in self.paths.nodes()])
        self.add_edge_list(['CBM0','hall0','hall1','hall2','hall3','hall4','hall5','CBM1'])   
        
        _sampdict = {'port' : [ -0.5, 0, math.pi, 0 ], 'starboard' : [ 0.5 , 0, -math.pi, 0 ],
                     'nadir' : [0, -0.5, 0, -math.pi], 'zenith' : [ 0 , 0.5, 0, math.pi ]}
        for _d in _sampdict.keys():
            for _ex,_x in enumerate([-0.75, -0.45, -0.15, 0.15, 0.45, 0.75]):
                self.equipment[ ''.join( [ _d , str( _ex ) ] ) ] = [ np.array([ _x , _sampdict[_d][0] , _sampdict[_d][1] ]) , np.array([ _sampdict[_d][2] , _sampdict[_d][3] ]), 'RACK', None ]
                self.nodes[ self.node( ''.join( [ _d , str( _ex ) ] ) ) ] = np.array([ _x , _sampdict[_d][0]/2 , _sampdict[_d][1]/2 ])
                self.paths.add_node( self.node( ''.join([ _d , str( _ex ) ] ) ) )
                self.add_edge( self.node( ''.join( [ 'hall' , str( _ex ) ] ) ) , self.node( ''.join( [ _d , str( _ex ) ] ) ) )
                
                
                 
        self.equipment['port1'][3]=O2TankRack().install(self)              
        self.equipment['starboard5'][3]=BatteryBank().install(self)              
        self.equipment['starboard3'][3]=FoodStorageRack().install(self) 
        
        stuffrack = GenericStorageRack() 
        stuffrack.filter = clutter.ClutterFilter(['Supplies'])
        self.stowage.add( stuffrack )
        #self.equipment['nadir0'][3]=MysteryBoxRack().install(self)              
        
                                      
if __name__ == "__main__":
    test  = DestinyModule()
    toast = BasicStationModule()
    print test.atmo.pressure
    test.equipment['port1'][1].update()
    print test.atmo.pressure
    print absolute_xyz(test.location, test.equipment['CBM1'][0], test.orientation, test.size)
    print absolute_xyz(test.location, test.equipment['CBM0'][0], test.orientation, test.size)
    toast.berth('CBM0', test, 'CBM0')
    print toast.location
    print toast.equipment['CBM0'][3].docked.location
