
#from pygraph.classes.graph import graph
import networkx as nx
from atmospherics import Atmosphere
from equipment import CBM, O2TankRack, FoodStorageRack, BatteryBank, DOCK_EQUIPMENT, GenericStorageRack, Equipment
from clutter import Stowage
from filtering import ClutterFilter
import clutter
from equipment_science import MysteryBoxRack
from module_resources import ResourceBundle

import math
import numpy as np
import random
import string
import util
import globalvars as gv

import manifest

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
        self.id = util.register(self)     
        print self.id
        if not hasattr(self,'size'): self.size = np.array([ 3 , 2 , 2 ])
        self.stowage = Stowage(10) #things floating around in the module
        self.exterior_stowage = Stowage(0) #things strapped to the outside of the module
        self.sprite = None 
        self.gravity = np.array([ 0 , 0 , 0 ])
        self.max_gravity = 0.01
        self.min_gravity = 0
        self.orientation = np.array([ math.pi/4 , 0 ])
        self.location = np.array([ 0 , 0 , 0 ])
        self.composition = {'Al' : 14500}      
        self.package_material = [] #if a list of filters, material put in this will not be removed
        self.station = None
        self.manifest=None
        
        self.atmo = Atmosphere()
        self.atmo.volume= math.pi * 2*self.size[0] * pow (self.size[1], 2)   
        self.atmo.initialize('Air')  
        
        self.equipment=dict() #miscellaneous (or unremovable) non-rack equipment
        self.paths = nx.Graph() 
        
        self.nodes=dict()
        
        self.touched = False
        
        self.refresh_image()
     
    def refresh_image(self):
        if not gv.config['GRAPHICS']: return                            
                
        if gv.config['GRAPHICS'] == 'pyglet':           
            self.sprite = util.make_solid_sprite(int(2*self.size[0]*gv.config['ZOOM']),int(2*self.size[1]*gv.config['ZOOM']),(128,128,128,255),None,None,self.location[0],self.location[1], self.orientation[0])
            self.sprite.owner = self
        elif gv.config['GRAPHICS'] == 'cocos2d':
            self.sprite = util.make_solid_sprite(int(2*self.size[0]*gv.config['ZOOM']),int(2*self.size[1]*gv.config['ZOOM']),(128,128,128,255),None,None,self.location[0],self.location[1], self.orientation[0])
            if self.station: self.station.sprite.add(self.sprite)
            
    def new_manifest(self):
        self.manifest = manifest.Manifest(self)    
     
    def search(self, filter_, **kwargs):
        hits=[]
        if "Equipment" in filter_.comparison_type or 'All' in filter_.comparison_type:
            hits.extend([[self.equipment[e][3], self.node( e ), filter_.compare(self.equipment[e][3]) ]  for e in self.equipment.keys() if self.equipment[e][3]])
            
            hits.append( [ self.stowage.search( filter_ ), self.filterNode( self.node('Inside') ), self.stowage.search( filter_ ) != None ] )
            #hits.append( self.exterior_stowage.find_resource( filter_ ) )

        if "Equipment Slot" in filter_.comparison_type or 'All' in filter_.comparison_type:
            hits.extend([[self.equipment[e][2], self.node( e ), filter_.compare(self.equipment[e][2]) ]  for e in self.equipment.keys()  if not self.equipment[e][3]])
 
        if "Clutter" in filter_.comparison_type:
            hits.append( [ self.stowage.search( filter_ ), self.filterNode( self.node('Inside') ), self.stowage.search( filter_ ) != None ] )
            
        random.shuffle(hits)    
        hits.sort(key=lambda tup: tup[2], reverse=True)
        
        return hits[0] if hits and hits[0][2] else [None, None, False]        
                     
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
        #if 'Equipment' not in self.package_material:
        #    for c in self.stowage.contents:
        #        if isinstance(c,Equipment) and not c.installed and not c.task:
        #            c.install_task(self.station)
        if self.manifest: 
            satisfaction = self.manifest.check_satisfied()
            #print satisfaction    
        
    def get_random_dock(self, side_port_allowed=True, unused = True, used = False):
        docks=[]
        if unused: docks.extend([f for f in self.equipment.keys() if self.equipment[f][2] in DOCK_EQUIPMENT and self.equipment[f][3] and not self.equipment[f][3].docked and ( side_port_allowed or not ( '2' in f or '3' in f ) ) and self.equipment[f][3].player_usable ])
        if used: docks.extend([f for f in self.equipment.keys() if self.equipment[f][2] in DOCK_EQUIPMENT and self.equipment[f][3] and self.equipment[f][3].docked and ( side_port_allowed or not ( '2' in f or '3' in f ) ) and self.equipment[f][3].player_usable ])
        if not docks: return None
        return random.choice(docks)    
            
    def get_neighbors(self, equipment=False):
        out=[]
        for e in [f for f in self.equipment.keys() if self.equipment[f][2] in DOCK_EQUIPMENT and self.equipment[f][3] and self.equipment[f][3].docked ]:
            if not equipment:
                out.append(self.equipment[e][3].partner.installed)
            else:
                out.append(self.equipment[e][3])
        return out
        
    def get_neighbor(self,station=None):
        for n in self.get_neighbors():
            if station and n.station == station: return n
        return None
        
    def percolate(self):
        if self.touched: return []
        out = [self]
        self.touched=True
        for n in self.get_neighbors():
            out.extend(n.percolate())
        return out    
            
    def percolate_location(self):
        if self.touched: return
        self.touched = True
        for e in self.get_neighbors(equipment=True):
             #update e's partner's module's location
             n = e.partner.installed
             if not n.touched:                
                n.adjust_location(e.partner.get_name(),self,e.get_name())        
                n.refresh_image()     
             #call n
             n.percolate_location()           
            
    def get_empty_slot(self,slot_type='LSS'):
        slots = [s for s in self.equipment.keys() if ( self.equipment[s][2] == slot_type or slot_type=='ANY' ) and not self.equipment[s][3]]
        if not slots: return None
        return random.choice(slots)
            
    def get_node(self,equip):
        for f in self.equipment.keys():
            if self.equipment[f][3] == equip:
                return self.node(f)
        return None        
            
    def uninstall_equipment(self,equip):
        for f in self.equipment.keys():
            if self.equipment[f][3] == equip:
                self.equipment[f][3] = None
                self.stowage.add( equip )
                return True
        return False                            
        
    def adjust_location(self,my_node,neighbor,their_node):
        self.orientation = ( neighbor.orientation + neighbor.equipment[their_node][1] - self.equipment[my_node][1] ) + np.array([math.pi, 0])
        self.orientation %= 2*math.pi
        
        #calculate location
        self.location=np.array([ 0,0,0 ])
        loc_offset = self.getXYZ(self.equipment[my_node][0])
        self.location = neighbor.getXYZ(neighbor.equipment[their_node][0]) - loc_offset        
        
            
    def dock(self, my_node, neighbor, their_node):
        if not neighbor or not my_node or not their_node: return False, "Docking cancelled: pointers missing" 
        if not my_node in self.equipment or not their_node in neighbor.equipment: return False, "Docking cancelled: wrong module, I guess?"
        if not self.equipment[my_node][2] in DOCK_EQUIPMENT or not neighbor.equipment[their_node][2] in DOCK_EQUIPMENT: return False, "Docking cancelled: requested interface(s) are not docking equipment!"
        if self.equipment[my_node][2] != neighbor.equipment[their_node][2]: return False, "Docking cancelled: incompatible docking mechanisms"
        if self.equipment[my_node][3].docked or neighbor.equipment[their_node][3].docked: return False, "Docking cancelled: at least one module already docked elsewhere"
        
        self.adjust_location(my_node,neighbor,their_node)        
        
        #collision detection   
                        
        if neighbor.station:    
            if not self.station:     
                self.station = neighbor.station 
                self.station.paths.add_nodes_from(self.paths.nodes())
                self.station.paths.add_edges_from(self.paths.edges(data=True))
                self.refresh_station()                
        else:             
            neighbor.station = self.station                                    
            if self.station:
                self.station.paths.add_nodes_from(neighbor.paths.nodes())
                self.station.paths.add_edges_from(neighbor.paths.edges(data=True))
                neighbor.refresh_station()         
                     
        neighbor.refresh_image()    
        self.refresh_image()
            
        return True        
        
    def connect(self, my_node, neighbor, their_node, instant=False):    
        #dock, finally
        self.equipment[my_node][3].dock( neighbor, neighbor.equipment[their_node][3], instant)
        neighbor.equipment[their_node][3].dock( self, self.equipment[my_node][3], instant )
        
    
    def disconnect(self, my_node, their_node, instant=False):    
        #dock, finally
        a = self.equipment[my_node][3].undock( instant )
        b = their_node.undock( instant )
        return a and b
            
        
    def add_edge(self,one,two):
        delta = self.nodes[two] - self.nodes[one] #numpy vector subtraction, I hope
        delta *= self.size
        mag = abs( np.sqrt( np.vdot( delta , delta ) ) )
        self.paths.add_edge(one,two,weight=mag)
        
    def add_edge_list(self,edges):
        for e in range(1,len(edges)):            
            self.add_edge( self.node( edges[ e - 1 ] ), self.node( edges[ e ] ) )
        
    def add_equipment(self, eq_node, eq_obj, eq_coords, hall_node=None, eq_orientation=np.array([ 0 , 0]), eq_type='MISC' ):
        if not hall_node:
            all_nodes = [separate_node(n)[1] for n in self.nodes.keys()]
            hall_nodes = [n for n in all_nodes if not n in self.equipment.keys()]            
            hall_nodes.sort(key=lambda t: util.vec_dist( self.nodes[self.node( t )] , eq_coords ), reverse=False)
            #print [util.vec_dist( self.nodes[self.node( t )] , eq_coords ) for t in hall_nodes]
            hall_node = hall_nodes[0]
        node_coords = self.nodes[ self.node( hall_node ) ] + ( eq_coords - self.nodes[ self.node( hall_node ) ] ) 
        self.nodes[self.node(eq_node)] = node_coords
        self.add_edge( self.node(hall_node), self.node(eq_node) )
        self.equipment[ eq_node ] = [ eq_coords, eq_orientation, eq_type, eq_obj]

    def refresh_station(self, station=None):
        if station and station != self.station: self.station = station
        if gv.config['GRAPHICS'] == 'cocos2d': self.station.sprite.add(self.sprite)
        if self.manifest: self.manifest.refresh_station(self.station)
        for e in self.equipment:            
            if self.equipment[e][3]: 
                self.equipment[e][3].refresh_station()
                
    def draw(self,window):
        zoom=gv.config['ZOOM']
        #self.img.blit(zoom*self.location[0]+window.width // 2, zoom*self.location[1]+window.height // 2, 0)
        self.sprite.draw()
        
        for e in self.equipment.keys():
            if self.equipment[e][3] and self.equipment[e][3].visible:
                l=self.getXYZ(self.equipment[e][0]) 
                #rotimg=self.equipment[e][3].img.get_transform
                self.equipment[e][3].sprite.update_sprite(zoom*l[0], zoom*l[1],-180*(self.equipment[e][1][0]+self.orientation[0])/math.pi)
                #self.equipment[e][3].sprite.set_position(zoom*l[0], zoom*l[1])
                #self.equipment[e][3].sprite.rotation = -180*(self.equipment[e][1][0]+self.orientation[0])/math.pi
                #self.equipment[e][3].sprite.draw()#img.blit(zoom*l[0]+window.width // 2, zoom*l[1]+window.height // 2, 0)
        for c in self.stowage.contents:
            if hasattr(c,'sprite') and hasattr(c,'local_coords') and c.sprite:
                loc_xyz = self.getXYZ( 1.0*c.local_coords )
                c.sprite.set_position(zoom*loc_xyz[0],zoom*loc_xyz[1])
                c.sprite.rotation = (-180/math.pi)*self.orientation[0]
                c.sprite.draw()         


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
        self.imgfile='images/destiny_img.tif'        
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
        stuffrack.filter = ClutterFilter(['Supplies'])
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
