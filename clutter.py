import random
import util
import numpy as np
import globalvars as gv

#miscellaneous stuff related to the loose objects one might find floating around the station

common_densities =   {  'Food' : 714.33,
                        'Water' : 1000.0,
                        'Oxygen Candles' : 2420.0,
                        'Supplies' : 1000.0 }
                        
common_qualities = {    'Water' : {'Contaminants' : 0.0, 'Salt': 0.0, 'pH' : 7.0 }, #distilled water
                        'Waste Water' : {'Contaminants' : 2.0, 'Salt': 3.0, 'pH' : 7.0 }, #distilled water
                        'Food' : {'Freshness': 1.0, 'Contaminants' : 0.0, 'Perishability': 0.00002, 'Spoilage':0.0, 'Nutrient': [1.0, 1.0, 1.0, 1.0, 1.0], 'Flavor': [0.5, 0.5, 0.5, 0.5, 0.5] }, #Bland, nutritious, lasting food
                        'Supplies' : {'Medical':0.0, 'Tools':0.0, 'Spare Parts':0.0, 'Chemicals':0.0, 'Electronics':0.0 }
                   }

common_subtypes = {     'Waste Water' : 'Water', 
                        'Medical Supplies':'Supplies', 
                        'Mechanical Supplies':'Supplies',
                        'General Supplies':'Supplies' }

gather_rate = 0.001 #m^3/s - rate of grabbing a handful of something and putting it somewhere else

def equals(type1,type2):
    if not type1 and not type2: return True
    if not type1 or not type2: return False
    if type1 == 'Any' or type2 == 'Any': return True
    if type1 == type2: return True
    return False    
    
class Clutter(object):    
    def __init__(self, name='Trash', mass=0.1, density=0.1, quality=None): 
        self.id = util.register(self)   
        self.name = name
        self.mass = mass
        self.quality = quality if quality else common_qualities[self.name] if self.name in common_qualities.keys() else None
        self.local_coords = 0.75*np.array([random.uniform(-1,1),random.uniform(-1,1),0])
        self.sprite = None
        if isinstance(self.quality,dict):
            if self.name == 'Medical Supplies': self.quality['Medical'] = self.mass
            if self.name == 'Mechanical Supplies': self.quality['Spare Parts'] = self.mass
            if self.name == 'General Supplies': 
                for q in self.quality.keys():
                    self.quality[q] = self.mass / len(self.quality.keys())
        if self.name in common_subtypes: self.name = common_subtypes[self.name]
        self.density = common_densities[self.name] if self.name in common_densities.keys() else density
        
        self.refresh_image()
        
    def __getstate__(self):
        d = dict(self.__dict__)
        del d['sprite']
        return d    
        
    def __setstate__(self, d):
        self.__dict__.update(d)      
        self.sprite=None
        self.refresh_image()
        
        
    def refresh_image(self):    
        if not gv.config['GRAPHICS']: return                
        if self.name == 'Water': 
            self.imgfile = 'images/glitch-assets/cup_of_water/cup_of_water__x1_iconic_png_1354833111.png'
        elif self.name == 'Food':    
            self.imgfile = 'images/glitch-assets/pi/pi__x1_rescaled_iconic_png_1354839579.png'
        elif self.name == "Solid Waste":
            self.imgfile = 'images/glitch-assets/loam/loam__x1_40_iconic_png_1354832758.png'
        else:
            self.imgfile = 'images/glitch-assets/contraband/contraband__x1_1_png_1354836014.png'
        self.sprite = util.load_sprite(self.imgfile)
        
    def get_volume(self): return self.mass/self.density
    volume = property(get_volume, None, None, "Clutter volume" )  
    
    def split(self, amt, subtype=None):
        if amt < 0: assert False, 'Requested to split a negative amount. Denied.'
        curr_amt = min(amt, self.mass)   
        self.mass -= curr_amt
        return Clutter(self.name, curr_amt, self.density)
        
    def merge(self, other):        
        if not isinstance(other, Clutter): assert False, 'Requested merge a nonClutter object. Denied.'
        if not equals(self.name,other.name): return False
        self.mass += other.mass
        #TODO merge qualities as well, if water
        return True
        
    
class Stowage(object):
    def __init__(self, capacity=1):    
        self.capacity=capacity
        self.contents=[]
                        
    def search(self, filter_):
        stuff=[]
        stuff.extend( [ v for v in self.contents if filter_.compare( v ) ] )
        if stuff:
            return stuff[0]
        return None
        
    def update(self, dt):
        for c in self.contents:
            if hasattr(c,'update'): c.update(dt)
            if c.mass == 0:
                self.contents.remove(c)
        
    def remove (self, target, amt=1):
        if not isinstance(target, str): return self.remove_obj(target)
        if amt <= 0: return None
        out=[]
        cum_amt=0
        for v in self.contents:
            if equals(target, v.name):
                bite = v.split(amt-cum_amt)
                out.append(bite)
                cum_amt += bite.mass
                if v.mass <= 0: self.contents.remove(v) 
            if cum_amt >= amt: break
        return out
        
    def remove_obj(self,target):
        if target in self.contents:           
            self.contents.remove(target)
            return [target]
        return []
        
                
    def add (self, stuff=None):
        #if not ( isinstance(stuff,Clutter) or isinstance(stuff,Equipment)): return False
        if not stuff: return True
        if stuff.volume > self.free_space: 
            print "Storage overflow!"
            return False
        if stuff in self.contents: return False
        if isinstance(stuff, Clutter): 
            for v in self.contents:
                if isinstance(v,Clutter) and v.merge(stuff): 
                    return True
        self.contents.append(stuff)
        return True
        
    def get_free_space(self): 
        used_space=0
        for i in self.contents:
            used_space += i.volume
        return self.capacity - used_space        
    free_space = property(get_free_space, None, None, "Available storage space" )                  
        
    
class JanitorMon(object):
    def __init__(self,target= ['All']):    
        self.target=target
        
    def task_work_report(self,task,dt):
        if task.name.startswith('Pick Up'):
            #print self.target, task.target
            #print gather_rate, dt, task.target.density, task.assigned_to.inventory.free_space
            remove_amt = min(gather_rate*dt*task.target.density,task.assigned_to.inventory.free_space*task.target.density)
            if remove_amt <= 0: return
            #clut_type = task.name.split('Pick Up')[1].strip()            
            obj = task.target.split(remove_amt)
            task.assigned_to.inventory.add(obj)
            
