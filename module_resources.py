from atmospherics import Atmosphere

class Resource():
    def __init__(self, name, peak_capacity, storage_capacity, obj=None):
        self.name=name
        self.available=0
        self.previously_available=0
        
        #maximum amount allowed, or bad things happen (fuses blow, pipes burst)
        self.peak_capacity = peak_capacity 
        self.storage_capacity = storage_capacity
        self.obj = obj #optional pointer for relevant objects (e.g. Atmosphere)
       
    def merge(self,other):
        if self.name != other.name: return None
        self.available += other.available
        if self.obj and other.obj: 
            self.obj = self.obj.merge(other.obj)

    def update(self,dt):
        if self.name == "Electricity":
            #print self.available/dt, self.previously_available            
            frac = (dt/300.0)
            self.previously_available *= 1-frac
            self.previously_available += frac*self.available/dt
            self.available = 0#1-frac
            
    def draw(self,amt):
        if self.name == "Electricity":
            if self.previously_available < -0.9*self.peak_capacity: return 0
        else:
            if self.available < amt: return 0
        self.available -= amt
        return amt
        
            
    def status(self):
        return ' '.join([self.name,str(self.available),str(self.previously_available),str(self.storage_capacity)])            

class ResourceBundle():
    def __init__(self):
        self.contributors = 1
        self.resources = {  'Electricity' : Resource('Electricity', 10, 0)} 
                            
    def merge(self, new_resource):
        for (k,v) in self.resources: v.merge(new_resource[k])
        self.contributors += 1
        
    def grow(self):
        """Simple stretching of available resource space"""
        for (v) in self.resources.values():
             v.storage_capacity += v.storage_capacity/self.contributors
        self.contributors += 1                            
        
    def update(self,dt):
        for k in self.resources:
            self.resources[k].update(dt)
            
            
