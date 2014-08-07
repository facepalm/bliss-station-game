from tasks import Task
import util
import logging

need_severity_profile = {'VARIABLE' : {0.2:'HIGH', 0.5:'MODERATE', 0.7:'LOW', 1.0:'IGNORABLE'}, 
                         'HUMAN_BIOLOGICAL': {0.1:'HIGH',0.2:'MODERATE',0.3:'LOW', 1.0:'IGNORABLE'} }



def need_from_task(taskname):
    if taskname.startswith('Satisfy '):
        return taskname.split('Satisfy ')[1]
    else:
        return None

class Need():
    def __init__(self,name,owner,max_amt,depletion_rate,replenish_rate,on_task,on_fail,severity='VARIABLE'):
        self.name = name
        self.owner = owner
        self.amt = max_amt
        self.max_amt = max_amt
        self.depletion_rate = depletion_rate
        self.replenish_rate = replenish_rate
        self.on_task = on_task
        self.on_task_name = on_task.__name__ if self.on_task else None
        self.on_fail = on_fail
        self.on_fail_name = on_fail.__name__ if self.on_fail else None
        self.severity = severity
        self.touched = 0
        self.logger = logging.getLogger(self.owner.logger.name + '.' + self.name)
        self.loggername = self.logger.name  
        
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['logger']       
        d.pop('on_task')
        d.pop('on_fail')
        return d    
        
    def __setstate__(self, d):
        self.__dict__.update(d)   
        self.logger = logging.getLogger(self.loggername) if self.loggername else util.generic_logger    
        self.on_task = getattr( self.owner, self.on_task_name) if self.on_task_name else None
        self.on_fail = getattr( self.owner, self.on_fail_name) if self.on_fail_name else None
        
    def update(self,dt):
        assert self.owner, "Need has no owner.  This should never happen."
        if self.touched > 0: self.touched -= dt
        if self.amt < 0 and self.on_fail and self.touched <= 0:
            self.on_fail()
            return
                                
        _need_severity = self.current_severity()
        
        _need_task = None
        _need_task = self.owner.my_tasks.find_task(''.join(['Satisfy ',self.name]))
        
        #print _need_task, _need_ratio
        if _need_task: 
            _need_task.severity = _need_severity        
            #if _need_ratio > 0.95 and self.owner.task == _need_task: _need_task.flag('IGNORED')
        elif self.on_task and _need_severity != 'IGNORABLE':
            t=self.on_task(self.amt/(self.depletion_rate+0.00001),_need_severity)
            t.flag('OPEN')
            self.owner.my_tasks.add_task(t)
            
        self.amt -= dt*self.depletion_rate

    def current_severity(self):        
        if self.severity in need_severity_profile.keys():
            _need_ratio = self.amt/self.max_amt
            profile = need_severity_profile[self.severity]            
            sev = 'IGNORABLE'
            for f in sorted(profile.keys(),reverse=True):
                if _need_ratio <= f:
                    sev = profile[f]
            return sev          
        else:
            return self.severity
            
    def supply(self, available_amt, dt):
        _amt = min( available_amt, dt*self.replenish_rate, self.max_amt - self.amt )
        self.amt += _amt            
        if self.amt >= 0.99*self.max_amt:
            _need_task = self.owner.my_tasks.find_task(''.join(['Satisfy ',self.name]))
            if _need_task: _need_task.flag('COMPLETED')
        return _amt    
        
    def set_amt_to_severity(self,severity='IGNORABLE'):
        if not self.severity in need_severity_profile.keys(): return #can't do much if we don't have a profile
        profile = need_severity_profile[self.severity]
        for k in profile.keys():
            if severity == profile[k]:
                self.amt = k*self.max_amt
        
    def status(self):
        return [self.amt/self.max_amt, self.severity]
                
