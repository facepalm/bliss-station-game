class EquipmentSearchBroke():    
    
    def __init__(self, target, station, check_storage=False, resource_obj=None, storage_filter='Any'):
        self.target=target
        self.station=station
        self.equipment_targets = util.equipment_targets
        self.check_storage = check_storage #if True, will search inside storage equipment as well as loose clutter
        self.required_resource = resource_obj #if not None, will require w/e to be in a station sharing the res obj
        self.storage_filter = storage_filter # will check the filter of any storage eq
    
    def compare(self,obj):
        if self.required_resource: #if we're looking to draw or give via a specific resource, check for that
            if hasattr(obj,'installed'):
                if not obj.installed: return False
                if not obj.installed.station: return False
                if not obj.installed.station.resources == self.required_resource: return False
                
        if isinstance(self.target, str): #TODO pull this out into a separate EquipmentFilter, a la ClutterFilter
            if self.target == 'Storage' and isinstance( obj, Storage):
                #print self.storage_filter, obj.filter.target
                return self.storage_filter in obj.filter.target or self.storage_filter == 'Any'
            elif self.target in self.equipment_targets: 
                return isinstance( obj, self.equipment_targets [ self.target ] )    
            elif self.target == 'Equipment Slot':
                return obj == self.storage_filter              
            #print self.target                 
            #return clutter.equals(self.target, obj.name) #must be clutter
        elif isinstance(self.target, ClutterFilter):
            if self.check_storage and isinstance( obj, Storage ):
                return obj.stowage.find_resource(self.target.compare)
            return self.target.compare(obj) 
        elif isinstance(self.target, NeedFilter):            
            return self.target.compare(obj)         
        else:
            return obj is self.target
        return False
