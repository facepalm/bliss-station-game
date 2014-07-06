import random
import util, logging

TASK_STATUS = {'NEW':0, 'Open':1, 'Assigned':2, 'COMPLETED':3, 'Closed':4 }
TASK_SEVERITY_VALUE = { 'CRITICAL'  :   10,
                        'HIGH'      :   8,
                        'MODERATE'  :   5,
                        'LOW'       :   3,
                        'IGNORABLE' :   1,
                        'DISREGARD' :   0}

#Evolution of a task:
    #object breaks, activates or otherwise triggers
    #object creates new task, status NEW
    #station actor (human, computer, etc) notices task and flags "OPEN" with severity
    #human actor or robot, querying for tasks to do, picks up task, flags to 'ASSIGNED'
    #actor moves to task location, completes task, flags 'COMPLETED'
    #station actor notes completed task, flags 'CLOSED', removes it
    #       -or-
    #'NEW' or 'OPEN' task is never finished, or flagged 'IGNORED', times out
    # tasks fail and close themselves
class Task(object):
    def __init__(self, name = 'GENERIC TASK', owner = None, assigned_to = None, severity = "LOW", timeout = 86400, task_duration = 1800, fetch_location_method=None, station=None, logger=None):
        self.owner = owner
        self.assigned_to = assigned_to
        self.target = None
        self.location = None
        if fetch_location_method: 
            self.fetch_location = fetch_location_method             
        self.severity = severity
        self.timeout = timeout #Setting timeout to None will result in a task that never ends
        self.task_duration = task_duration #30 minutes
        self.task_duration_remaining = task_duration        
        self.task_reset = False #False: task work is not lost if abandoned. True: task resets if dropped
        self.name = name
        self.touched = 0
        self.description = 'NONE'
        self.status = 'NEW'
        self.station = station
        self.logger = logging.getLogger(logger.name + '.' + self.name) if logger else logging.getLogger(self.owner.logger.name + '.' + self.name) if (self.owner and hasattr(self.owner,'logger')) else util.generic_logger
        self.loggername = self.logger.name
        
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']
        if 'fetch_location' in d: 
            d['fetch_location_name'] = d['fetch_location'].__name__
            d['fetch_location_instance'] = d['fetch_location'].__self__
            d.pop('fetch_location')
        return d    
        
    def __setstate__(self, d):
        self.__dict__.update(d)   
        self.logger = logging.getLogger(self.loggername) if self.loggername else util.generic_logger     
        if 'fetch_location_instance' in d:
            self.fetch_location = getattr(d['fetch_location_instance'],d['fetch_location_name'])       
        
    def update(self,dt):
        if self.timeout: self.timeout -= dt        
        if self.touched > 0: 
            self.touched -= dt
            self.logger.debug(''.join(["Current delay:",str(self.touched)]))
        if self.timeout and self.timeout < 0 and not (self.status == 'COMPLETED' or self.status == 'CLOSED'): 
            self.flag('CLOSED')

    def chosen_location(self, loc):
        self.location = loc

    def do_work(self,dt):
        if self.task_ended(): return False
        self.task_duration_remaining -= dt
        if hasattr(self.owner, 'task_work_report'): self.owner.task_work_report(self,dt)
        #print self.name, self.task_duration_remaining
        if self.task_duration_remaining <=0: 
            self.flag('COMPLETED') 
            
    def drop(self):
        self.logger.info(''.join(["Task '",self.name,"' dropped!"]))
        if hasattr(self.owner, 'task_dropped'): self.owner.task_dropped(self)
        self.flag('OPEN')                          
        self.assigned_to = None   
        self.location = None
        self.touched = 300
        if self.task_reset: self.task_duration_remaining = self.task_duration   

    def assign(self, ass): #tee hee, I said "ass"
        self.flag('ASSIGNED')                          
        self.assigned_to = ass 
            
    def flag(self, new_flag):
        if new_flag == self.status: return True
        if new_flag == 'IGNORED': 
            self.touched = 60
            return self.flag('CLOSED')
        if new_flag == 'CLOSED' and not self.status == 'COMPLETED':
            self.logger.info(''.join(["Task failed!"]))
            self.status = new_flag
            if hasattr(self.owner, 'task_failed'): self.owner.task_failed(self)            
        if new_flag == 'COMPLETED' and not self.status == 'CLOSED':
            self.logger.info(''.join(["Task '",self.name,"' finished!"]))
            self.status = new_flag
            if hasattr(self.owner, 'task_finished'): self.owner.task_finished(self) 
        self.status = new_flag
        return True                
        
    def task_ended(self):
        return self.status == 'COMPLETED' or self.status == 'CLOSED'    
        
    def task_value(self):
        if self.task_ended(): return 0 
        #print self.name, self.severity
        return TASK_SEVERITY_VALUE[self.severity]#/self.timeout#(self.task_duration_remaining/self.task_duration)
        
    def __cmp__(self, other):
        if not other: return 1
        assert isinstance(other, Task)
        if cmp(self.task_value(),other.task_value()) == 0: return random.choice([-1,1])         
        return cmp(self.task_value(),other.task_value())        
      
        
