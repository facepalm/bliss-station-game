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
    density_multiplier = 1.0

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
    
    def split(self, amt):
        if amt <= 0: return None
        curr_amt = min(amt, self.mass)   
        self.mass -= curr_amt
        ret = type(self)(name=self.name, mass=curr_amt, density=self.density, quality= self.quality.copy() if self.quality else None)
        if hasattr(self,'subtype'): ret.subtype = self.subtype
        return ret
    
    def check_merge(self,obj):
        if not isinstance(obj, Clutter): return False
        if not equals(self.name,obj.name): return False
        return True    
        
    def merge(self, other):        
        if not self.check_merge(other): return False
        self.mass += other.mass
        other.mass = 0
        #TODO merge qualities as well
        return True
        
    def satisfies(self, name):
        return equals(name, self.name)  
        
    def __repr__(self):
        return ''.join([self.name,':',str(self.mass)])  

    def extract_subtype(self,name):
        if not hasattr(self,'possible_subtypes') or not self.possible_subtypes: return None
        for p in self.possible_subtypes.keys():
            if p in name: return p
        return self.possible_subtypes.keys()[0]
        
    def calcSubtypeDensity(self):
        if not (hasattr(self,'subtype') and hasattr(self,'possible_subtypes') and self.possible_subtypes): return 1000.0
        if self.subtype in self.possible_subtypes.keys():
            return self.possible_subtypes[self.subtype]

class MetalClutter(Clutter):
    possible_subtypes = {'Steel':7874.0,'Iron':7874,'Aluminum':2700,'Bronze':7872.6,'Tin':7365}

    def __init__(self, *args, **kwargs):
        if not hasattr(self,'subtype'): self.subtype = kwargs['subtype'] if 'subtype' in kwargs else self.extract_subtype(kwargs['name'])                
        if not hasattr(self,'imgfile'): self.imgfile = 'images/glitch-assets/molybdenum/molybdenum__x1_iconic_png_1354832628.png'
        self.quality = {'Purity': 1.0, 'Form':'Ingot' }
        if 'Scrap' in kwargs['name']: 
            self.quality['Form'] = 'Scrap'
        elif 'Wire' in kwargs['name']: 
            self.quality['Form'] = 'Wire'
        self.name='Metal'
        Clutter.__init__(self, *args, **kwargs)   
        
    def check_merge(self,obj):
        if not isinstance(obj, MetalClutter): return False
        if self.subtype != obj.subtype: return False
        if self.quality['Form'] != obj.quality['Form']: return False
        return True
        
    def merge(self,other):
        oldm, theirm = self.mass, other.mass
        test = Clutter.merge(self,other)
        if not test: return
        self.quality['Purity'] = self.quality['Purity'] * oldm/self.mass + other.quality['Purity'] * theirm/self.mass                    
        
    def calcDensity(self):
        return self.calcSubtypeDensity()            
    density = property(calcDensity, None, None, "Metal Density" )   
        
    def satisfies(self, name):
        if 'Scrap' in name:
            return self.quality['Form'] == 'Scrap' and self.satisfies(name.strip('Scrap '))
        elif 'Ingot' in name:
            return self.quality['Form'] == 'Ingot' and self.satisfies(name.rstrip(' Ingot'))
        elif 'Wire' in name:
            return self.quality['Form'] == 'Wire' and self.satisfies(name.rstrip(' Wire'))        
        elif name != 'Metal':
            return self.subtype == name
        return equals(name, self.name)
        
    def __repr__(self):
        return ''.join([self.subtype,' ',self.quality['Form'],':',str(self.mass)])
        
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

class Plastic(Clutter):
    def __init__(self, *args, **kwargs):
        self.density = 500.0 #kg/m3
        self.imgfile = 'images/glitch-assets/molybdenum/plastic.png'
        self.quality = {'Oxidation' : 0.0 } #TODO replace with whatever process causes plastics to just crumble over time
        self.name='Plastic'
        Clutter.__init__(self, *args, **kwargs)        
        
class PreciousMetal(MetalClutter):
    subtypes = {'Silver':8000.0, 'Gold':10000.0,'Copper':8960.0,'Platinum':8000.0}
    
    def __init__(self, *args, **kwargs):
        self.subtype = kwargs['subtype'] if 'subtype' in kwargs else self.extract_subtype(kwargs['name'])                        
        self.imgfile = 'images/glitch-assets/molybdenum/molybdenum__x1_iconic_png_1354832628.png' #TODO find/make better image        
        Metal.__init__(self, *args, **kwargs)           
        self.name='PreciousMetal'
        
    def check_merge(self,obj):
        if not isinstance(obj, PreciousMetal): return False
        return MetalClutter.check_merge(self,obj)                           
        
    def satisfies(self, name):
        if name == 'PreciousMetal':
            return equals(name, self.name)    
        else:
            return MetalClutter.satisfies(self,name)
                
class ComplexClutter(Clutter):
    tech={} #min tech required for reaction
    reaction={} #recipe to create this clutter
        
    
    ''' Clutter comprised of other clutters '''
    def __init__(self, *args, **kwargs):
        self.composition = [] #list of raw materials making this guy up
        Clutter.__init__(self, *args, **kwargs) 
                                  
        
    def calcDensity(self):
        if not self.composition: return 1000.0*self.density_multiplier
        totmass = 0.0
        dens = 0.0
        for c in self.composition:
            totmass += c.mass
        for c in self.composition:
            dens += c.density * (c.mass/totmass)
        return dens * self.density_multiplier
    density = property(calcDensity, None, None, "Material Density" ) 
    
    
    def split(self, amt):
        obj = Clutter.split(self,amt)
        for c in self.composition:
            obj.composition.append(c.split(amt))        
        return obj
                
        
