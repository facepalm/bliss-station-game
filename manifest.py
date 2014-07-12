import util
import clutter
import filtering
import equipment
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
        elif itemtype == "Equipment":
            self.filter=filtering.EquipmentFilter(target="Misc",subtype=subtype)
            
    def check_satisfaction(self):
        if self.task and not self.task.task_ended(): return False
        station = self.owner.module.station
        if self.itemtype == 'Actors':
            if self.tasktype == 'Unload':
                loc = lambda: lambda: station.random_location(modules_to_exclude=[self.owner.module])  
            else: 
                loc = lambda: lambda: [None, self.owner.module.filterNode( self.owner.module.node('Inside') ), None]
            for a in station.actors.values():
                if self.subtype=='All' or a.name == self.subtype:
                    self.task = Task(name = 'Move', severity = "HIGH", task_duration = 3600, fetch_location_method = loc(), owner=a)
                    a.my_tasks.add_task(self.task)
        elif self.tasktype == 'Unload':
            found_any = self.owner.module.stowage.search(self.filter)
            if found_any: 
                if self.itemtype=="Clutter":
                    filter_str = self.filter.target_string()
                    self.task = TaskSequence(name = ''.join(['Move ',filter_str]), severity = "MODERATE")
                    self.task.add_task(Task(name = ''.join(['Pick Up ',filter_str]), severity = "MODERATE", timeout = None, task_duration = 30, fetch_location_method=filtering.Searcher(self.filter,self.owner.module).search, owner=clutter.JanitorMon(self.filter.target)))
                    self.task.add_task(Task(name = ''.join(['Put Away ',filter_str]), severity = "MODERATE", timeout = None, task_duration = 30, fetch_location_method = lambda: station.random_location(modules_to_exclude=[self.owner.module]), owner=self))
                    station.tasks.add_task(self.task)
                    return False
                elif self.itemtype == "Equipment":
                    eq = found_any
                    self.task = TaskSequence(name = ''.join(['Move Equipment']), severity = "MODERATE")
                    self.task.station = self.owner.module.station
                    self.task.add_task(Task(name = ''.join(['Pick Up']), owner = eq, timeout=None, task_duration = 60, severity='MODERATE', fetch_location_method=filtering.Searcher(eq,station,check_storage=True).search,station=station))
                    self.task.add_task(Task(name = ''.join(['Put Down']), owner = eq, timeout=None, task_duration = 60, severity='MODERATE', fetch_location_method=lambda: station.random_location(modules_to_exclude=[self.owner.module]),station=station))
                    station.tasks.add_task(self.task)
                    return False
        elif self.tasktype == 'Load':
            found_any = self.owner.module.stowage.search(self.filter)
            if not found_any or (found_any.volume < self.taskamt and self.owner.module.stowage.free_space > 0.25):
                found_any = self.owner.module.station.search(self.filter,modules_to_exclude=[self.owner.module])   
                if found_any[0]:
                    if self.itemtype == "Clutter":
                        filter_str = self.filter.target_string()
                        self.task = TaskSequence(name = ''.join(['Move ',filter_str]), severity = "MODERATE")
                        self.task.add_task(Task(name = ''.join(['Pick Up ',filter_str]), severity = "MODERATE", timeout = None, task_duration = 30, fetch_location_method=filtering.Searcher(self.filter,station,exclude=[self.owner.module]).search, owner=clutter.JanitorMon(self.filter.target)))
                        self.task.add_task(Task(name = ''.join(['Put Away ',filter_str]), severity = "MODERATE", timeout = None, task_duration = 30, fetch_location_method = lambda: [None, self.owner.module.filterNode( self.owner.module.node('Inside') ), None], owner=self))
                        station.tasks.add_task(self.task)
                        return False   
                    elif self.itemtype == "Equipment":
                        eq = found_any[0]
                        self.task = TaskSequence(name = ''.join(['Move Equipment']), severity = "MODERATE")
                        self.task.station = self.owner.module.station
                        self.task.add_task(Task(name = ''.join(['Pick Up']), owner = eq, timeout=None, task_duration = 60, severity='MODERATE', fetch_location_method=filtering.Searcher(eq,station,exclude=[self.owner.module]).search,station=station))
                        self.task.add_task(Task(name = ''.join(['Put Down']), owner = eq, timeout=None, task_duration = 60, severity='MODERATE', fetch_location_method=lambda: [None, self.owner.module.filterNode( self.owner.module.node('Inside') ), None],station=station))
                        station.tasks.add_task(self.task)
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
            
    def conflicts(self,other): #currently unused
        '''given another manifest item, returns true if the two requirements conflict'''
        if not isinstance(other,ManifestItem): raise TypeError("ManifestItems must only conflict with other ManifestItems")
        if (self.tasktype == 'Unload' and other.tasktype == "Load") or (other.tasktype == 'Unload' and self.tasktype == "Load"):
            if self.itemtype == other.itemtype:
                if self.subtype == other.subtype or self.subtype == "Any" or other.subtype == "Any":
                    return True
        return False 
        
    def cancel(self): #when removed, manifest tasks should be dropped
        if self.task and not self.task.task_ended():
            self.task.drop()
        if self.itemtype == 'Actors':            
            for a in self.owner.module.station.actors.values():
                if self.subtype=='All' or a.name == self.subtype:
                    #task = Task(name = 'Move', severity = "HIGH", task_duration = 3600, fetch_location_method = loc(), owner=a)
                    #a.my_tasks.add_task(task)    
                    a.my_tasks.cancel_task('Move')
            

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
                    entry = ManifestItem(self, tasktype=tasktype, taskamt=taskamt, itemtype=itemtype, subtype=e.name)
                    entry.filter.target='By Name'
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

    def append_item(self,entry): #currently unused
        for i in self.item:            
            if i.conflicts(entry):
                entry = i.merge(entry)
            if not entry: return
        self.item.append(entry)    

    def refresh_station(self, station=None):
        for i in self.item: #New station!  New station! Dump tasks!
            i.task=None
            
        
