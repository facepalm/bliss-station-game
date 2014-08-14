
from equipment.general import Machinery
import clutter
from filtering import ClutterFilter, EquipmentFilter
import util
import atmospherics

#delicate equipment        
class UniversalToilet(Machinery):
    def __init__(self):   
        super(UniversalToilet, self).__init__() 
        self.tank = clutter.Stowage(1)
        self.tank.target_1 = ClutterFilter(['Waste Water'])
        self.processing_speed = 0.001
        self.satisfies['WasteCapacityLiquid'] = 0.5
        self.satisfies['WasteCapacitySolid'] = 0.5
        self.name = "Toilet"

    def refresh_image(self):     
        super(UniversalToilet, self).refresh_image()
        if self.sprite is None: return
        self.sprite.add_layer('Toilet',util.load_image("images/14_toilets_40x40.png"))

    def deposit(self, amt1=0, amt2=0):
        if amt1: self.tank.add( clutter.spawn_clutter( "Waste Water", amt1 ) )
        if amt2: self.tank.add( clutter.spawn_clutter( "Solid Waste", amt2, 714.0 ) )
        
    def update(self,dt):
        super(UniversalToilet, self).update(dt)   
        p = self.tank.search( self.tank.target_1 )
        if self.installed and p and self.draw_power(0.03,dt):            
            gray_dest, d, d = self.installed.station.search( EquipmentFilter( target='Storage', subtype='Gray Water' ) ) 
            if not gray_dest: return   
            self.active = True         
            proc_amt = max( 0, min( gray_dest.available_space, p.mass , self.processing_speed*dt ) )
            new_p = p.split(proc_amt)
            if not new_p: return
            new_p.quality['Contaminants'] = 0.09
            new_p.quality['Salt'] = 0.09            
            gray_dest.stowage.add(new_p)
        else:
            self.active = False         
        
class WaterPurifier(Machinery):
    '''Converts gray water into potable water.  Basically an abstracted still'''
    def __init__(self):   
        super(WaterPurifier, self).__init__()          
        self.processing_speed = 0.0001
        self.name = "Water Purifier"
        
    def update(self,dt):
        super(WaterPurifier, self).update(dt)    
        self.active = False           
        if self.installed and self.draw_power(0.03,dt): #TODO replace with actual distillation power use
            gray_source, d, d = self.installed.station.search( EquipmentFilter( target='Storage', subtype='Gray Water' ) )           
            pure_dest, d, d = self.installed.station.search( EquipmentFilter( target='Storage', subtype='Potable Water' ) )
            if not gray_source or not pure_dest: return            
            water = gray_source.stowage.remove('Water',min( self.processing_speed*dt, pure_dest.available_space ) )            
            if not water: return            
            self.active = True            
            for w in water:
                w.quality['Contaminants'] = 0.0
                w.quality['Salt'] = 0.0
                pure_dest.stowage.add( w )        
                       

class OxygenElectrolyzer(Machinery):
    '''Converts purified water to O2 (and disappears the H2 to space, presumably)'''
    def __init__(self):
        super(OxygenElectrolyzer, self).__init__()
        self.process_rate = 0.0001 #kg of water per second
        self.efficiency = 0.5
        self.power_draw = (self.process_rate * 1000 / (15.9994+2*1.008)) * 237 / self.efficiency
        self.name = "O2 Electrolyzer"

    def update(self,dt):
        super(OxygenElectrolyzer, self).update(dt)        
        self.active = False      
        if self.powered: #idling power use
            O2_content = self.installed.atmo.partial_pressure('O2')            
            if O2_content < 21.27:   #sea-level pp of oxygen.  
                #*Technically* we should also check for total pp, and release more O2 until like 40 kPa
                pure_src, d, d = self.installed.station.search( EquipmentFilter( target='Storage', subtype='Potable Water' ) )
                if pure_src and self.draw_power(self.power_draw,dt):
                    self.active = True
                    water = pure_src.stowage.remove('Water',self.process_rate*dt)
                    for w in water:
                        gasses = atmospherics.decompose_h2o(w.mass) #handle contaminated detritus somehow?
                        gasses['H2'] = 0 #H2 is "vented" into space, TODO check for storage container
                        self.installed.atmo.inject(gasses)

class RegenerableCO2Filter(Machinery):
    '''Collects excess (>0.4 kPa) CO2 and ejects it into space.  A bit magic atm, but we can fill in the details later'''
    def __init__(self):
        super(RegenerableCO2Filter, self).__init__()
        self.airflow = 0.01 #m^3 per second
        self.extraction_fraction = 0.5
        self.power_draw = .2 # kW
        self.pp_trigger = 0.04 #CO2 pp at sea level
        self.last_co2_reading = 1.0
        self.name = "CO2 Filter"

    def update(self,dt):
        super(RegenerableCO2Filter, self).update(dt)       
        self.active=False       
        if self.powered:
            CO2_content = self.installed.atmo.partial_pressure('CO2')            
            self.last_co2_reading = CO2_content            
            if CO2_content > self.pp_trigger and self.draw_power(self.power_draw,dt):
                self.active = True
                air_in = self.installed.atmo.extract('volume',self.airflow*dt)
                air_in['CO2'] = air_in[ 'CO2' ] * (1.0 - self.extraction_fraction)
                self.installed.atmo.inject(air_in)                                        

util.equipment_targets['Toilet'] = UniversalToilet
util.equipment_targets['CO2Filter'] = RegenerableCO2Filter
util.equipment_targets['Electrolyzer'] = OxygenElectrolyzer
util.equipment_targets['Purifier'] = WaterPurifier