class PartsClutter(ComplexClutter):
    tech = {'Materials':1}
    reaction = {'Input': {'Metal Ingot':1.0}, 'Output':{'Basic Parts':0.9, 'Scrap Metal':0.1}, 'Tech':{'Materials':1}, 'Reactor':['Machine Shop'], 'Type':'Continuous'}        
    density_multiplier = 0.5
    
    def __init__(self, *args, **kwargs):
        self.name='Basic Parts'
        self.imgfile = 'images/glitch-assets/metalmaker_mechanism/metalmaker_mechanism__x1_1_png_1354836814.png'
        
        ComplexClutter.__init__(self, *args, **kwargs)   
        if self.sprite: self.sprite.scale = 0.4
        

class MechPartsClutter(ComplexClutter):
    tech = {'Materials':1,'Thermodynamics':1}
    reaction = {'Input': {'Basic Parts':0.5,'Metal Ingot':0.5}, 'Output':{'Mechanical Parts':0.87, 'Scrap Metal':0.13}, 'Tech':{'Materials':1,'Thermodynamics':1}, 'Reactor':['Machine Shop'], 'Type':'Continuous'}                
    density_multiplier = 0.25
    
    def __init__(self, *args, **kwargs):
        self.name='Mechanical Parts'
        self.imgfile = 'images/glitch-assets/metalmaker_tooler/metalmaker_tooler__x1_1_png_1354836816.png'
        
        ComplexClutter.__init__(self, *args, **kwargs)   
        if self.sprite: 
            self.sprite.scale = 0.33          
            #self.sprite.image.anchor_x *= 0.33
            #self.sprite.image.anchor_y *= 0.33
                        
                     
def spawn_clutter(name='Water',mass=1, density=1000.0):
    if name in ['Water','Potable Water','Gray Water','Waste Water']:
        return WaterClutter(name=name,mass=mass)
    elif name in ['Food']:
        return FoodClutter(name=name,mass=mass)
    elif 'Aluminum' in name or 'Steel' in name or 'Metal' in name:
        return MetalClutter(name=name,mass=mass)
    elif name in ['Basic Parts']:
        return PartsClutter(name=name, mass=mass)
    elif name in ['Mechanical Parts']:
        return MechPartsClutter(name=name, mass=mass)
    return Clutter(name,mass, density)
    
def run_reaction(goal, inputs, cap_vol=10000000000000):    
    reaction=None
    dens_mult=1.0
    if isinstance(goal, Clutter):
        reaction = goal.reaction
        dens_mult = goal.density_multiplier
    else:
        tmp = spawn_clutter(goal,mass=0)        
        if hasattr(tmp,'reaction'):
            reaction=tmp.reaction
            dens_mult = tmp.density_multiplier
        else:
            return inputs
        
    used_inputs=dict()
    reqs = reaction['Input'].keys()
    net_vol = cap_vol #total reaction mass
    metal_type = None
    for r in reqs:
        req_satisfied = False
        for i in inputs:
            if i.satisfies(r):
                req_satisfied = True
                if 'Metal' in r: metal_type = i.subtype
                net_vol = min( net_vol, (i.mass/i.density)/(reaction['Input'][r]*dens_mult) )
                used_inputs[r] = i                    
                inputs.remove(i)
                break
        if not req_satisfied:
            return inputs
        
    out = inputs    
        
    #at this point, we can run the reaction
    comp=[]
    for r in used_inputs.keys():
        i = used_inputs[r]
        comp.append( i.split( i.density * net_vol * reaction['Input'][r] * dens_mult ) )
        out.append( i )
                   
    
    for r in reaction['Output'].keys():
        i = spawn_clutter(r, net_vol * reaction[ 'Output' ][ r ] ) #using volume as mass for now
        if 'Metal' in r: i.subtype = metal_type
        out.append(i)
        if hasattr(i,'composition'):
            for c in comp:
                c.mass *= reaction[ 'Output' ][ r ] * dens_mult
            i.composition = comp            
        i.mass *= i.density #correcting the placeholder value used above
        
    for i in out:
        for j in out:            
            if i is j or i.mass == 0 or j.mass == 0: continue
            print i,j
            i.merge(j)
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
        
    def search_info(self, filter_):
        mass,vol = 0,0
        stuff=[]
        stuff.extend( [ v for v in self.contents if filter_.compare( v ) ] )
        for s in stuff:    
            mass += s.mass
            vol += s.mass/s.density
        return mass,vol        
        
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
    
    def dump_into(self,other):
        if not isinstance(other,Stowage): return False
        for i in self.contents:
            if not other.add(i): return False            
            self.remove(i)
        return True
        
    
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
            


                
if __name__ == "__main__": 
    gv.config['GRAPHICS'] = None
    metal = spawn_clutter('Steel Ingots',1000)
    inter = run_reaction('Basic Parts',[metal],.05)
    print inter
    #inter.append(metal)
    out = run_reaction('Mechanical Parts',inter,.05)
    print out
    print sum([m.mass for m in out])
    for m in out:
        if hasattr(m,'composition'):
            print m,':',m.composition
