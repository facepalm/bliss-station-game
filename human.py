from actor import Actor


class Human(Actor):
    def __init__(self, name='Buzz Kerman'):
        super(Human, self).__init__(name)
        self.needs['Food']=Need('Food', self, 0.62, 0.62/86400.0, 0.62/600.0, self.new_dinner_task, self.hunger_hit)
        self.needs['Water']=Need('Water', self, 3.52, 3.52/86400.0, 3.52/600.0, self.new_drink_task, self.dehydration_hit)
        self.needs['WasteCapacitySolid']=Need('WasteCapacitySolid', self, 0.22, 0.22/192800.0, 0.22/300.0, self.number_2_task, self.code_brown)
        self.needs['WasteCapacityLiquid']=Need('WasteCapacityLiquid', self, 3.87, 3.87/21600.0, 3.87/30.0, self.number_1_task, self.code_yellow)        
        self.health = 1.0
        self.hygiene = 1.0
        self.activity_state = 'IDLE'
        
    def hunger_hit(self):
        self.health -= 0.02 #TODO model malnutrition better later
        self.needs['Food']=Need('Food', self, 0.1, 0.1/86400.0, 0.1/600.0, self.new_dinner_task, self.hunger_hit)
        self.needs['Food'].severity='HIGH'

    def dehydration_hit(self):
        self.health -= 0.05 #TODO model malnutrition better later
        self.needs['Water']=Need('Water', self, 0.1, 0.1/86400.0, 0.1/600.0, self.new_drink_task, self.dehydration_hit)
        self.needs['Water'].severity='CRITICAL'
        
    def new_drink_task(self,timeout,severity):
        t=Task(''.join(['Satisfy Water']), owner = self, timeout=timeout, task_duration = 30, severity=severity, fetch_location_method=EquipmentSearch('Storage',self.station,'Potable Water').search)
        return t
        
    def new_dinner_task(self,timeout,severity):
        t=Task(''.join(['Satisfy Food']), owner = self, timeout=timeout, task_duration = 1800, severity=severity, fetch_location_method=EquipmentSearch('Storage',self.station,'Food').search)
        return t         

    def update(self, dt):
        Actor.update(self,dt)               
                                        
    def task_work_report(self,task,dt):
        if not task: return
        need = need_from_task(task.name)
        
        if need == 'Food':
            pass
            #TODO take from food locker
            #available = 0 if not hasattr(task.target, 'charge') else max(task.target.charge,0)
            #used=self.needs['Charge'].supply( available, dt )
            #task.target.charge -= used
            
