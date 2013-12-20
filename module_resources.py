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
            self.previously_available -= min(1,dt)*self.previously_available
            self.previously_available += min(1,dt)*self.available
            self.available -= min(1,dt)*self.available

class ResourceBundle():
    def __init__(self):
        self.contributors = 1
        self.resources = {  'Electricity' : Resource('Electricity', 10, 0), 
                            'Potable Water' : Resource('Potable Water', 10, 10),
                            'Gray Water' : Resource('Gray Water', 10, 10),
                            'Air Out' : Resource('Air Out', 1, 1, Atmosphere),
                            'Air In' : Resource('Air In', 1, 1, Atmosphere)  }
                            
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
