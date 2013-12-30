
"""Equipment: most kinds of mechanical shit that does things.  It may need power.  It may take from atmo.  It may open onto space.  It may spontaneously explode.  Equipment is guaranteed to liven up any old party!  Equipment is not for everyone.  Consult your doctor before using equipment."""

from atmospherics import Atmosphere
from tasks import Task, TaskSequence
import clutter

DOCK_EQUIPMENT = ['CBM']

class EquipmentSearch():    
    
    def __init__(self, target, station, extra='', check_storage=False):
        self.target=target
        self.station=station
        self.equipment_targets = {  'Battery' : Battery,
                                    'Toilet' : UniversalToilet }
        self.check_storage = check_storage #if True, will search inside storage equipment as well as loose clutter
        self.extra = extra
    
    def compare(self,obj):
        if isinstance(self.target,str):
            if self.target in self.equipment_targets: 
                return isinstance( obj, self.equipment_targets [ self.target ] )    
            print self.target                 
            return clutter.equals(self.target, obj.name) #must be clutter
        elif isinstance(self.target, clutter.ClutterFilter):
            if self.check_storage and isinstance( obj, Storage ):
                return obj.stowage.find_resource(self.target.compare)
            return self.target.compare(obj) 
        else:
            return obj is self.target
        return False
        
    def search(self):
        if self.target in self.equipment_targets or isinstance(self.target,Equipment):
            return self.station.find_resource('Equipment',check = self.compare) 
        else:            
            tar,loc = self.station.find_resource('Clutter',check = self.compare)
            if not ( tar or loc) and self.check_storage:
                #no free objects, check stored stuff
                tar, loc = self.station.find_resource('Equipment',check = self.compare)  
            return tar, loc
        
class Equipment(object):
    def __init__(self, installed=None):
        self.installed=None #pointer to module if installed, none if loose
        self.mass=100
        self.task=None
        self.power_usage = 0 #in kilowatts
        self.powered = False
        self.in_vaccuum = False #if True, requires EVA to service
        self.volume = 1.3 #m^3
        #basic health stats and such go here, as well as hooking into the task system
        pass
      
    def update(self,dt):
        pass

    def install(self,home):
        if self.installed: return None # "Can't install the same thing twice!"
        self.installed=home
        return self             
        
    def draw_power(self,kilowattage,dt): #kilowatts in per seconds
        if self.installed:            
            self.installed.station.resources.resources['Electricity'].available -= kilowattage*dt/3600
            #TODO add equivalent heat into module
            return kilowattage*dt/3600
        return 0
        
class Window(Equipment): #might even be too basic for equipment, but ah well.
    def __init__(self):
        super(Window, self).__init__()     
        
    def update(self,dt):
        super(Window, self).update(dt)        
        if self.installed and not self.task or self.task.task_ended():
            #stellar observations
            self.task = Task(''.join(['Collect Observational Data']), owner = self, timeout=86400, task_duration = 1800, severity='IGNORABLE', fetch_location_method=EquipmentSearch(self,self.installed.station).search)
            self.installed.station.tasks.add_task(self.task)  
                                   
        
class Machinery(Equipment): #TODO eventual ancestor class for things that need regular maintenance
    def __init__(self):
        super(Machinery, self).__init__()              
        
        
#miscellaneous equipment
class Storage(Equipment):
    def __init__(self):
        super(Storage, self).__init__()         
        self.stowage = clutter.Stowage(1) #things floating around in the rack
        self.filter = clutter.ClutterFilter('All')
        self.space_trigger = 0.1 #free volume
        
    def update(self,dt):
        #print 'Available storage: ',self.available_space
        super(Storage, self).update(dt)
        self.stowage.update(dt)
        if self.installed and (not self.task or self.task.task_ended()) and \
                            self.get_available_space() >= self.space_trigger:
            #find stuff to store    
            #sequence! 
            #Task 1: find stuff to store, go to, pick up  #Task 2: find self, go to, deposit
            self.task = TaskSequence(name = ''.join(['Store ',self.filter.target]), severity = "LOW")
            self.task.add_task(Task(name = ''.join(['Pick Up ',self.filter.target]), severity = "LOW", timeout = 86400, task_duration = 30, fetch_location_method=EquipmentSearch(self.filter,self.installed.station).search, owner=clutter.JanitorMon(self.filter.target)))
            self.task.add_task(Task(name = ''.join(['Put Away ',self.filter.target]), severity = "LOW", timeout = 86400, task_duration = 30, fetch_location_method=EquipmentSearch(self,self.installed.station).search, owner=self))
            self.installed.station.tasks.add_task(self.task)
        
    def get_available_space(self): return self.stowage.free_space       
    available_space = property(get_available_space, None, None, "Available storage space" )    
    
    def task_work_report(self,task,dt):
        if task.name.startswith('Put Away'):
            item = task.assigned_to.inventory.find_resource(lambda x: self.filter.compare(x))
            if not item: return
            remove_amt = min(clutter.gather_rate*dt*item.density,self.available_space*item.density,item.mass)
            if remove_amt <= 0: return         
            obj = item.split(remove_amt)
            self.stowage.add(obj)       
            
    def task_finished(self,task):
        self.update(0)         

#delicate equipment        
class UniversalToilet(Machinery):
    def __init__(self):   
        super(UniversalToilet, self).__init__() 
        self.solid_waste = 0
        self.liquid_waste = 0 
        self.gray_water = 0
        self.capacity = 1 # m^3, shared between both
        self.gray_water_capacity = 0.25 #m^3
        self.processing_speed = 0.01

    def deposit(self,amt1,amt2):
        self.solid_waste += amt2
        self.liquid_waste += amt1
        if self.solid_waste/714.33 + self.liquid_waste/1000 > self.capacity: #ohhhh shiiiiii
            pass #TODO replace with bad things happening
        
    def update(self,dt):
        super(UniversalToilet, self).update(dt)    
        if self.installed and self.liquid_waste > 0:
            if not self.draw_power(0.03,dt): return
            proc_amt = max( 0, self.liquid_waste - self.processing_speed)
            if self.gray_water_capacity - self.gray_water < proc_amt: return # water tank is full
            self.liquid_waste -= proc_amt
            self.gray_water += proc_amt
        
