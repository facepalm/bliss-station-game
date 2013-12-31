

from generic_module import BasicStationModule
from equipment import SolarPanel, DOCK_EQUIPMENT, WaterTank, CBM, UniversalToilet, Window

import math
import numpy as np

                                      
class ZvezdaModule(BasicStationModule):
    """ Modeled after the Zvezda module of the ISS.  Lots and lots and lots of life support. """
    def __init__(self):   
        BasicStationModule.__init__(self) 
        self.size = np.array([ 13.1 , 4.15 , 4.15 ])
        self.composition = { 'Al' : 20400 }
        
        new_nodes={ self.node('hall0'): np.array([ -0.6, 0 , 0 ]),
                    self.node('hall1'): np.array([ 0.4, 0 , 0 ]),
                    self.node('hall2'): np.array([ 0.8, 0 , 0 ]),
                    self.node('CBM2') : np.array([ 0.8, -0.95 , 0 ]),
                    self.node('CBM3') : np.array([ 0.8, 0.95 , 0 ]),
                    self.node('Water1') : np.array([ 0, 0.25 , 0 ]),
                    self.node('Toilet1') : np.array([   0, -0.35 , -0.1 ]),
                    self.node('Window01'): np.array([ 0.3,  0.1 , -0.1 ]),
                    self.node('Window02'): np.array([ 0.3, -0.1 , -0.1 ]),
                    self.node('Window11'): np.array([ 0.4, 0 , -0.1 ]),
                    self.node('Window12'): np.array([ 0.1, 0 , -0.1 ]),
                    self.node('Window21'): np.array([ 0.5,  0.1 , -0.1 ]),
                    self.node('Window22'): np.array([ 0.5, -0.1 , -0.1 ])
                    }
                    
        # merging n dicts with a generator comprehension
        self.nodes = dict(i for iterator in (self.nodes, new_nodes) for i in iterator.iteritems())                    
                    
        self.paths.add_nodes_from([f for f in self.nodes.keys() if not f in self.paths.nodes()])
        self.add_edge_list(['CBM0','hall0','hall1','hall2','CBM1'])   
        self.add_edge(self.node('CBM0'),self.node('CBM1'))
        self.add_edge(self.node('hall2'),self.node('CBM2'))
        self.add_edge(self.node('hall2'),self.node('CBM3'))   
        self.add_edge(self.node('Water1'),self.node('hall1'))
        self.add_edge(self.node('Toilet1'),self.node('hall1'))
        self.add_edge(self.node('Window01'),self.node('hall1'))
        self.add_edge(self.node('Window02'),self.node('hall1'))
        self.add_edge(self.node('Window12'),self.node('hall1'))
        self.add_edge(self.node('Window12'),self.node('hall1'))
        self.add_edge(self.node('Window21'),self.node('hall1'))
        self.add_edge(self.node('Window22'),self.node('hall1'))
        
        self.equipment['CBM2']= [ np.array([ 0.8 , -1 , 0 ]), np.array([ math.pi/2 , 0]), 'CBM', CBM().install(self)]
        self.equipment['CBM3']= [ np.array([ 0.8 , 1 , 0 ]), np.array([ -math.pi/2 , 0]), 'CBM', CBM().install(self)]        
        
        self.equipment['Solars0']= [ np.array([ 0 , 1 , 0 ]), np.array([ math.pi , 0]), 'SOLAR', SolarPanel().install(self)]
        self.equipment['Solars1']= [ np.array([ 0 , -1 , 0 ]), np.array([ -math.pi , 0]), 'SOLAR', SolarPanel().install(self)]
        
        self.equipment['Water1']= [ np.array([ 0 , 0.5 , 0 ]), np.array([ math.pi , 0]), 'LSS', WaterTank().install(self)]
        self.equipment['Toilet1']= [ np.array([ 0 , -0.5 , 0 ]), np.array([ math.pi , 0]), 'LSS', UniversalToilet().install(self)]
        
        self.equipment['Window01'] = [ np.array([ 0.3 , 0.1 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window02'] = [ np.array([ 0.3 , -0.1 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window11'] = [ np.array([ 0.4 , 0 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window12'] = [ np.array([ 0.1 , 0 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window21'] = [ np.array([ 0.5 , 0.1 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window22'] = [ np.array([ 0.5 , 0.1 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        
        
        self.equipment['Solars0'][3].extended=True
        self.equipment['Solars1'][3].extended=True        
        

