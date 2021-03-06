
"""Equipment: most kinds of mechanical shit that does things.  It may need power.  It may take from atmo.  It may open onto space.  It may spontaneously explode.  Equipment is guaranteed to liven up any old party!  Equipment is not for everyone.  Consult your doctor before using equipment."""

from atmospherics import Atmosphere
from tasks import Task, TaskSequence
from filtering import ClutterFilter, NeedFilter, EquipmentFilter, Searcher, SearchFilter
import clutter
import util
import logging
import random
import numpy as np
import globalvars as gv

DOCK_EQUIPMENT = ['CBM']
        
class Equipment(object):
    def __init__(self, installed=None, logger=None, name='UnspecifiedEquipment'):
        self.id=util.register(self)

        self.components = [] #list of items used to build this equipment
            
        self.installed=None #pointer to module if installed, none if loose
        self.mass=100
        self.task=None
        self.power_usage = 0 #in kilowatts        
        self.powered = False
        self.idle_draw = 0 #in kilowatts
        self.in_vaccuum = False #if True, requires EVA to service       
        self.volume = 1.3 #m^3
        self.broken = False
        self.name = name
        self.type = 'Misc'
        self.satisfies = dict() #what qualities can this equipment provide?
        self.logger = logging.getLogger(logger.name + '.' + self.name) if logger else util.generic_logger
        self.loggername = self.logger.name
        self.visible = True
        self.local_coords = 0.75*np.array([random.uniform(-1,1),random.uniform(-1,1),0])
        
        self.sprite=None
        #basic health stats and such go here, as well as hooking into the task system
        
        #if not hasattr(self,'imgfile'): self.imgfile = "images/placeholder_equipment.tif"
        self.refresh_image()    
        
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        del d['sprite']
        #if 'docked' in d: d.pop('docked')
        return d    
        
    def __setstate__(self, d):
        self.__dict__.update(d)   
        self.logger = logging.getLogger(self.loggername) if self.loggername else util.generic_logger    
        self.sprite=None
        self.refresh_image()
     
    def refresh_image(self):
        if not gv.config['GRAPHICS']: return
        if gv.config['GRAPHICS'] == 'pyglet':        
            import graphics_pyglet
            if self.sprite: self.sprite.delete()
            self.sprite = graphics_pyglet.LayeredSprite(name=self.name)
            self.sprite.add_layer('Equipment',util.make_solid_image(40,40,(100,100,100,255)))
            self.sprite.owner = self
                   
      
    def update(self,dt):
        if self.task and self.task.task_ended(): self.task = None                
        self.powered = self.idle_draw > 0 and self.draw_power(self.idle_draw,dt) > 0
        

    def install(self,home,loc=None):
        if self.installed: return None # "Can't install the same thing twice!"
        self.installed=home
        if loc: home.equipment[loc][3] = self
        if home.station: self.logger = logging.getLogger(home.station.logger.name +'.' + home.short_id+ '.' + self.name)
        self.logger.info(''.join([self.name," installed in ", home.short_id,' at ',str(loc)]))
        return self    
        
    def get_name(self):
        if not self.installed: return None
        for e in self.installed.equipment.keys():
            if self.installed.equipment[e][3] == self:
                return e
        return None
        
    def refresh_station(self):
        if self.installed and self.installed.station:
            self.logger = logging.getLogger(self.installed.station.logger.name +'.' + self.installed.short_id+ '.' + self.name)             
        elif self.station:
            self.logger = logging.getLogger(self.station.logger.name +'.' + self.name)
        self.task = None #a new station means our tasks are no longer relevant

    def uninstall(self):
        if not self.installed: return None # "Can't install the same thing twice!"
        worked = self.installed.uninstall_equipment(self)
        self.installed=None
        self.refresh_image()
        return worked
        
    def draw_power(self,kilowattage,dt): #kilowatts
        if self.installed and (not hasattr(self,'broken') or not self.broken): #it's installed, not broken or can't break          
            #self.installed.station.resources.resources['Electricity'].available -= kilowattage*dt/3600            
            #TODO add equivalent heat into module
            return self.installed.station.resources.resources['Electricity'].draw(kilowattage*dt)
        return 0
        
    def task_finished(self,task):
        if task:
            if task.name == "Install" and not self.installed:
                home, loc = task.station.get_module_from_loc(task.location) , task.location.split('|')[1]
                if home.equipment[loc][3]: #this slot already has something installed!
                    task.drop()
                    return
                if task.assigned_to.held == self:
                    task.assigned_to.held = None
                else:
                    print "Object not held!"                
                self.install(home,loc)
                self.refresh_image()   
            elif task.name == "Uninstall" and self.installed:
                self.uninstall()
            elif task.name == 'Pick Up':                
                if self.installed: 
                    assert self.uninstall(), 'Unknown error after uninstallation'             
                module = task.station.get_module_from_loc(task.location)                
                if module.stowage.remove(self) is None:
                    self.logger.warning('This equipment not found in expected location.  Dropping pickup task.')
                    task.flag('CLOSED')
                    return
                task.assigned_to.held=self
                self.refresh_image()
            elif task.name == 'Put Down':                  
                module = task.station.get_module_from_loc(task.location)
                module.stowage.add(self)
                task.assigned_to.held=None
                self.refresh_image()

    def task_failed(self,task):
        pass     
        
    def task_dropped(self,task):
        if task.assigned_to.held == self:
            task.assigned_to.drop_held()
            

    def install_task(self,station):
        if self.installed or not station: return
        self.task = TaskSequence(name = ''.join(['Install Equipment']), severity = "LOW", logger=self.logger)
        self.task.station = station
        self.task.add_task(Task(name = ''.join(['Pick Up']), owner = self, timeout=86400, task_duration = 60, severity='LOW', fetch_location_method=Searcher(self,station,check_storage=True).search,station=station))
        self.task.add_task(Task(name = ''.join(['Install']), owner = self, timeout=86400, task_duration = 600, severity='LOW', fetch_location_method=Searcher(EquipmentFilter(target=self.type, subtype=self.name, comparison_type="Equipment Slot"),station).search,station=station))
        station.tasks.add_task(self.task)

    def uninstall_task(self):
        if not self.installed: return
        self.task = Task(name = ''.join(['Uninstall']), owner = self, timeout=None, task_duration = 300, severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)  
        self.installed.station.tasks.add_task(self.task)        
        