class TaskSequence(Task):        
    '''A sequence of tasks, all of which need to be completed in consecutive order.
    Example: Eat Dinner
        Locate, move to, pick up food
        (optional) locate, move to eating location
        Eat
        (optional) locate, move to trash can, dispose of trash'''
    def __init__(self, **kwargs):
        Task.__init__(self, **kwargs)
        self.current_task = None
        self.current_task_required = True
        self.task_list = None
        self.real_name=self.name
        
    def get_duration_remaining(self): return sum([f.task_duration_remaining for f in self.task_list.keys()])  
    def set_duration_remaining(self, amt): pass      
    task_duration_remaining = property(get_duration_remaining, set_duration_remaining, None, "Total task duration" )                  
    
    def get_location_method(self): 
        self.update(0) 
        return self.current_task.fetch_location if self.current_task else None
    fetch_location = property(get_location_method, None, None, "Fetch location method" )      
        
    def update(self,dt):
        if self.touched > 0: 
            self.touched -= dt
        if not self.task_list and (not self.current_task or self.current_task.status == 'COMPLETED'): 
            self.flag('COMPLETED')            
            return
        if not self.current_task or self.current_task.status == 'COMPLETED': 
            [ self.current_task, self.current_task_required ] = self.task_list.pop(0) 
            [self.target, self.location, d] = self.current_task.fetch_location()
            #print "SEARCHED", self.target, self.location, self.current_task.name
            self.name = ''.join( [ self.real_name, ': ', self.current_task.name ] )
        if self.current_task_required and self.current_task.status == 'CLOSED':
            self.flag('CLOSED')
            return
        self.current_task.assigned_to = self.assigned_to
        self.current_task.target=self.target
        self.current_task.location=self.location
        self.current_task.update(dt)
        
    def do_work(self,dt): 
        loc=self.location
        self.update(0)   
        if self.location != loc: return     
        if dt <= 0: return                  
        if self.task_ended(): return    
        
        time_slice = min(dt, self.current_task.task_duration_remaining)
        self.current_task.do_work(time_slice)        
      
        #What's this?  Recursion?  Yer goddamned right it is, son.  We COMPSCI 201 all up in this bitch.
        return self.do_work(dt-time_slice) 
        
    def drop(self):
        self.current_task.drop()
        self.touched = 300        
        
    def add_task(self,task,required=False):  
        if self.task_list:      
            self.task_list.append([task, required])
        else:
            self.task_list = [[task, required]]
        
class TaskTracker():
    def __init__(self):
        self.tasks=[]
                        
        
    def update(self,dt):
        for f in self.tasks:
            f.update(dt)
        for f in self.tasks:    
            if f.task_ended(): self.tasks.remove(f)
            if f.status == 'NEW': f.flag('OPEN')
            
    def add_task(self,task):
        self.tasks.append(task)           
        
    def find_task(self,name):
        for f in self.tasks:
            if f.name == name:
                return f
        return None   
              
         
    def fetch_open_task(self):
        self.update(0)
        open_tasks = sorted([t for t in self.tasks if t.status == 'OPEN' and t.touched <= 0])
        if open_tasks: return open_tasks[-1]        
            
if __name__ == "__main__":
    from time import sleep    
    t1 = Task('Pass Task', timeout=10, task_duration = 5)
    t2 = Task('Fail Task', timeout=10, task_duration = 15, severity='MODERATE')

    taskmon = TaskTracker()
    taskmon.add_task(t1)
    taskmon.add_task(t2)   
    
    print max(t1,t2).name     

    for i in range(1,30):
        taskmon.update(0.5)
        t1.do_work(0.5)
        t2.do_work(0.5)
        print t2 >= t1, taskmon.fetch_open_task().name
        sleep(0.5)
        
