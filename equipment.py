
"""Equipment: most kinds of mechanical shit that does things.  It may need power.  It may take from atmo.  It may open onto space.  It may spontaneously explode.  Equipment is guaranteed to liven up any old party!  Equipment is not for everyone.  Consult your doctor before using equipment."""

from atmospherics import Atmosphere
from tasks import Task, TaskSequence
import clutter
import util
import random

DOCK_EQUIPMENT = ['CBM']


class EquipmentSearch():    
    
    def __init__(self, target, station, check_storage=False, resource_obj=None, storage_filter='Any'):
        self.target=target
        self.station=station
        self.equipment_targets = util.equipment_targets
        self.check_storage = check_storage #if True, will search inside storage equipment as well as loose clutter
        self.required_resource = resource_obj #if not None, will require w/e to be in a station sharing the res obj
        self.storage_filter = storage_filter # will check the filter of any storage eq
    
    def compare(self,obj):
        if self.required_resource: #if we're looking to draw or give via a specific resource, check for that
            if hasattr(obj,'installed'):
                if not obj.installed: return False
                if not obj.installed.station: return False
                if not obj.installed.station.resources == self.required_resource: return False
                
        if isinstance(self.target, str): #TODO pull this out into a separate EquipmentFilter, a la ClutterFilter
            if self.target == 'Storage' and isinstance( obj, Storage):
                #print self.storage_filter, obj.filter.target
                return self.storage_filter in obj.filter.target or self.storage_filter == 'Any'
            elif self.target in self.equipment_targets: 
                return isinstance( obj, self.equipment_targets [ self.target ] )    
            elif self.target == 'Equipment Slot':
                return obj == self.storage_filter              
            #print self.target                 
            #return clutter.equals(self.target, obj.name) #must be clutter
        elif isinstance(self.target, clutter.ClutterFilter):
            if self.check_storage and isinstance( obj, Storage ):
                return obj.stowage.find_resource(self.target.compare)
            return self.target.compare(obj) 
        else:
            return obj is self.target
        return False
        
    def search(self):
        if self.target in self.equipment_targets or isinstance(self.target,Equipment):
            tar,loc = self.station.find_resource('Equipment',check = self.compare) 
            if not ( tar or loc) and self.check_storage: #no installed eq, check free objects
                tar, loc = self.station.find_resource('Clutter',check = self.compare)              
            #print "Task location",tar,loc, self.target
        elif self.target == 'Equipment Slot':
            tar,loc = self.station.find_resource('Equipment Slot',check = self.compare)             
        else:            
            tar,loc = self.station.find_resource('Clutter',check = self.compare)
            if not ( tar or loc) and self.check_storage: #no free objects, check stored stuff
                tar, loc = self.station.find_resource('Equipment',check = self.compare)  
        return tar, loc
        
