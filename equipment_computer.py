
from equipment import Equipment, Machinery, EquipmentSearch, Rack
import clutter
import util
import atmospherics

     
class Computer(Equipment):
    '''Progenitor class for non-moving computery bits'''
    
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/placeholder_computer.tif"
        super(Computer, self).__init__()              
        self.idle_draw = 0.100 #kW

    def update(self,dt):            
        super(Computer, self).update(dt)

class DockingComputer(Computer, Rack):
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/docking_computer.tif"
        super(DockingComputer, self).__init__()              
        self.idle_draw = 0.200 #kW
