import util
import clutter
import filtering
from tasks import TaskSequence, Task

class ManifestItem(object):
    def __init__(self, owner, itemtype = 'Clutter', subtype = 'Any', tasktype='Unload', taskamt = 'All' ):
        self.task = None
        self.satisfied = False
        self.owner = owner
        self.tasktype=tasktype
        self.taskamt=taskamt
        self.itemtype=itemtype
        self.subtype=subtype
        self.filter = None
        if itemtype=="Clutter":
            self.filter=filtering.ClutterFilter([subtype],check_storage=True)
            
    def check_satisfaction(self):
        if self.task and not self.task.task_ended(): return False
        if self.tasktype == 'Unload':
            found_any = self.owner.module.stowage.search(self.filter)
            if found_any: 
                filter_str = self.filter.target_string()
                self.task = TaskSequence(name = ''.join(['Move ',filter_str]), severity = "MODERATE")
                self.task.add_task(Task(name = ''.join(['Pick Up ',filter_str]), severity = "MODERATE", timeout = None, task_duration = 30, fetch_location_method=filtering.Searcher(self.filter,self.owner.module).search, owner=clutter.JanitorMon(self.filter.target)))
                self.task.add_task(Task(name = ''.join(['Put Away ',filter_str]), severity = "MODERATE", timeout = None, task_duration = 30, fetch_location_method = lambda: self.owner.module.station.random_location(modules_to_exclude=[self.owner.module]), owner=self))
                self.owner.module.station.tasks.add_task(self.task)
                return False
        elif self.tasktype == 'Load':
            found_any = self.owner.module.stowage.search(self.filter)
            if not found_any or (found_any.volume < self.taskamt and self.owner.module.stowage.free_space > 0.25):
                found_any = self.owner.module.station.search(self.filter,modules_to_exclude=[self.owner.module])   
                if found_any[0]:
                    filter_str = self.filter.target_string()
                    self.task = TaskSequence(name = ''.join(['Move ',filter_str]), severity = "HIGH")
                    self.task.add_task(Task(name = ''.join(['Pick Up ',filter_str]), severity = "HIGH", timeout = None, task_duration = 30, fetch_location_method=filtering.Searcher(self.filter,self.owner.module.station,exclude=[self.owner.module]).search, owner=clutter.JanitorMon(self.filter.target)))
                    self.task.add_task(Task(name = ''.join(['Put Away ',filter_str]), severity = "MODERATE", timeout = None, task_duration = 30, fetch_location_method = lambda: [None, self.owner.module.filterNode( self.owner.module.node('Inside') ), None], owner=self))
                    self.owner.module.station.tasks.add_task(self.task)
                    return False     
        return True
                      
    
    def get_some_satisfaction(self):
        self.satisfied = self.check_satisfaction()
        if self.satisfied: return True
        
    def task_work_report(self,task,dt):
        if task.name.startswith('Put Away'):
            item = task.assigned_to.inventory.search(self.filter)
            if not item: return
            remove_amt = min(clutter.gather_rate*dt*item.density,item.mass)
            if remove_amt <= 0: return         
            obj = item.split(remove_amt)
            self.owner.module.station.get_module_from_loc(task.location).stowage.add(obj) 
            
    def task_dropped(self,task):
        if task.name.startswith('Put Away'): #Drop your crap wherever you are
            item = task.assigned_to.inventory.search(self.filter)
            if not item: return
            remove_amt = item.mass
            if remove_amt <= 0: return         
            obj = item.split(remove_amt)
            self.owner.module.station.get_module_from_loc(task.assigned_to.location).stowage.add(obj)                              
            

class Manifest(object):
    '''Manifests are, essentially, list managers'''
    def __init__(self,module=None):
        self.module = module
        self.item = []
        
    def new_item(self, tasktype='Unload', taskamt = None, itemtype = 'Clutter', subtype = 'Any'):  
        if subtype == 'Any':
            if itemtype == 'Clutter':
                for c in [m for m in self.module.stowage.contents if isinstance(m,clutter.Clutter)]:
                    entry = ManifestItem(self, tasktype=tasktype, taskamt=taskamt, itemtype=itemtype, subtype=c.name)
                    self.item.append(entry)
            if itemtype == 'Equipment': 
                for e in [m for m in self.module.stowage.contents if isinstance(m,equipment.Equipment)]:
                    entry = ManifestItem(self, tasktype=tasktype, taskamt=taskamt, itemtype=itemtype, subtype=c.name)
                    self.item.append(entry)      
        else:
            entry = ManifestItem(self, tasktype=tasktype, taskamt=taskamt, itemtype=itemtype, subtype=subtype)
            self.item.append(entry)
        
    def check_satisfied(self):
        fail = False
        for i in self.item:
            i.get_some_satisfaction()
            if not i.satisfied: fail = True
        if fail: return False
        return True   
    satisfied = property(check_satisfied, None, None, "Check manifest satisfaction" )          

    def refresh_station(self, station=None):
        for i in self.item: #New station!  New station! Dump tasks!
            i.task=None
            
        
