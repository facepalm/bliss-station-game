import clutter
import needs

class Filter(object):
    def __init__(self, target=None):
        self.target = target

    def compare(self,obj):
        return obj is self.target
        
class ClutterFilter(Filter):
    def __init__(self,target=['All']):    
        super(ClutterFilter, self).__init__(target)              
            
    def compare(self,obj):
        if not isinstance(obj,clutter.Clutter): return False
        if 'Potable Water' in self.target and obj.name == 'Water': 
            if 'Contaminants' in obj.quality and 'Salt' in obj.quality:
                return obj.quality['Contaminants'] <= 0.01 and obj.quality['Salt'] <= 0.01
        elif 'Gray Water' in self.target and obj.name == 'Water': 
            if 'Contaminants' in obj.quality and 'Salt' in obj.quality:
                return obj.quality['Contaminants'] <= 0.1 and obj.quality['Salt'] <= 0.1 and obj.quality['Contaminants'] > 0.01 and obj.quality['Salt'] > 0.01
        elif 'Waste Water' in self.target and obj.name == 'Water': 
            if 'Contaminants' in obj.quality and 'Salt' in obj.quality:
                return obj.quality['Contaminants'] > 0.1 or obj.quality['Salt'] > 0.1      
        elif 'Nonperishable Food' in self.target and obj.name == 'Food': 
            if 'Contaminants' in obj.quality and 'Spoilage' in obj.quality:
                return obj.quality['Contaminants'] <= 0.05 and obj.quality['Spoilage'] <= 0.05 and obj.quality['Perishability'] <= 0.005
        elif 'Edible Food' in self.target and obj.name == 'Food': 
            if 'Contaminants' in obj.quality and 'Spoilage' in obj.quality:
                return obj.quality['Contaminants'] <= 0.05 and obj.quality['Spoilage'] <= 0.05
        return clutter.equals(self.target, obj.name)
        
    def target_string(self):
        out = ''
        for et,t in enumerate(self.target):
            if et > 0: out = ''.join([out,'/'])
            out = ''.join([out,t])
        return out        
        
        
class NeedFilter(Filter):
    def __init__(self,target='Food'):    
        super(NeedFilter, self).__init__(target)       
        
    def compare(self,obj):
        if not hasattr(obj,'satisfies'): return False
        if not self.target in obj.satisfies: return False        
        return obj.satisfies[self.target]
        
