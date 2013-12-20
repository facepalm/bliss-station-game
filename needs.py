from tasks import Task

def need_from_task(taskname):
    if taskname.startswith('Satisfy '):
        return taskname.split('Satisfy ')[1]
    else:
        return None

class Need():
    def __init__(self,name,owner,max_amt,depletion_rate,replenish_rate,on_task,on_fail):
        self.name = name
        self.owner = owner
        self.amt = max_amt
        self.max_amt = max_amt
        self.depletion_rate = depletion_rate
        self.replenish_rate = replenish_rate
        self.on_task = on_task
        self.on_fail = on_fail
        self.severity = 'VARIABLE'
        self.touched = 0
        
    def update(self,dt):
        assert(self.owner, "Need has no owner.  This should never happen.")
        if self.touched > 0: self.touched -= dt
        if self.amt < 0 and self.on_fail and self.touched <= 0:
            self.on_fail()
            return
                                
        _need_ratio = self.amt/self.max_amt
        if self.severity == 'VARIABLE':
            _need_severity = 'HIGH' if _need_ratio < 0.2 else 'MODERATE' if _need_ratio < 0.5 else 'LOW' if _need_ratio < 0.7 else 'IGNORABLE'
        else:
            _need_severity = self.severity
        
        _need_task = None
        _need_task = self.owner.my_tasks.find_task(''.join(['Satisfy ',self.name]))
        
        #print _need_task, _need_ratio
        if _need_task: 
            _need_task.severity = _need_severity        
            #if _need_ratio > 0.95 and self.owner.task == _need_task: _need_task.flag('IGNORED')
        elif self.on_task:
            t=self.on_task(self.amt/(self.depletion_rate+0.00001),_need_severity)
            t.flag('OPEN')
            self.owner.my_tasks.add_task(t)
            
        self.amt -= dt*self.depletion_rate

            
    def supply(self, available_amt, dt):
        _amt = min( available_amt, dt*self.replenish_rate, self.max_amt - self.amt )
        self.amt += _amt            
        return _amt
        
    def status(self):
        return [self.amt/self.max_amt, self.severity]
