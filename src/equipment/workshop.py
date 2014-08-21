
from general import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from filtering import Searcher, ClutterFilter, SearchFilter
import random
from tasks import Task, TaskSequence
            
class Workshop(Equipment):
    '''Progenitor class for machine shop bits'''
    
    configuration = 'Workbench' #space suitable for building small equipment from parts
    
    def __init__(self):
        self.img="images/glitch-assets/tinkertool/tinkertool__x1_iconic_png_1354832369.png"
    
        super(Workshop, self).__init__()              
        self.idle_draw = 0.200 #kW                
        self.name = "Workshop"        
        self.status = 'idle'

    def update(self,dt):            
        super(Workshop, self).update(dt)
                               
    def refresh_image(self):     
        super(Workshop, self).refresh_image() 
        if self.sprite is None: return        
        self.sprite.add_layer('Workshop',util.load_image(self.img))
        self.sprite.layer['Workshop'].scale = 0.8          
        
    def append_fetch_task(self,item):
        filt = ClutterFilter([item],check_storage=True)
        self.task.prepend_task(Task(name = ''.join(['Prep ',item]), severity = "MODERATE", task_duration = 120, fetch_location_method = Searcher( SearchFilter( self ), self.installed.station ).search, owner=self,logger=self.logger))
        self.task.prepend_task(Task(name = ''.join(['Pick Up ',item]), severity = "MODERATE", task_duration = 120, fetch_location_method=Searcher(filt,self.installed.station).search, owner=clutter.JanitorMon(filt.target),logger=self.logger))                  
    

class WorkbenchRack(Rack, Workshop):
    configuration = 'Workbench' #space suitable for building small equipment from parts

    def __init__(self):
        
        Workshop.__init__(self) 
        Rack.__init__(self)                    
        
        self.name = "Workbench InnaBox"
        self.local_parts = clutter.Stowage(3)
        self.equip_goal = None
        self.recipe_goal = None
        self.ready_goal = False
        
    def update(self,dt):            
        Workshop.update(self,dt)
        Rack.update(self,dt)              
                            
    def build_equipment_task(self, equip, recipe_num = 0):
        if not equip or not hasattr(equip,'recipe') or not equip.recipe: return False
        if self.status != 'idle': return False
        
        self.status = 'Constructing: '+ str(equip).rsplit('.')[-1]
        
        self.equip_goal = equip        
        self.recipe_goal = equip.recipe[recipe_num]
        self.ready_goal = False
        #TODO check tech levels
        
        self.task = TaskSequence(name = ''.join(['Build ',str(equip).rsplit('.')[-1]]), severity = "MODERATE",logger=self.logger)
        for r in self.recipe_goal['components'].keys():
            self.append_fetch_task(r)
        
        self.task.add_task(Task(name = ''.join(['Assemble item']), severity = "MODERATE", task_duration = 3600, fetch_location_method = Searcher( SearchFilter( self ), self.installed.station ).search, owner=self,logger=self.logger))
        
        self.installed.station.tasks.add_task(self.task)

    def task_work_report(self,task,dt):
        #Workshop.task_work_report(self,task,dt)         
        #Rack.task_work_report(self,task,dt)
        if task.name.startswith('Prep '):
            filt = ClutterFilter([task.name.rsplit('Prep ')[-1]])
            item = task.assigned_to.inventory.search(filt)
            if not item: return
            remove_amt = min(clutter.gather_rate*dt*item.density,self.local_parts.free_space*item.density,item.mass)
            #print remove_amt
            if remove_amt <= 0: return         
            obj = item.split(remove_amt)
            self.local_parts.add(obj)
        if task.name.startswith('Assemble item') and not self.ready_goal:
            for r in self.recipe_goal['components'].keys():
                filt = ClutterFilter([r])
                vol = self.local_parts.search_info(filt)[1]
                if vol < self.recipe_goal['components'][r]:
                    self.logger.info("Delaying assembly!  Reason: "+r)
                    task.drop()
                    return
            self.ready_goal = True
        

    def task_finished(self,task):
        #Workshop.task_finished(self,task)         
        #Rack.task_finished(self,task)
        if task.name.startswith('Prep '):
            #find local volume of item, reopen task if need be.
            item_name = task.name.rsplit('Prep ')[-1]
            filt = ClutterFilter([item_name])
            vol = self.local_parts.search_info(filt)[1]
            if vol < self.recipe_goal['components'][item_name]: 
                self.logger.info('Ingredient volume too low, reopening: '+item_name+ str(vol))
                self.append_fetch_task(item_name)
        if task.name.startswith('Assemble item') and self.ready_goal:
            new_equip = self.equip_goal()
            for r in self.recipe_goal['components'].keys():
                filt = ClutterFilter([r])
                item = self.local_parts.search(filt)
                new_item = item.split(self.recipe_goal['components'][r] * item.density)
                new_equip.components.append(new_item)
            self.installed.stowage.add(new_equip)
            self.local_parts.dump_into(self.installed.stowage)
            self.status = 'idle'
            #self.task = None
                
        self.update(0)

