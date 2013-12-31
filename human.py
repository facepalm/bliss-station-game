from actor import Actor
from equipment import EquipmentSearch, Storage
from tasks import Task, TaskTracker
from needs import Need, need_from_task
import equipment
import clutter
import util

class Human(Actor):
    def __init__(self, name='Buzz Kerman'):
        super(Human, self).__init__(name)
        self.needs['Food']=Need('Food', self, 0.62, 0.62/86400.0, 0.62/1800.0, self.new_dinner_task, self.hunger_hit)
        self.needs['Water']=Need('Water', self, 3.52, 3.52/86400.0, 3.52/600.0, self.new_drink_task, self.dehydration_hit)
        self.needs['WasteCapacitySolid']=Need('WasteCapacitySolid', self, 0.22, 0.22/192800.0, 0.22/300.0, self.number_2_task, self.code_brown)
        self.needs['WasteCapacityLiquid']=Need('WasteCapacityLiquid', self, 3.87, 3.87/21600.0, 3.87/30.0, self.number_1_task, self.code_yellow)       
        
        self.nutrition = [1.0, 1.0, 1.0, 1.0, 1.0]
        self.health = 1.0
        self.hygiene = 1.0
        self.activity_state = 'IDLE'
        self.suffocation = 0.0
        
    def hunger_hit(self):
        self.health -= 0.02 #TODO model malnutrition better later
        self.needs['Food']=Need('Food', self, 0.1, 0.1/86400.0, 0.1/600.0, self.new_dinner_task, self.hunger_hit)
        self.needs['Food'].severity='HIGH'

    def dehydration_hit(self):
        self.health -= 0.2 #TODO model malnutrition better later
        self.needs['Water']=Need('Water', self, 0.1, 0.1/43200.0, 0.1/600.0, self.new_drink_task, self.dehydration_hit)
        self.needs['Water'].severity='CRITICAL'
        
    def new_drink_task(self,timeout,severity):
        t=Task(''.join(['Satisfy Water']), owner = self, timeout=timeout, task_duration = 30, severity=severity, fetch_location_method=EquipmentSearch(clutter.ClutterFilter('Potable Water'),self.station,check_storage=True).search)
        return t
        
    def new_dinner_task(self,timeout,severity):
        t=Task(''.join(['Satisfy Food']), owner = self, timeout=timeout, task_duration = util.seconds(30,'minutes'), severity=severity, fetch_location_method=EquipmentSearch(clutter.ClutterFilter('Edible Food'),self.station,check_storage=True).search)
        return t        
        
    def number_1_task(self,timeout,severity):
        return Task(''.join(['Satisfy WasteCapacityLiquid']), owner = self, timeout=timeout, task_duration = 30, severity=severity, fetch_location_method=EquipmentSearch('Toilet',self.station).search)

    def number_2_task(self,timeout,severity):
        return Task(''.join(['Satisfy WasteCapacitySolid']), owner = self, timeout=timeout, task_duration = 30, severity=severity, fetch_location_method=EquipmentSearch('Toilet',self.station).search)
 
    def code_brown(self):
        #you have shit your pants.  This might be too goddamn realistic even for me.
        pass
        
    def code_yellow(self):
        #you have pissed your pants.  And all the spaghetti fell out of your pocket
        pass        

    def update(self, dt):
        if self.health <= 0: 
            print self.name, "'s dead!-------------------"
            return
        
        Actor.update(self,dt)                        
        #breathe
        module = self.station.get_module_from_loc(self.location)       
        if not module or module.atmo.pressure < 15: #below 15 kPa, you really can't even breathe 
            self.suffocate(dt)
        else:
            O2_pp = module.atmo.partial_pressure('O2')
            CO2_pp = module.atmo.partial_pressure('CO2')
            breath = module.atmo.extract('volume',.0005/3*dt) #avg rate of human breath
            CO2_frac = breath['O2']*0.05
            breath['O2'] -= CO2_frac
            breath['CO2'] += CO2_frac
            module.atmo.inject(breath)
            if O2_pp < 7.5 or O2_pp > 300.0 or CO2_pp > 7.0: #Everest vs oxygen toxicity
                self.suffocate(dt) 
            else: 
                self.suffocation = 0
                                        
    def suffocate(self, dt):
        ''' Suffocation, this is suffocation!  
            Suffocation, an easy game to play '''
        self.suffocation += dt
        print self.name," is suffocationg!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        #test for suffocation
        if self.suffocation > 240: #u ded nao
            self.health -= 1  
                       
    def task_finished(self,task):
        if not task: return
        need = need_from_task(task.name)
        if need:             
            if need == 'Food' and self.needs['Food'].severity == 'HIGH':
                amt=self.needs[need].amt
                self.needs['Food']=Need('Food', self, 0.62, 0.62/86400.0, 0.62/1800.0, self.new_dinner_task, self.hunger_hit)
                self.needs[need].amt=amt
            elif need == 'Water' and self.needs['Water'].severity == 'CRITICAL':
                amt=self.needs[need].amt
                self.needs['Water']=Need('Water', self, 3.52, 3.52/86400.0, 3.52/60.0, self.new_drink_task, self.dehydration_hit)
                self.needs[need].amt=amt
            elif need == 'WasteCapacitySolid' and isinstance(task.target,equipment.UniversalToilet):
                task.target.solid_waste += self.needs[need].max_amt - self.needs[need].amt
                self.needs[need].set_to_severity('IGNORABLE')     
            if need in ['WasteCapacityLiquid', 'WasteCapacitySolid'] and isinstance(task.target,equipment.UniversalToilet):
                task.target.liquid_waste += self.needs['WasteCapacityLiquid'].max_amt - self.needs['WasteCapacityLiquid'].amt
                self.needs['WasteCapacityLiquid'].set_to_severity('IGNORABLE')  
                                        
    def task_work_report(self,task,dt):
        if not task: return
        need = need_from_task(task.name)
        need_pristines = {  'Food':'Edible Food', 
                            'Water':'Potable Water'}
        
        if need in need_pristines.keys():
            target=task.target
            if isinstance(task.target, Storage):
                target = task.target.stowage.find_resource(clutter.ClutterFilter(need_pristines[need]).compare)
            if not target: return                        
                
            #"eat" - TODO make a more detailed nutrition model for things like scurvy            
            eaten = self.needs[need].supply( target.mass , dt )
            if need == 'Food':
                self.nutrition = [util.quad_mean(self.nutrition[eu],target.quality['Nutrient'][eu],10,eaten) for eu,u in enumerate(self.nutrition)]
                #print 'New Nutrition!' ,self.nutrition, target.mass, eaten, self.needs['Food'].max_amt
            target.mass -= eaten
            
