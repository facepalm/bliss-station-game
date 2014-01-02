
from equipment import Machinery, EquipmentSearch
import clutter
import util

#delicate equipment        
class UniversalToilet(Machinery):
    def __init__(self):   
        super(UniversalToilet, self).__init__() 
        self.solid_waste = 0
        self.liquid_waste = 0 
        self.gray_water = 0
        self.capacity = 1 # m^3, shared between both
        self.gray_water_capacity = 0.25 #m^3
        self.processing_speed = 0.01

    def deposit(self,amt1,amt2):
        self.solid_waste += amt2
        self.liquid_waste += amt1
        if self.solid_waste/714.33 + self.liquid_waste/1000 > self.capacity: #ohhhh shiiiiii
            pass #TODO replace with bad things happening
        
    def update(self,dt):
        super(UniversalToilet, self).update(dt)    
        if self.installed and self.liquid_waste > 0:
            if not self.draw_power(0.03,dt): return
            proc_amt = max( 0, min( self.liquid_waste, self.processing_speed*dt ) )
            if self.gray_water_capacity - self.gray_water < proc_amt: return # water tank is full
            self.liquid_waste -= proc_amt
            self.gray_water += proc_amt
        
class WaterPurifier(Machinery):
    '''Converts gray water into potable water.  Basically an abstracted still'''
    def __init__(self):   
        super(WaterPurifier, self).__init__()          
        self.processing_speed = 0.001
        
    def update(self,dt):
        super(WaterPurifier, self).update(dt)              
        if self.installed and self.draw_power(0.03,dt): #TODO replace with actual distillation power use
            gray_source, discard = EquipmentSearch('Toilet',self.installed.station,resource_obj=self.installed.station.resources).search()
            pure_dest, discard = EquipmentSearch( 'Storage', self.installed.station, resource_obj = self.installed.station.resources, storage_filter = 'Potable Water').search()
            proc_amt = max( 0, min( gray_source.gray_water, self.processing_speed*dt ) )
            if pure_dest.available_space > proc_amt:
                gray_source.gray_water -= proc_amt
                pure_dest.stowage.add( clutter.Clutter( 'Water', proc_amt ) )

util.equipment_targets['Toilet'] = UniversalToilet
