
from equipment import Equipment, Machinery, EquipmentSearch
import clutter
import util
import atmospherics

     #TODO FINISH, half this crap is still toilet
class HydroponicTray(Equipment):
    def __init__(self):   
        super(HydroponicTray, self).__init__() 
        self.water_tank = clutter.Stowage(.25)
        self.nutrient_tank = clutter.Stowage(.05)
        
        self.tank.target_1 = clutter.ClutterFilter('Waste Water')
        self.processing_speed = 0.01

    def deposit(self, amt1=0, amt2=0):
        print amt1, amt2
        if amt1: self.tank.add( clutter.Clutter( "Waste Water", amt1 ) )
        if amt2: self.tank.add( clutter.Clutter( "Solid Waste", amt2, 714.0 ) )
        
    def update(self,dt):
        super(UniversalToilet, self).update(dt)   
        p = self.tank.find_resource( self.tank.target_1.compare )
        if self.installed and p and self.draw_power(0.03,dt):
            gray_dest, discard = EquipmentSearch( 'Storage', self.installed.station, resource_obj = self.installed.station.resources, storage_filter = 'Gray Water').search()
            #print 'gray dest', gray_dest
            if not gray_dest: return            
            proc_amt = max( 0, min( gray_dest.available_space, p.mass , self.processing_speed*dt ) )
            #print 'proc amt', proc_amt, p
            new_p = p.split(proc_amt)
            if not new_p: return
            new_p.quality['Contaminants'] = 0.09
            new_p.quality['Salt'] = 0.09
            gray_dest.stowage.add(new_p)
        

util.equipment_targets['Toilet'] = UniversalToilet
