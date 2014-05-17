

from generic_module import BasicStationModule
from equipment import SolarPanel, DOCK_EQUIPMENT, WaterTank, CBM, Window, Battery
from lifesupport import UniversalToilet, WaterPurifier, OxygenElectrolyzer, RegenerableCO2Filter
from equipment_computer import DockingComputer

import math
import numpy as np
from filtering import ClutterFilter

                                      
class ZvezdaModule(BasicStationModule):
    """ Modeled after the Zvezda module of the ISS.  Lots and lots and lots of life support. """
    def __init__(self):   
        #self.imgfile='images/zvezda_img.tif'
        self.size = np.array([ 13.1 , 4.15 , 4.15 ])
        BasicStationModule.__init__(self)         
        self.composition = { 'Al' : 20400 }
        
        new_nodes={ self.node('hall0'): np.array([ -0.6, 0 , 0 ]),
                    self.node('hall1'): np.array([ 0.4, 0 , 0 ]),
                    self.node('hall2'): np.array([ 0.8, 0 , 0 ]),
                    self.node('CBM2') : np.array([ 0.7, -0.95 , 0 ]),
                    self.node('CBM3') : np.array([ 0.7, 0.95 , 0 ]),
                    self.node('Water1') : np.array([ 0, 0.5 , 0 ]),
                    self.node('Toilet1') : np.array([   0, -0.35 , -0.1 ]),
                    self.node('Window01'): np.array([ 0.3,  0.1 , -0.1 ]),
                    self.node('Window02'): np.array([ 0.3, -0.1 , -0.1 ]),
                    self.node('Window11'): np.array([ 0.4, 0 , -0.1 ]),
                    self.node('Window12'): np.array([ 0.1, 0 , -0.1 ]),
                    self.node('Window21'): np.array([ 0.5,  0.1 , -0.1 ]),
                    self.node('Window22'): np.array([ 0.5, -0.1 , -0.1 ]),
                    self.node('H2OStill'): np.array([ -0.2,  -0.35 , 0 ]),
                    self.node('Electrolyzer'): np.array([ -0.2,  0.35 , 0 ]),
                    self.node('CO2Filter'): np.array([ -0.3,  0.35 , 0 ]),
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
        self.add_edge(self.node('Window11'),self.node('hall1'))
        self.add_edge(self.node('Window12'),self.node('hall1'))
        self.add_edge(self.node('Window21'),self.node('hall1'))
        self.add_edge(self.node('Window22'),self.node('hall1'))
        self.add_edge(self.node('H2OStill'),self.node('hall0'))
        self.add_edge(self.node('Electrolyzer'),self.node('hall0'))        
        self.add_edge(self.node('CO2Filter'),self.node('hall0'))       
        
        self.equipment['CBM2']= [ np.array([ 0.7 , -1 , 0 ]), np.array([ -math.pi/2 , 0]), 'CBM', CBM().install(self)]
        self.equipment['CBM3']= [ np.array([ 0.7 , 1 , 0 ]), np.array([ math.pi/2 , 0]), 'CBM', CBM().install(self)]        
        
        self.equipment['Solars0']= [ np.array([ 0 , 1 , 0 ]), np.array([ math.pi/2 , 0]), 'SOLAR', SolarPanel().install(self)]
        self.equipment['Solars1']= [ np.array([ 0 , -1 , 0 ]), np.array([ -math.pi/2 , 0]), 'SOLAR', SolarPanel().install(self)]
        
        self.equipment['Water1']= [ np.array([ 0 , 0.5 , 0 ]), np.array([ math.pi , 0]), 'LSS', WaterTank().install(self)]
        self.equipment['Toilet1']= [ np.array([ 0 , -0.5 , 0 ]), np.array([ -math.pi , 0]), 'LSS', UniversalToilet().install(self)]
        
        self.equipment['Window01'] = [ np.array([ 0.3 , 0.2 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window02'] = [ np.array([ 0.3 , -0.2 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window11'] = [ np.array([ 0.4 , 0 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window12'] = [ np.array([ 0.1 , 0 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window21'] = [ np.array([ 0.5 , 0.2 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        self.equipment['Window22'] = [ np.array([ 0.5 , -0.2 , -0.15 ]), np.array([ 0 , -math.pi]), 'WINDOW', Window().install(self)]
        
        self.equipment['H2OStill'] = [ np.array([ -0.2 , -0.35 , 0 ]), np.array([ 0 , 0]), 'LSS', WaterPurifier().install(self)]
        self.equipment['Electrolyzer'] = [ np.array([ -0.2 , 0.35 , 0 ]), np.array([ 0 , 0]), 'LSS', OxygenElectrolyzer().install(self)]
        self.equipment['CO2Filter'] = [ np.array([ -0.3 , 0.35 , 0 ]), np.array([ 0 , 0]), 'LSS', RegenerableCO2Filter().install(self)]
        
        self.add_equipment('Docking Console', DockingComputer().install(self), np.array([ -0.5 , 0.35 , 0 ]), eq_type='CONSOLE' )
        self.add_equipment('BackupBattery', Battery().install(self), np.array([ -0.6 , 0.35 , 0 ]), eq_type='ELECTRICAL' )
        self.equipment['BackupBattery'][3].capacity = 3
        self.equipment['BackupBattery'][3].visible = False
        
        graytank = WaterTank().install(self)
        graytank.filter = ClutterFilter(['Gray Water'])
        graytank.imgfile = "images/gray_water.tif"
        graytank.refresh_image()
        self.add_equipment('Gray W Tank', graytank, np.array([ -0.4 , 0.35 , 0 ]), 'hall0', eq_type = 'LSS' )
                
        self.equipment['Solars0'][3].extended=True
        self.equipment['Solars1'][3].extended=True        
        

