from generic_module import BasicStationModule
from equipment import CBM, SolarPanel, DOCK_EQUIPMENT

import math
import numpy as np

                                      
class UnityModule(BasicStationModule):
    """ Modeled after the Unity module of the ISS.  Lots and lots and lots of life support. """
    def __init__(self):   
        self.size = np.array([ 5.47 , 4.57 , 4.57 ])
        self.imgfile='images/unity_img.tif'
        BasicStationModule.__init__(self) 
        
        self.composition = {'Al' : 11600}
        
        new_nodes={ self.node('hall0'): np.array([ 0.25 , 0 , 0 ]),
                    self.node('hall1'): np.array([ -0.6, 0 , 0 ]),
                    self.node('CBM2') : np.array([ 0.25, -0.95 , 0 ]),
                    self.node('CBM3') : np.array([ 0.25, 0.95 , 0 ])}
                    
        # merging n dicts with a generator comprehension
        self.nodes = dict(i for iterator in (self.nodes, new_nodes) for i in iterator.iteritems())                    
                    
        self.paths.add_nodes_from([f for f in self.nodes.keys() if not f in self.paths.nodes()])
        self.add_edge(self.node('CBM0'),self.node('hall1'))
        self.add_edge(self.node('hall0'),self.node('hall1'))
        self.add_edge(self.node('hall0'),self.node('CBM2'))
        self.add_edge(self.node('hall0'),self.node('CBM3'))
        self.add_edge(self.node('hall0'),self.node('CBM1'))   
        
        self.equipment['CBM2']= [ np.array([ 0.25 , -1 , 0 ]), np.array([ math.pi/2 , 0]), 'CBM', CBM().install(self)]
        self.equipment['CBM3']= [ np.array([ 0.25 , 1 , 0 ]), np.array([ -math.pi/2 , 0]), 'CBM', CBM().install(self)]
        
        _sampdict = {'port' : [ -0.5, 0, math.pi, 0 ], 'starboard' : [ 0.5 , 0, -math.pi, 0 ],
                     'nadir' : [0, -0.5, 0, -math.pi], 'zenith' : [ 0 , 0.5, 0, math.pi ]}
        for _d in _sampdict.keys():
            for _ex,_x in enumerate([-0.6]):
                self.equipment[ ''.join( [ _d , '0' ] ) ] = [ np.array([ -0.6 , _sampdict[_d][0] , _sampdict[_d][1] ]) , np.array([ _sampdict[_d][2] , _sampdict[_d][3] ]), 'RACK', None ]
                self.nodes[ self.node( ''.join( [ _d , '0' ] ) ) ] = np.array([ -0.6 , _sampdict[_d][0]/2 , _sampdict[_d][1]/2 ])
                self.paths.add_nodes_from([ self.node( ''.join([ _d , '0' ] ) ) ])
                self.add_edge( self.node( ''.join( [ 'hall' , '1' ] ) ) , self.node( ''.join( [ _d , '0' ] ) ) )
                
        
                
        

