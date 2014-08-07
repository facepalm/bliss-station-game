import clutter
import equipment.general
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
        if self.check_storage and isinstance( obj, equipment.general.Storage ):
            return obj.stowage.search(self)
        if not isinstance(obj,clutter.Clutter): return False
        return obj.satisfies(self.target[0])
        
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
    def __init__(self,target='Storage', comparison_type='Equipment', subtype='Any', is_installed=False, **kwargs):    
        super(EquipmentFilter, self).__init__(target=target, comparison_type=comparison_type, **kwargs)       
        self.subtype=subtype
        self.equipment_targets = util.equipment_targets
        self.check_if_installed = is_installed
        
    def compare(self,obj):        
        from equipment.science import Experiment
        if self.check_if_installed and (not hasattr(obj, 'installed') or not obj.installed): return False
        if self.target == 'Storage' and isinstance( obj, equipment.general.Storage):
            #print obj, obj.filter.target, self.subtype, self.subtype in obj.filter.target or self.subtype == 'Any'
            return self.subtype in obj.filter.target or self.subtype == 'Any'
        elif self.target in self.equipment_targets: 
            return isinstance( obj, self.equipment_targets [ self.target ] ) 
        elif self.comparison_type == 'Equipment Slot':
            return obj == self.target
        elif self.subtype == "Dead Science" and isinstance( obj, Experiment):
            return obj.no_more_SCIENCE
        elif self.subtype == "Live Science" and isinstance( obj, Experiment):
            return not obj.no_more_SCIENCE    
        elif self.target=="By Name":
            return hasattr(obj, 'name') and obj.name == self.subtype
        elif self.target=="By ID":
            return hasattr(obj, 'id') and obj.id == self.subtype
            
            
    def target_string(self):        
        return self.target + "-" + self.subtype            
      
      
class ManifestFilter(SearchFilter):
    '''Specialized filter for fulfilling manifest results'''
    pass
    
