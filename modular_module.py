
from generic_module import BasicModule
from equipment import SolarPanel, DOCK_EQUIPMENT, WaterTank, CBM, Window, Battery, Comms
from lifesupport import UniversalToilet, WaterPurifier, OxygenElectrolyzer, RegenerableCO2Filter
from equipment_computer import DockingComputer, MissionComputer

import math
import numpy as np
from filtering import ClutterFilter
import util

import globalvars as gv


class ModuleComponent(object):
    def __init__(self,pos = 0):
        self.size = np.array([ 1 , 4.27 , 4.27 ])
        self.sprite = None
        self.nodes = []
        self.equipment = []
        self.edges = []
        self.nodes.append(['hall'+str(pos),[0,0,0]])
        self.entry_node = 'hall'+str(pos)
        self.exit_node = 'hall'+str(pos)
                
    def refresh_image(self, imgfile, x_off = 0):     
        if self.sprite is None: return
        img = util.load_image(imgfile,anchor_x= int(gv.config['ZOOM'] * 2 * x_off))                
        
        self.sprite.add_layer(self.name,img)
        
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['sprite']
        return d    
                
class DockingCap(ModuleComponent):
    def __init__(self,pos=0):
        self.name = 'OpenDock'+str(pos)
        ModuleComponent.__init__(self,pos)
        self.equipment.append( [ 'CBM'+str(pos), np.array([ -1 , 0 , 0 ]), np.array([ math.pi , 0]), 'CBM', CBM() ] )
        #self.edges.append( [  ''.join(['hall',str(pos)])  ,  ''.join(['CBM',str(pos)])  ] )
        
    def refresh_image(self, x_off = 0):     
        super(DockingCap, self).refresh_image('images/dockcap_comp_flip.png',x_off)

class DockingCapClosed(DockingCap):
    def __init__(self,pos=0):
        DockingCap.__init__(self,pos)
        self.equipment[0][1] = np.array([ 1 , 0 , 0])
        self.equipment[0][2] = np.array([ 0 , 0])

    def refresh_image(self, x_off = 0):     
        super(DockingCap, self).refresh_image('images/dockcap_comp.png',x_off)


class DockingHub(ModuleComponent):
    def __init__(self,pos=0):
        self.name = 'OpenDock'+str(pos)
        ModuleComponent.__init__(self,pos)
        self.size = np.array([ 2 , 4.27 , 4.27 ])
        self.equipment.append( [ 'CBM-L'+str(pos), np.array([ 0 , 1 , 0 ]), np.array([ math.pi/2 , 0]), 'CBM', CBM() ] )
        self.equipment.append( [ 'CBM-R'+str(pos), np.array([ 0 , -1 , 0 ]), np.array([ -math.pi/2 , 0]), 'CBM', CBM() ] )
        #self.edges.append( [  ''.join(['hall',str(pos)])  ,  ''.join(['CBM',str(pos)])  ] )
        
    def refresh_image(self, x_off = 0):     
        super(DockingHub, self).refresh_image('images/double_comp.png',x_off)

                    
class RackRing(ModuleComponent):
    def __init__(self,pos=0):
        self.name = 'Rack ring'+str(pos)
        ModuleComponent.__init__(self,pos)
        _sampdict = {'port' : [ -0.5, 0, math.pi, 0 ], 'starboard' : [ 0.5 , 0, -math.pi, 0 ], 'nadir' : [0, -0.5, 0, -math.pi]}
        for _d in _sampdict.keys():
            self.equipment.append([ ''.join( [ _d , str( pos ) ] ), np.array([ 0 , _sampdict[_d][0] , _sampdict[_d][1] ]) , np.array([ _sampdict[_d][2] , _sampdict[_d][3] ]), 'RACK', None ])
            #self.edges.append( [ ''.join( [ 'hall' , str( pos ) ] ) , ''.join( [ _d , str( pos ) ] ) ] )
        
    
    def refresh_image(self, x_off = 0):     
        super(RackRing, self).refresh_image('images/rack_comp.tif',x_off)
    
        

def spawn_component(letter,pos=0):
    if letter in '{':
        return DockingCap(pos)
    elif letter in '}':
        return DockingCapClosed(pos)
    elif letter in 'r':
        return RackRing(pos)
    elif letter in 'O':
        return DockingHub(pos)


class ModularModule(BasicModule):
    def __init__(self,name = "Module", build_str = "{rrOrr}" ):   
        self.component_string = build_str
        self.components=[]
        self.name=name
        for ec,c in enumerate(self.component_string):
            newc = spawn_component(c,ec)
            if not newc is None: self.components.append(newc)    
        self.refresh_size()
        BasicModule.__init__(self)
        x_off = -self.size[0]/2
        path_node = None
        for c in self.components:            
            for n in c.nodes:
                self.nodes[self.node(n[0])] = 2*(np.array([x_off,0,0]) + c.size*(n[1]+np.array([1,1,1]))/2 )/self.size
            for e in c.equipment:
                #self.add_equipment(e[0], e[4].install(self) if e[4] else None, e[1], eq_orientation=e[2], eq_type=e[3] )
                loc = np.array([2,1,1])*(np.array([x_off,0,0]) + c.size*(e[1]+np.array([1,0,0]))/np.array([2,1,1]) )/self.size
                
                self.add_equipment(e[0], e[4].install(self) if e[4] else None, loc, eq_orientation=e[2], eq_type=e[3] )
            for e in c.edges:
                self.add_edge(e[0],e[1])                       
            if path_node:
                self.add_edge( self.node(path_node), self.node(c.entry_node) )
            path_node = c.exit_node                
            x_off += c.size[0]
        print [e for e in self.equipment.values() if e[3]]
        #quit()
        self.refresh_image()
        
    def refresh_size(self):
        x,y,z = 0,0,0      
        for c in self.components:      
            x += c.size[0]
            y = max(y,c.size[1])
            z = max(z,c.size[2])
        self.size = np.array([ x , y , z ])

    def refresh_image(self):
        if not gv.config['GRAPHICS']: return
        if gv.config['GRAPHICS'] == 'pyglet':        
            import graphics_pyglet
            if self.sprite: self.sprite.delete()
            self.sprite = graphics_pyglet.LayeredSprite(name=self.name,start_order = -20)
            x_off = -self.size[0]/2
            for c in self.components:
                x_off += c.size[0]
                c.sprite = self.sprite
                c.refresh_image(x_off)
            
