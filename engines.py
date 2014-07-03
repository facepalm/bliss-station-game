
from equipment import Equipment, Machinery, Rack, Storage
import clutter
import util
import atmospherics
from filtering import Searcher, ClutterFilter
     
class Engine(Machinery):
    '''Ancestor to all modern rocket engines, the Engine is best known for its crummy Isp rating'''
    
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/placeholder_engine.tif"
        super(Engine, self).__init__()
        self.in_vaccuum=True #default for rocket engines         
        self.Isp = 300
        self.fuel = 'Kerosene'
        self.oxid = 'LOX'
        
    def update(self,dt):
        super(Engine, self).update(dt)        
        
        
class Thruster(Machinery):
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/placeholder_nodule.tif"
        super(Engine, self).__init__()
        self.in_vaccuum=True #default for rocket engines         
        self.Isp = 300
        self.fuel = 'Kerosene'
        self.oxid = 'LOX'
        self.name = "Thruster"
        
    def update(self,dt):
        super(Engine, self).update(dt)   
                
        
class Merlin_A(Engine):
    def __init__(self):
        if not hasattr(self,'imgfile'): self.imgfile = "images/merlin_engine.tif"
        super(Merlin_A, self).__init__()              
        self.Isp = 450
        self.name = "Merlin A Engine"
        
    def refresh_image(self):     
        super(Merlin_A, self).refresh_image()
        if self.sprite is None: return
        self.sprite.add_layer('Nozzle',util.load_image("images/merlin_engine.tif")) 
        
class KeroseneTank(Storage):
    def __init__(self):   
        if not hasattr(self,'imgfile'): self.imgfile = "images/flammable_fuel.tif"
        super(KeroseneTank, self).__init__()         
        self.filter = ClutterFilter(['Kerosene'])
        self.stowage.capacity = 2.0
        self.stowage.add(clutter.Clutter('Kerosene', mass = 1600, density = 800.0 ))
        self.name = "Fuel tank (Kerosene)"

class OxygenTank(Storage):
    def __init__(self):   
        if not hasattr(self,'imgfile'): self.imgfile = "images/cryo_storage.tif"
        super(OxygenTank, self).__init__()         
        self.filter = ClutterFilter(['LOX'])
        self.stowage.capacity = 2.0
        self.stowage.add(clutter.Clutter('LOX', mass = 2252.0, density = 1146.0 ))
        
        self.name = "Tank (LOX)"