class Window(Equipment): #might even be too basic for equipment, but ah well.
    def __init__(self):
        super(Window, self).__init__()       
        self.name = "Window"
        self.in_vaccuum = True
        
    def refresh_image(self):     
        super(Window, self).refresh_image()
        if self.sprite is None: return
        self.sprite.add_layer('Window',util.load_image("images/window.png"))
        self.sprite.layer['Equipment'].visible=False
        
    def update(self,dt):
        super(Window, self).update(dt)        
        if self.installed and not self.task or self.task.task_ended():
            comms, d, d = self.installed.station.search( EquipmentFilter( target='Comms' ) )
            if comms:
                #stellar observations TODO vary the observables - military spying, geological data, etc
                self.task = TaskSequence(name = ''.join(['Conduct Stellar Observations']), severity = "IGNORABLE", logger=self.logger)            
                self.task.add_task(Task(''.join(['Collect Data']), owner = self, timeout=None, task_duration = 1800, severity='IGNORABLE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger))
                self.task.add_task(Task(''.join(['Report Star Data']), owner = comms, timeout=None, task_duration = 300, severity='IGNORABLE', fetch_location_method=Searcher(comms,self.installed.station).search,logger=self.logger))
                
                self.installed.station.tasks.add_task(self.task)  
                                   
        
class Machinery(Equipment): #ancestor class for things that need regular maintenance
    def __init__(self):
        self.active = False
        super(Machinery, self).__init__()              
        self.idle_draw = 0.001 #kW
        #self.maint_timer = random.randrange(util.seconds(6,'months'), util.seconds(2,'years') )
        self.maint_task = None
        self.operating_time_since_last_maintenance = 0
        self.maintenance_interval = util.seconds(7,'days')
        self.wear = 1.0
        self.broken = False
        self.recently_active=False
        self.type = 'MACHINERY'
            
    def refresh_image(self):     
        super(Machinery, self).refresh_image()
        if self.sprite is None: return
        import pyglet
        img1=pyglet.image.AnimationFrame(util.load_image("images/machinery_40x40.png"),0.5 if self.active else None)
        img2=pyglet.image.AnimationFrame(util.load_image("images/machinery_40x40_1.png"),0.5)
        
        animation = pyglet.image.Animation([img1,img2])
        
        self.sprite.add_layer('Machinery',animation)                                                 
        
    def set_active(self):
        #TODO figure out why the below line doesn't work
        self.sprite.layer['Machinery'].image.frames[0].duration=0.5 if self.recently_active else None        
                
    def update(self,dt):
        super(Machinery, self).update(dt)     
  
        if self.active: 
            if not self.recently_active:
                self.recently_active = True
                self.refresh_image()
                #self.set_active()
            
            self.operating_time_since_last_maintenance += dt
            if random.random() < (dt/util.seconds(1,'month'))*self.operating_time_since_last_maintenance/(100*self.wear*self.maintenance_interval):
                self.broken = True
        else:
            if self.recently_active:
                self.recently_active = False
                #self.set_active()
                self.refresh_image()
            
        if self.broken:
            if not self.maint_task or self.maint_task.name != ''.join(['Repair ',self.name]):
                self.maint_task = Task(''.join(['Repair ',self.name]), owner = self, timeout=None, task_duration = util.seconds(4,'hours'), severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
                self.installed.station.tasks.add_task(self.maint_task)  
                
        if self.operating_time_since_last_maintenance >= self.wear*self.maintenance_interval and ( not self.maint_task or self.maint_task.task_ended() ):
            self.maint_task = Task(''.join(['Maintain ',self.name]), owner = self, timeout=None, task_duration = util.seconds(1,'hours'), severity='LOW', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
            #print self.maint_task.timeout,self.maint_task.task_duration
            self.installed.station.tasks.add_task(self.maint_task)        
        
    def task_finished(self,task): #TODO add supply usage
        super(Machinery, self).task_finished(task) 
        if not task: return
        if task.name == ''.join(['Maintain ',self.name]) and task.target == self:
            self.maint_task = None
            self.wear -= self.operating_time_since_last_maintenance/(self.wear*self.maintenance_interval) - 1
            print self.operating_time_since_last_maintenance, self.wear, self.maintenance_interval
            self.wear = max(self.wear,0)
            self.operating_time_since_last_maintenance = 0
        elif task.name == ''.join(['Repair ',self.name]) and task.target == self:
            self.maint_task = None
            self.broken = False
            self.wear += (1 - self.wear) / 2        

        
class Comms(Equipment):
    def __init__(self):   
        super(Comms, self).__init__()
        self.type = 'Communication Equipment'
        self.idle_draw = 0.01 #kW
        self.name = 'Comms Equipment'
                
    def refresh_image(self):     
        super(Comms, self).refresh_image()
        if self.sprite is None: return
        #self.sprite.add_layer('Comms',util.load_image("images/smallcomms_40x40.png"))                 
        self.sprite.add_layer('Comms',util.load_image("images/mozilla-feed-icon-28x28.png"))
                
    def spawn_mc_task(self):
        if not self.task or self.task.task_ended():
            self.task = Task(''.join(['Contact Mission Control']), owner = self, timeout=None, task_duration = 300, severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)  
            self.installed.station.tasks.add_task(self.task)    
                    
    def task_finished(self,task):
        super(Comms, self).task_finished(task) 
        if task.name == "Contact Mission Control":
            util.contact_mission_control()  
        elif task.name == 'Report Star Data':
            util.universe.science.field['Astronomy'].add_progress(prog_amt = 5)              
        
#docking equipment        
class DockingRing(Equipment):
    def __init__(self):   
        if not hasattr(self,'imgfile'): self.imgfile = "images/closed_hatch.tif"
        self.open = False
        self.player_usable = True #toggle to allow player to "turn off" hatches
        super(DockingRing, self).__init__()     
        self.docked = None #a pointer to the module we've docked to        
        self.in_vaccuum = True
        self.partner = None #a pointer to the docking equipment partner
                
    def toggle_player_usable(self):
        self.player_usable = not self.player_usable            
        self.refresh_image()
        
    def refresh_image(self):     
        super(DockingRing, self).refresh_image()
        if self.sprite is None: return
        if self.open:
            self.sprite.add_layer('DockingRing',util.load_image("images/open_hatch.png"))
        else:
            self.sprite.add_layer('DockingRing',util.load_image("images/closed_hatch.png"))
        
        #import pyglet
        #img1=pyglet.image.AnimationFrame(util.load_image("images/blank_40x40.png"),0.5 if not self.player_usable else None)
        #img2=pyglet.image.AnimationFrame(util.load_image("images/half_red.png"),0.5)
        
        #animation = pyglet.image.Animation([img1,img2])
        
        if self.player_usable:
            self.sprite.add_layer('Forbidden',util.load_image("images/blank_40x40.png"))
        else:
            self.sprite.add_layer('Forbidden',util.load_image("images/half_red.png"))
        
        self.sprite.layer['Equipment'].visible=False    
        
    #these two need to generate tasks for unpowered rings
    def open_(self):
        if self.open: return
        if not self.docked: return False, "What are you, nuts?!"
        self.open = True
        self.refresh_image()
        if self.partner and not self.partner.open:
            self.installed.station.paths.add_edge(self.installed.get_node(self),self.docked.get_node(self.partner),weight=1)
            self.partner.installed.station.paths.add_edge(self.installed.get_node(self),self.docked.get_node(self.partner),weight=1)
        
    def close_(self):
        if not self.open: return
        self.open=False
        self.refresh_image()
        if self.partner and not self.partner.open:            
            self.installed.station.paths.remove_edge(self.installed.get_node(self),self.docked.get_node(self.partner))
            self.partner.installed.station.paths.remove_edge(self.installed.get_node(self),self.docked.get_node(self.partner))
        
    def dock(self, target, partner=None, instant = False):
        self.docked=target                
        self.in_vaccuum = False
        self.partner=partner
        if instant:             
            self.open_()
        else:
            if not self.installed.station: return
            self.task = Task(''.join(['Open Hatch']), owner = self, timeout=None, task_duration = 300, severity='MODERATE', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)            
            self.installed.station.tasks.add_task(self.task)            
                
    def undock(self, instant = False):
        if not self.open: 
            self.docked = None
            self.in_vaccuum = True
            self.partner = None
            return True
        if self.task and not self.task.task_ended():
            return False
        if instant:
            self.close_()                
        else:
            #TODO check and add a task for disconnecting the pipes
            self.task = Task(''.join(['Close Hatch']), owner = self, timeout=86400, task_duration = 300, severity='LOW', fetch_location_method=Searcher(self,self.installed.station).search,logger=self.logger)
            self.installed.station.tasks.add_task(self.task)
        return self.undock(instant)
            
        
    def task_finished(self,task):
        super(DockingRing, self).task_finished(task) 
        if task.name == 'Close Hatch': 
            #TODO check for someone in the other module
            if self.partner: self.partner.close_()
            if self.open: self.close_()
        elif task.name == 'Open Hatch':
            if not self.open: self.open_()
            if self.partner: self.partner.open_()
            #TODO add a task to connect pipes, open other side
            
    def task_work_report(self,task,dt):
        if task.name == 'Close Hatch' and not self.open: 
            self.task.flag('COMPLETED')
        elif task.name == 'Open Hatch' and self.open:    
            self.task.flag('COMPLETED')
            
            
class CBM(DockingRing):
    def __init__(self):   
        super(CBM, self).__init__()     
        self.active = False
        self.name = 'CBM'
     
#specialized, installed, single-purpose equipment
class SolarPanel(Equipment):
    def __init__(self):   
        super(SolarPanel, self).__init__()       
          
        self.extended = False
        self.in_vaccuum = True
        self.capacity= 5 #kW
        
        self.name='Solar Panel'
        
    def refresh_image(self):     
        super(SolarPanel, self).refresh_image()
        if self.sprite is None: return
        img = util.load_image("images/solarpanel_horiz.png")
        img.anchor_x, img.anchor_y = [2,15]
        self.sprite.add_layer('SolarPanel',img)
        self.sprite.layer['Equipment'].visible=False        
        
    def update(self,dt):
        super(SolarPanel, self).update(dt)    
        if self.installed and self.extended:
            #print dt, self.installed.station.resources.resources['Electricity'].available, self.capacity*dt/3600.0
            self.installed.station.resources.resources['Electricity'].available += self.capacity*dt

class Battery(Equipment):
    def __init__(self):   
        super(Battery, self).__init__()
        self.type = 'Li-ion'
        self.capacity = 100     #kilowatt-hours            
        self.charge = 0         #kilowatt-hours
        self.discharge_rate = 2 #kilowatts
        self.efficiency = 0.95
        self.type = 'ELECTRICAL'
        
        self.name = str(self.capacity)+"kWh Battery"
        self.avg_charge = 0.0
                
    def refresh_image(self):     
        super(Battery, self).refresh_image()
        if self.sprite is None: return
        self.sprite.add_layer('Battery',util.load_image("images/battery_40x40.png"))                 
                
    def update(self,dt): 
        #print self.charge
        super(Battery, self).update(dt)
        if self.installed:
            power_situation = self.installed.station.resources.resources['Electricity'].previously_available
            if power_situation > 0:
                _charge = min(power_situation*dt, dt * self.discharge_rate) if self.charge < self.capacity else 0
                self.charge += self.efficiency * _charge / 3600
            else:
                _charge = max(power_situation*dt, -dt * self.discharge_rate) if self.charge > 0 else 0
                self.charge += _charge / 3600
            time_slice = dt/300.0
            cps = _charge/dt
            self.avg_charge = time_slice*cps + (1-time_slice)*self.avg_charge
            self.installed.station.resources.resources['Electricity'].available -= _charge
        #print dt, self.installed.station.resources.resources['Electricity'].available, _charge, self.charge, self.capacity
     
     
#rack equipment            
class Rack(Equipment):
    def __init__(self):   
        super(Rack, self).__init__()                    
        self.mass = 104
        self.type = 'RACK'
       
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
        
#miscellaneous equipment
class Storage(Equipment):
    def __init__(self, **kwargs):
        super(Storage, self).__init__(**kwargs)         
        self.stowage = clutter.Stowage(1) #things floating around in the rack
        if not hasattr(self,'filter'): self.filter = ClutterFilter(['All']) 
        self.space_trigger = 0.1 #free volume
        self.type = 'STORAGE'
                    
    def refresh_image(self):     
        super(Storage, self).refresh_image()
        
    def dump_task(self):
        if self.task and self.task.active and self.task.name is "Dump Out": return
        self.task = Task(name = ''.join(['Dump Out']), owner = self, task_duration = 60, fetch_location_method=Searcher(self,self.installed.station).search,station=self.installed.station)
        self.installed.station.tasks.add_task(self.task)    
        
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
            self.task = TaskSequence(name = ''.join(['Store ',filter_str]), severity = "LOW",logger=self.logger)
            self.task.add_task(Task(name = ''.join(['Pick Up ',filter_str]), severity = "LOW", timeout = 86400, task_duration = 30, fetch_location_method=Searcher(self.filter,self.installed.station).search, owner=clutter.JanitorMon(self.filter.target),logger=self.logger))
            self.task.add_task(Task(name = ''.join(['Put Away ',filter_str]), severity = "LOW", timeout = 86400, task_duration = 30, fetch_location_method = Searcher( SearchFilter( self ), self.installed.station ).search, owner=self,logger=self.logger))
            self.installed.station.tasks.add_task(self.task)
        
    def get_available_space(self): return self.stowage.free_space       
    available_space = property(get_available_space, None, None, "Available storage space" )    
    
    def task_work_report(self,task,dt):
        
        if task.name.startswith('Put Away'):
            item = task.assigned_to.inventory.search(self.filter)
            if not item: return
            remove_amt = min(clutter.gather_rate*dt*item.density,self.available_space*item.density,item.mass)
            if remove_amt <= 0: return         
            obj = item.split(remove_amt)
            self.stowage.add(obj)                         
            
    def task_finished(self,task):
        super(Storage, self).task_finished(task)         
        if task.name.startswith('Dump Out'):
            for c in self.stowage.contents:
                  self.installed.stowage.add(c)
            self.stowage.contents=[]
        self.update(0)           
        
        

class WaterTank(Storage):
    def __init__(self):                   
        self.filter = ClutterFilter(['Potable Water'])
        super(WaterTank, self).__init__()         
        
        self.stowage.capacity = 0.75
        self.name = "Water tank, "+str(self.stowage.capacity)+"m^3"
        
    def refresh_image(self):     
        super(WaterTank, self).refresh_image()
        if self.sprite is None: return
        if 'Gray Water' in self.filter.target:
            self.sprite.add_layer('GrayDrop',util.load_image("images/graywdrop_40x40.png"))  
        else:
            self.sprite.add_layer('WaterDrop',util.load_image("images/waterdrop_40x40.png"))        

class FoodStorageRack(Storage,Rack):
    def __init__(self, **kwargs):   
        super(FoodStorageRack, self).__init__(**kwargs)         
        self.filter = ClutterFilter(['Nonperishable Food'])
        self.space_trigger = 0.5 #free volume, m^3   
        self.name = "Food storage, "+str(self.stowage.capacity)+"m^3"
    
    def refresh_image(self):     
        super(FoodStorageRack, self).refresh_image()
        if self.sprite is None: return
        self.sprite.add_layer('FoodSmall',util.load_image("images/glitch-assets/pi/pi__x1_rescaled_iconic_png_1354839579.png"))
        self.sprite.layer['FoodSmall'].scale=0.75
    

class GenericStorageRack(Storage,Rack):
    
    recipe = [ {'tech':{'Materials':1}, 'components':{'Basic Parts':1.0} } ]

    def __init__(self):   
        Storage.__init__(self)
        Rack.__init__(self)         
        self.filter = ClutterFilter(['Supplies'])
        self.space_trigger = 0.5 #free volume, m^3  
        self.name = "Generic storage, "+str(self.stowage.capacity)+"m^3"

    def refresh_image(self):     
        super(GenericStorageRack, self).refresh_image()
        if self.sprite is None: return
        self.sprite.add_layer('SuppSmall',util.load_image('images/glitch-assets/contraband/contraband__x1_1_png_1354836014.png'))
        self.sprite.layer['SuppSmall'].scale=0.75
    

class WaterStorageRack(WaterTank,Rack):
    def __init__(self):   
        super(WaterStorageRack, self).__init__()                 
        self.space_trigger = 0.5 #free volume, m^3                                          

                    
util.equipment_targets['Battery'] = Battery
util.equipment_targets['Storage'] = Storage
util.equipment_targets['Generic Storage Rack'] = GenericStorageRack
util.equipment_targets['Comms'] = Comms

