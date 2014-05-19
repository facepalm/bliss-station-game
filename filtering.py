import clutter
import equipment
import needs
import util

class SearchFilter(object):
    def __init__(self, target=None, **kwargs):
        self.target = target
        self.comparison_type = 'All' if not 'comparison_type' in kwargs else kwargs['comparison_type']
        self.check_storage = False if not 'check_storage' in kwargs else kwargs['check_storage']

    def compare(self,obj):
        return obj is self.target
        
class Searcher(): #wrapper around search method to allow it to be called later
    def __init__(self, filter_, station, **kwargs):
        self.station=station
        self.filter = filter_ if isinstance( filter_, SearchFilter ) else SearchFilter( filter_, **kwargs )
        self.exclude=[] if not 'exclude' in kwargs else kwargs['exclude']
                
    def search(self):
        return self.station.search(self.filter, modules_to_exclude=self.exclude)
        
class ClutterFilter(SearchFilter):
    def __init__(self,target=['All'],  **kwargs):    
        super(ClutterFilter, self).__init__(target=target, **kwargs)              
            
    def compare(self,obj):
        if self.check_storage and isinstance( obj, equipment.Storage ):
            return obj.stowage.search(self)
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
        return clutter.equals(self.target[0], obj.name)
        
    def target_string(self):
        out = ''
        for et,t in enumerate(self.target):
            if et > 0: out = ''.join([out,'/'])
            out = ''.join([out,t])
        return out        
        
        
class NeedFilter(SearchFilter):
    def __init__(self,target='Food', **kwargs):    
        super(NeedFilter, self).__init__(target=target, **kwargs)       
        
    def compare(self,obj):
        if not hasattr(obj,'satisfies'): return False
        if not self.target in obj.satisfies: return False        
        return obj.satisfies[self.target]
        
        
class EquipmentFilter(SearchFilter):        
    def __init__(self,target='Storage', comparison_type='Equipment', subtype='Any', **kwargs):    
        super(EquipmentFilter, self).__init__(target=target, comparison_type=comparison_type, **kwargs)       
        self.subtype=subtype
        self.equipment_targets = util.equipment_targets
        
    def compare(self,obj):
        if self.target == 'Storage' and isinstance( obj, equipment.Storage):
            #print obj, obj.filter.target, self.subtype, self.subtype in obj.filter.target or self.subtype == 'Any'
            return self.subtype in obj.filter.target or self.subtype == 'Any'
        if self.target in self.equipment_targets: 
            return isinstance( obj, self.equipment_targets [ self.target ] )    
        if self.comparison_type == 'Equipment Slot':
            return obj == self.target
      
