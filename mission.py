

class Mission(object):
    def __init__(self,selection=None):
        self.load_mission(selection)  
        self.objectives = dict()
        self.num_objectives = 0          

    def load_mission(self,selection=None, **kwargs):
        if not selection: return
        if selection == 'Standard Resupply' and 'target_id' in kwargs:
            self.current_mission = selection
            dockObj=Objective(name='Dock Vessel',description='Dock vessel to station',order='DOCK '+kwargs['target_id']+'  station')
            self.add_objective(dockObj)  
            berthObj=Objective(name='Berth Vessel',description='Dock vessel to station',order='BERTH '+kwargs['target_id']+'  station',requires=dockObj)     
            self.add_objective(berthObj)    
            self.add_objective(Objective(name='Resupply Manifest',order='MANIFEST '+kwargs['target_id']+' RESUPPLY'))
            unberthObj=Objective(name='Unberth Vessel',order='UNBERTH '+kwargs['target_id'],requires=berthObj)
            self.add_objective(unberthObj)
            sendoffObj = Objective(name='Send off Vessel',order='SENDOFF '+kwargs['target_id'],requires=unberthObj)
            self.add_objective(sendoffObj)               
            self.add_objective(Objective(name='Contact Mission Control',order='DEORBIT '+kwargs['target_id'],requires=sendoffObj)) 
        
    def update_mission(self,scenario):
        if self.current_mission == "Standard Resupply":
            pass
            
    def add_objective(self,obj):
        if not obj: return
        self.num_objectives += 1
        self.objectives['{02- }'.format(self.num_objectives)+obj.name]=obj    
        
    def current_objective(self):
        open_obj = [o for o in self.objectives.keys() if not self.objectives[o].completed and (not self.objectives[o].requires or self.objectives[o].requires.completed)]
        if not open_obj: return None
        return self.objectives[sorted(open_obj)[0]]
            
class Objective(object):
    def __init__(self,name='Spawn Dragon capsule', description = '', order = 'SpawnModule DragonResupply TROGDOR', **kwargs):
        self.name = name
        self.desc = description                     
        self.order = order
        self.completed = False
        self.requires = kwargs['requires'] if 'requires' in kwargs else None
        
    def carry_out(self,station=None, scenario=None):
        #if not station: return
        order_token = self.order.split(' ')
        if order_token[0] == 'DOCK': 
            if not scenario or not station: return
            if not order_token[1] in scenario.stations.keys(): station.logger.warning("Requested docking to a station which doesn't exist!")
            docking_station = scenario.stations[order_token[1]]
            [mod, dock] = docking_station.get_random_dock()
            station.begin_docking_approach(mod,dock)
            
            self.completed=True
        elif order_token[0] == 'BERTH':
            self.completed=True #TODO actually do
        elif order_token[0] == 'MANIFEST':
            pass                
        
        
