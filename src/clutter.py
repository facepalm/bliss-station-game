import random
import util
import numpy as np
import globalvars as gv

#miscellaneous stuff related to the loose objects one might find floating around the station

common_densities =   {  'Oxygen Candles' : 2420.0,
                        'Supplies' : 1000.0 }

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
    def __init__(self, name='Trash', mass=0.1, density=1000.0, quality=dict()): 
        self.id = util.register(self)   
        if not hasattr(self,'name'): self.name = name
        if not hasattr(self,'mass'): self.mass = mass
        if not hasattr(self,'quality'): self.quality = quality
        self.local_coords = 0.75*np.array([random.uniform(-1,1),random.uniform(-1,1),0])
        self.sprite = None
        if isinstance(self.quality,dict):
            if self.name == 'Medical Supplies': self.quality['Medical'] = self.mass
            if self.name == 'Mechanical Supplies': self.quality['Spare Parts'] = self.mass
            if self.name == 'General Supplies': 
                for q in self.quality.keys():
                    self.quality[q] = self.mass / len(self.quality.keys())
        if self.name in common_subtypes: self.name = common_subtypes[self.name]
        if not hasattr(self,'density'): self.density = common_densities[self.name] if self.name in common_densities.keys() else density
        
        self.refresh_image()
        
    def update(self,dt):
        if self.mass <= 0:
            self.sprite.visible=False
        
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
        if not hasattr(self,'imgfile'):              
            if self.name == "Solid Waste":
                self.imgfile = 'images/glitch-assets/loam/loam__x1_40_iconic_png_1354832758.png'
            else:
                self.imgfile = 'images/glitch-assets/contraband/contraband__x1_1_png_1354836014.png'
        if self.sprite: self.sprite.delete()
        self.sprite = util.load_sprite(self.imgfile)
        self.sprite.batch = util.station_batch
        
    def get_volume(self): return self.mass/self.density
    volume = property(get_volume, None, None, "Clutter volume" )  
    
    def split(self, amt, subtype=None):
        if amt <= 0: return None
        curr_amt = min(amt, self.mass)   
        self.mass -= curr_amt
        return type(self)(name=self.name, mass=curr_amt, density=self.density, quality= self.quality.copy() if self.quality else None)
        
    def merge(self, other):        
        if not isinstance(other, Clutter): assert False, 'Requested merge a nonClutter object. Denied.'
        if not equals(self.name,other.name): return False
        self.mass += other.mass
        #TODO merge qualities as well
        return True
        
    def satisfies(self, name):
        return equals(name, self.name)    

class MetalClutter(Clutter):
    def __init__(self, *args, **kwargs):
        self.subtype = kwargs['subtype'] if 'subtype' in kwargs else 'Aluminum'                
        self.imgfile = 'images/glitch-assets/molybdenum/molybdenum__x1_iconic_png_1354832628.png'
        self.quality = {'Purity': 1.0, 'Form':'Ingot' }
        if 'Scrap' in kwargs['name']: 
            self.quality['Form'] = 'Scrap'
        self.name='Metal'
        Clutter.__init__(self, *args, **kwargs)   
        
    def calcDensity(self):
        if self.subtype == 'Aluminum': return 2700 #kg/m3
        if self.subtype in ['Iron','Steel']: return 7874
        if self.subtype in ['Copper']: return 8960
        if self.subtype in ['Tin']: return 7365
        if self.subtype in ['Bronze']: return 0.78*8960 + 0.12*7365
    density = property(calcDensity, None, None, "Metal Density" )   
        
    def satisfies(self, name):
        if 'Scrap' in name:
            return self.quality['Form'] == 'Scrap' and self.satisfies(name.strip('Scrap '))
        elif 'Ingot' in name:
            return self.quality['Form'] == 'Ingot' and self.satisfies(name.rstrip(' Ingot'))
        elif name != 'Metal':
            return self.subtype == name
        return equals(name, self.name)
        
class FoodClutter(Clutter):
    def __init__(self, *args, **kwargs):
        self.density = 714.33 #kg/m3
        self.imgfile = 'images/glitch-assets/pi/pi__x1_rescaled_iconic_png_1354839579.png'
        self.quality = {'Freshness': 0.0, 'Contaminants' : 0.0, 'Perishability': 0.00002, 'Spoilage':0.0, 'Nutrient': [1.0, 1.0, 1.0, 1.0, 1.0], 'Flavor': [0.5, 0.5, 0.5, 0.5, 0.5] } #Bland, nutritious, lasting food
        if kwargs['name'] in ['Spoiled Food']: 
            self.quality['Spoilage']= 1.0
        self.name='Food'
        Clutter.__init__(self, *args, **kwargs)   
        
    def satisfies(self, name):
        if name == 'Nonperishable Food':
            return self.quality['Contaminants'] <= 0.05 and self.quality['Spoilage'] <= 0.05 and self.quality['Perishability'] <= 0.005
        elif name == 'Edible Food':
            return self.quality['Contaminants'] <= 0.05 and self.quality['Spoilage'] <= 0.05
        return equals(name, self.name)           
        