#docking equipment        
class DockingRing(Equipment):
    def __init__(self):   
        super(DockingRing, self).__init__()     
        self.docked = None #a pointer to the module we've docked to
        self.open = False
        self.in_vaccuum = True
        self.partner = None #a pointer to the docking equipment partner
        
    #these two need to generate tasks for unpowered rings
    def open_(self):
        if self.open: return
        if not self.docked: return False, "What are you, nuts?!"
        self.open = True
        
    def close_(self):
        self.open=False
        
    def dock(self, target, instant = False):
        self.docked=target        
        if instant: 
            self.open_()
        else:
            self.task = Task(''.join(['Open Hatch']), owner = self, timeout=86400, task_duration = 300, severity='LOW', fetch_location_method=EquipmentSearch(self,self.installed.station).search)
            self.installed.station.tasks.add_task(self.task)
        self.in_vaccuum = False
                
    def undock(self, instant = False):
        if self.open: 
            if instant:
                self.close_()
            else:
                #TODO check and add a task for disconnecting the pipes
                self.task = Task(''.join(['Close Hatch']), owner = self, timeout=86400, task_duration = 300, severity='LOW', fetch_location_method=EquipmentSearch(self,self.installed.station).search)
                self.installed.station.tasks.add_task(self.task)
        self.docked = None
        self.in_vaccuum = True
        
    def task_finished(self,task):
        if task.name == 'Close Hatch': 
            #TODO check for someone in the other module
            self.close_()
        elif task.name == 'Open Hatch':
            self.open_()
            #TODO add a task to connect pipes, open other side
        
class CBM(DockingRing):
    def __init__(self):   
        super(CBM, self).__init__()     
        self.active = False
     
#specialized, installed, single-purpose equipment
class SolarPanel(Equipment):
    def __init__(self):   
        super(SolarPanel, self).__init__()         
        self.extended = False
        self.in_vaccuum = True
        self.capacity= 5 #kW
        
    def update(self,dt):
        super(SolarPanel, self).update(dt)    
        if self.installed and self.extended:
            self.installed.station.resources.resources['Electricity'].available += self.capacity*dt/3600.0

class Battery(Equipment):
    def __init__(self):   
        super(Battery, self).__init__()
        self.type = 'Li-ion'
        self.capacity = 100     #kilowatt-hours            
        self.charge = 0         #kilowatt-hours
        self.discharge_rate = 2 #kilowatts
        self.efficiency = 0.95
                
    def update(self,dt): #TODO add time calculations
        super(Battery, self).update(dt)
        if self.installed:
            power_situation = self.installed.station.resources.resources['Electricity'].previously_available
            if power_situation > 0:
                _charge = min(power_situation, dt * self.discharge_rate) if self.charge < self.capacity else 0
                self.charge += self.efficiency * _charge / 3600
            else:
                _charge = max(power_situation, -dt * self.discharge_rate) if self.charge > 0 else 0
                self.charge += _charge / 3600
            self.installed.station.resources.resources['Electricity'].available -= _charge
        #print _charge, self.charge, self.capacity
     
#rack equipment            
class Rack(Equipment):
    def __init__(self):   
        super(Rack, self).__init__()                    
        self.mass=104
       
    def update(self,dt):
        pass
        
class O2TankRack(Rack): #about a 1m^3 tank in ISPR rack form
    def __init__(self):   
        super(O2TankRack, self).__init__()                    
        self.mass += 100
        self.atmo=Atmosphere()
        #self.volume=1
        self.active = False
        self.atmo.initialize("O2 Tank")
        
    def update(self,dt):
        super(O2TankRack, self).update(dt)
        if self.installed and hasattr(self.installed, 'atmo') and self.active:
            self.atmo.equalize(self.installed.atmo)                 
        
class BatteryBank(Rack, Battery):
    def __init__(self):   
        super(BatteryBank, self).__init__()         
        self.capacity = 50 #kilowatt-hours      
        self.mass += 450                  
        
    def update(self,dt):
        Battery.update(self,dt)    
        

class WaterTank(Storage):
    def __init__(self):   
        super(WaterTank, self).__init__()         
        self.filter = clutter.ClutterFilter('Potable Water')
        self.stowage.capacity = 0.5

class FoodStorageRack(Storage,Rack):
    def __init__(self):   
        super(FoodStorageRack, self).__init__()         
        self.filter = clutter.ClutterFilter('Food')
        self.space_trigger = 0.5 #free volume, m^3   

class WaterStorageRack(WaterTank,Rack):
    def __init__(self):   
        super(WaterStorageRack, self).__init__()                 
        self.space_trigger = 0.5 #free volume, m^3   
                    
class MysteryBoxRack(Rack):
    '''Mysterious box of boxy mystery.  Dare you enter its magical realm?'''
    
    def __init__(self):
        super(MysteryBoxRack, self).__init__()         
        
    def update(self,dt):
        super(MysteryBoxRack, self).update(dt)        
        if self.installed and not self.task or self.task.task_ended():
            #work on the box    
            self.task = Task(''.join(['Stare at Mystery Box']), owner = self, timeout=86400, task_duration = 86400, severity='LOW', fetch_location_method=EquipmentSearch(self,self.installed.station).search)
            self.installed.station.tasks.add_task(self.task)
                    
            