class Equipment(object):
    def __init__(self, installed=None, logger=util.generic_logger):
        self.installed=None #pointer to module if installed, none if loose
        self.mass=100
        self.task=None
        self.power_usage = 0 #in kilowatts
        self.powered = False
        self.in_vaccuum = False #if True, requires EVA to service
        self.volume = 1.3 #m^3
        self.name = 'Equipment'
        self.type = 'Misc'
        self.logger=logger
        #basic health stats and such go here, as well as hooking into the task system
        pass
      
    def update(self,dt):
        if self.task and self.task.task_ended(): self.task = None

    def install(self,home,loc=None):
        if self.installed: return None # "Can't install the same thing twice!"
        self.installed=home
        if loc: self.installed.equipment[loc][3] = self
        self.logger.debug(''.join([self.name," installed in ",self.installed.id,' at ',str(loc)]))
        return self             

    def uninstall(self):
        if not self.installed: return None # "Can't install the same thing twice!"
        worked = self.installed.uninstall_equipment(self)
        self.installed=None
        return worked
        
    def draw_power(self,kilowattage,dt): #kilowatts in per seconds
        if self.installed and (not hasattr(self,'broken') or not self.broken): #it's installed, not broken or can't break          
            self.installed.station.resources.resources['Electricity'].available -= kilowattage*dt/3600
            #TODO add equivalent heat into module
            return kilowattage*dt/3600
        return 0
        
    def task_finished(self,task):
        if task:
            if task.name == "Install" and not self.installed:
                if task.assigned_to.held == self:
                    task.assigned_to.held = None
                else:
                    print "Object not held!"
                self.installed = task.station.get_module_from_loc(task.location)
                self.installed.equipment[task.location.split('|')[1]][3] = self      
            elif task.name == 'Pick Up':
                
                if self.installed: 
                    assert self.uninstall(), 'Unknown error after uninstallation'             
                print task.location   
                module = task.station.get_module_from_loc(task.location)
                print module.stowage.contents
                assert module.stowage.remove(self), 'Equipment not found in targeted module'
                task.assigned_to.held=self

    def task_failed(self,task):
        pass     
        
    def install_task(self,station):
        if self.installed or not station: return
        self.task = TaskSequence(name = ''.join(['Install Equipment']), severity = "LOW")
        self.task.station = station
        self.task.add_task(Task(name = ''.join(['Pick Up']), owner = self, timeout=86400, task_duration = 60, severity='LOW', fetch_location_method=EquipmentSearch(self,station,check_storage=True).search,station=station))
        self.task.add_task(Task(name = ''.join(['Install']), owner = self, timeout=86400, task_duration = 600, severity='LOW', fetch_location_method=EquipmentSearch("Equipment Slot",station,storage_filter=self.type).search,station=station))
        station.tasks.add_task(self.task)
        
        
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
        self.idle_draw = 0.001 #kW
        self.maint_timer = random.randrange(0, util.seconds(6,'months') )
        self.maint_task = None
        self.wear = 1.0
        self.broken = False
                
    def update(self,dt):
        super(Machinery, self).update(dt)           
        if self.broken:
            if not self.maint_task or self.maint_task.name != ''.join(['Repair ',self.name]):
                self.maint_task = Task(''.join(['Repair ',self.name]), owner = self, timeout=util.seconds(1,'months'), task_duration = util.seconds(4,'hours'), severity='MODERATE', fetch_location_method=EquipmentSearch(self,self.installed.station).search)
                self.installed.station.tasks.add_task(self.maint_task)
        if self.maint_timer < 0 and ( not self.maint_task or self.maint_task.task_ended() ):
            self.maint_task = Task(''.join(['Maintain ',self.name]), owner = self, timeout=util.seconds(1,'months'), task_duration = util.seconds(1,'hours'), severity='LOW', fetch_location_method=EquipmentSearch(self,self.installed.station).search)
            print self.maint_task.timeout,self.maint_task.task_duration
            self.installed.station.tasks.add_task(self.maint_task)
        
        self.maint_timer -= dt
        
    def task_finished(self,task): #TODO add supply usage
        super(Machinery, self).task_finished(task) 
        if not task: return
        if task.name == ''.join(['Maintain ',self.name]) and task.target == self:
            self.maint_task = None
            self.maint_timer = random.randrange(int (util.seconds(1,'months') * self.wear), int( util.seconds(6,'months') * self.wear ) )
        elif task.name == ''.join(['Repair ',self.name]) and task.target == self:
            self.broken = False
            self.wear += (1 - self.wear) / 2        

    def task_failed(self,task):
        super(Machinery, self).task_failed(task)
        if not task: return
        if task.name == ''.join(['Maintain ',self.name]) and task.target == self:
            self.wear -= 0.05
            if random.random() > self.wear:
                self.broken = True
        
#miscellaneous equipment
class Storage(Equipment):
    def __init__(self):
        super(Storage, self).__init__()         
        self.stowage = clutter.Stowage(1) #things floating around in the rack
        self.filter = clutter.ClutterFilter(['All'])
        self.space_trigger = 0.1 #free volume
        
    def update(self,dt):
        #print 'Available storage for ',self.filter.target_string(),': ',self.available_space
        super(Storage, self).update(dt)
        self.stowage.update(dt)        
        #if self.task: print self.task.name
        if self.installed and (not self.task or self.task.task_ended()) and \
                            self.get_available_space() >= self.space_trigger:
            #find stuff to store    
            #sequence! 
            #Task 1: find stuff to store, go to, pick up  #Task 2: find self, go to, deposit
            filter_str = self.filter.target_string()
            self.task = TaskSequence(name = ''.join(['Store ',filter_str]), severity = "LOW")
            self.task.add_task(Task(name = ''.join(['Pick Up ',filter_str]), severity = "LOW", timeout = 86400, task_duration = 30, fetch_location_method=EquipmentSearch(self.filter,self.installed.station).search, owner=clutter.JanitorMon(self.filter.target)))
            self.task.add_task(Task(name = ''.join(['Put Away ',filter_str]), severity = "LOW", timeout = 86400, task_duration = 30, fetch_location_method=EquipmentSearch(self,self.installed.station).search, owner=self))
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
        super(Storage, self).task_finished(task) 
        self.update(0)         

        
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
        super(DockingRing, self).task_finished(task) 
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
        self.type='RACK'
       
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
        self.filter = clutter.ClutterFilter(['Potable Water'])
        self.stowage.capacity = 0.5

class FoodStorageRack(Storage,Rack):
    def __init__(self):   
        super(FoodStorageRack, self).__init__()         
        self.filter = clutter.ClutterFilter(['Edible Food'])
        self.space_trigger = 0.5 #free volume, m^3   

class GenericStorageRack(Storage,Rack):
    def __init__(self):   
        super(GenericStorageRack, self).__init__()         
        self.filter = clutter.ClutterFilter(['Any'])
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
                    
util.equipment_targets['Battery'] = Battery
util.equipment_targets['Storage'] = Storage