class WaterClutter(Clutter):
    def __init__(self, *args, **kwargs):
        self.density = 1000.0 #kg/m3
        self.imgfile = 'images/glitch-assets/cup_of_water/cup_of_water__x1_iconic_png_1354833111.png'
        if kwargs['name'] in ['Water','Potable Water']: 
            self.quality = {'Contaminants' : 0.0, 'Salt': 0.0, 'pH' : 7.0 } #distilled water
        elif kwargs['name'] =='Gray Water': 
            self.quality = {'Contaminants' : 0.1, 'Salt': 0.1, 'pH' : 7.0 } #cleanish water
        else: # kwargs['name'] =='Waste Water': 
            self.quality = {'Contaminants' : 2.0, 'Salt': 3.0, 'pH' : 7.0 } #used water
        self.name='Water'
        Clutter.__init__(self, *args, **kwargs)
        
    def satisfies(self, name):
        if name == 'Potable Water':
            return self.quality['Contaminants'] <= 0.05 and self.quality['Salt'] <= 0.05
        elif name == 'Gray Water' and not self.satisfies('Potable Water'):
            return self.quality['Contaminants'] <= 0.1 and self.quality['Salt'] <= 0.1
        elif name == 'Waste Water' and not self.satisfies('Gray Water') and not self.satisfies('Potable Water'):
            return True            
        return equals(name, self.name)          
        
        
class ComplexClutter(Clutter):
    tech={} #min tech required for reaction
    reaction={} #recipe to create this clutter
        
    
    ''' Clutter comprised of other clutters '''
    def __init__(self, *args, **kwargs):
        self.composition = [] #list of raw materials making this guy up
        Clutter.__init__(self, *args, **kwargs)                           
        
                
        
class PartsClutter(ComplexClutter):
    tech = {'Materials':1}
    reaction = {'Input': {'Metal Ingot':1.0}, 'Output':{'Basic Parts':0.9, 'Scrap Metal':0.1}}        
        
    
    def __init__(self, *args, **kwargs):
        self.name='Basic Parts'
        self.imgfile = 'images/glitch-assets/metalmaker_mechanism/metalmaker_mechanism__x1_1_png_1354836814.png'
        ComplexClutter.__init__(self, *args, **kwargs)   
        self.sprite.scale = 0.4
        

class MechPartsClutter(ComplexClutter):
    tech = {'Materials':1,'Thermodynamics':1}
    reaction = {'Input': {'Basic Parts':0.5,'Metal Ingot':0.5}, 'Output':{'Mechanical Parts':0.67, 'Scrap Metal':0.33}}                
    
    def __init__(self, *args, **kwargs):
        self.name='Mechanical Parts'
        self.imgfile = 'images/glitch-assets/metalmaker_tooler/metalmaker_tooler__x1_1_png_1354836816.png'
        ComplexClutter.__init__(self, *args, **kwargs)   
        self.sprite.scale = 0.33
                        
                     
def spawn_clutter(name='Water',mass=1, density=1000.0):
    if name in ['Water','Potable Water','Gray Water','Waste Water']:
        return WaterClutter(name=name,mass=mass)
    elif name in ['Food']:
        return FoodClutter(name=name,mass=mass)
    elif 'Aluminum' in name:
        return MetalClutter(name=name,mass=mass)
    elif name in ['Basic Parts']:
        return PartsClutter(name=name, mass=mass)
    elif name in ['Mechanical Parts']:
        return MechPartsClutter(name=name, mass=mass)
    return Clutter(name,mass, density)
    
def run_clutter_reaction(goal, inputs):    
    reaction=None
    if isinstance(goal, Clutter):
        reaction = goal.reaction
    else:
        tmp = spawn_clutter(goal,mass=0)        
        if hasattr(tmp,'reaction'):
            reaction=tmp.reaction
        else:
            return []
        
    used_inputs=dict()
    reqs = reaction['Input'].keys()
    net_amt = 1000000000000 #total reaction mass
    for r in reqs:
        req_satisfied = False
        for i in inputs:
            if i.satisfies(r):
                req_satisfied = True
                net_amt = min( net_amt, i.mass/reaction['Input'][r] )
                used_inputs[r] = i                    
                inputs.remove(i)
                break
        if not req_satisfied:
            return []
        
    #at this point, we can run the reaction
    comp=[]
    for r in used_inputs.keys():
        comp.append( used_inputs[r].split( net_amt * reaction['Input'][r] ) )
                   
    out = [self]
    for r in reaction['Output'].keys():
        i = spawn_clutter(r, net_amt * self.reaction[ 'Output' ][ r ] ) 
        out.append(i)
        if hasattr(i,composition):
            for c in comp:
                c.mass *= self.reaction[ 'Output' ][ r ]
            i.composition = comp            
    return out

    
class Stowage(object):
    def __init__(self, capacity=1):    
        self.capacity=capacity
        self.contents=[]
        self.internal=False #True if storage is meant to be "hidden"
                        
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
            stuff.sprite.visible = False
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
            
