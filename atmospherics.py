
GAS_R = 0.0083144621 # m^3 * kPa / K * mol

#def Pressure2Moles(total_volume, total_pressure, temperature):
    

class Atmosphere():
    def __init__(self, volume=1):
        self.volume = volume
            
        self.temperature=273        
        
        self.composition={'O2' : 0, 'N2' : 0, 'CO2':0 , 'Aromatics':0, 'Fragrants':0, 'Particulates':0}    
    
    def initialize(self, composition="Air"):        
        #PV=nRT
        if composition=='Air': #P= 1 atm (101.3 kPa), T=273K
            _moles = (101.3*self.volume)/(GAS_R*273)
            self.composition['O2'] = 0.21 * _moles
            self.composition['N2'] = 0.78 * _moles
            self.composition['CO2'] = 0.004 * _moles
        elif composition=='O2 Tank':
            _moles = (10130*self.volume)/(GAS_R*273)
            self.composition['O2'] = _moles
        elif composition=='N2 Tank':
            _moles = (10130*self.volume)/(GAS_R*273)
            self.composition['N2'] = _moles    
            
    def total_moles(self):
        return sum(self.composition.values())
            
    def get_pressure(self): return self.total_moles() * GAS_R * self.temperature / self.volume        
    pressure = property(get_pressure, None, None, "Pressure reading" ) 
            
    def inject(self,composition):
        if not composition: return False
        for x in composition.keys():
            self.composition[x] = (self.composition[x] + composition[x]) if x in self.composition.keys() else composition[x]
         
    def extract(self,extr_type='pressure',delta=0):
        out_composition = dict()
        ratio = delta/self.pressure if extr_type == 'pressure' else delta/self.volume
        for x in self.composition.keys():
            out_composition[x] = self.composition[x]*ratio
            self.composition[x] -= self.composition[x]*ratio
        return out_composition        
            
    def equalize(self, atmo):
        if not atmo: return False
        """Pressure differentials cause exchange in atmospheres"""
        p_us = self.pressure * self.volume / (self.volume + atmo.volume)
        p_them = atmo.pressure * atmo.volume / (self.volume + atmo.volume)
        p_new = p_us + p_them
        if self.pressure > p_new:
            draft = self.extract('pressure',self.pressure - p_new)
            atmo.inject(draft)
        else:
            draft = atmo.extract('pressure',atmo.pressure - p_new)
            self.inject(draft) 
            
    def mix (self, atmo, volume = 0.1 ):
        if not atmo: return False    
        mine = self.extract('volume',volume)
        theirs = atmo.extract('volume',volume)
        self.inject(theirs)
        atmo.inject(mine)    
        
    def merge(self,atmo):
        new_total_moles = self.total_moles() + atmo.total_moles()
        self.temperature = (self.total_moles()*self.temperature + atmo.total_moles()*atmo.temperature)/(new_total_moles)
        self.volume += atmo.volume
        self.inject(atmo.composition)
        
    def split(self,fraction=0.5):
        out = self.extract('volume',fraction*self.volume)
        return out
        
if __name__ == "__main__":
    test=Atmosphere()    
    bottle=Atmosphere()
    test.initialize('O2 Tank')
    bottle.initialize('N2 Tank')
    print test.pressure, bottle.pressure
    test.equalize(bottle)
    print test.pressure, bottle.pressure
    print test.composition    
    test.mix(bottle)
    print test.pressure, bottle.pressure
    print test.composition  
