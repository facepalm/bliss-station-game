import manifest
import util

from cargo_modules import DragonCargoModule

class Mission(object):
    def __init__(self,selection=None):
        self.load_mission(selection)  
        self.objectives = dict()
        self.num_objectives = 0          

    def load_mission(self,selection=None, **kwargs):
        if not selection: return
        if selection == 'Standard Resupply' and 'target_id' in kwargs:
            self.current_mission = selection
            
            dockObj=Objective(name='Dock Vessel',description='Dock vessel to station',order='DOCK '+kwargs['target_id']+'  ')
            self.add_objective(dockObj)  
            
            berthObj=Objective(name='Join Vessel',description='Join vessel to station',order='JOIN '+kwargs['target_id']+'  ',requires=dockObj)     
            self.add_objective(berthObj)    
            
            undock_mod_id = kwargs['module_id'] if 'module_id' in kwargs else ''
            manObj = Objective(name='Resupply Manifest',order='MANIFEST MODULE '+undock_mod_id+' RESUPPLY',requires=berthObj)
            self.add_objective(manObj)
            
            undock_dock_id = kwargs['dock_id'] if 'dock_id' in kwargs else ''            
            unberthObj=Objective(name='Split Vessel',order='SPLIT '+undock_dock_id+' ',requires=berthObj)
            self.add_objective(unberthObj)
            
            sendoffObj = Objective(name='Undock Vessel',order='SENDOFF '+undock_mod_id+' ',requires=unberthObj)
            self.add_objective(sendoffObj)               
            
            self.add_objective(Objective(name='Contact Mission Control',order='DEORBIT '+undock_mod_id+' ',requires=sendoffObj)) 
            
        elif selection == 'New Module' and 'target_id' in kwargs and 'module_id' in kwargs:
            self.current_mission = selection
            
            dockObj=Objective(name='Dock Vessel',description='Dock vessel to station',order='DOCK '+kwargs['target_id']+'  ')
            self.add_objective(dockObj)  
            
            berthObj=Objective(name='Join Vessel',description='Join vessel to station',order='JOIN '+kwargs['target_id']+'  ',requires=dockObj)     
            self.add_objective(berthObj)    
            
            undock_mod_id = kwargs['module_id'] if 'module_id' in kwargs else ''
            manObj = Objective(name='Resupply Manifest',order='MANIFEST MODULE '+undock_mod_id+' RESUPPLY',requires=berthObj)
            self.add_objective(manObj)
            
            unberthObj=Objective(name='Split Vessel',order='SPLIT '+undock_mod_id+' ',requires=berthObj)
            self.add_objective(unberthObj)
            
            sendoffObj = Objective(name='Undock Vessel',order='SENDOFF '+undock_mod_id+' ',requires=unberthObj)
            self.add_objective(sendoffObj)               
            
            self.add_objective(Objective(name='Contact Mission Control',order='DEORBIT '+undock_mod_id+' ',requires=sendoffObj)) 
        
        
    def update_mission(self,scenario):
        if self.current_mission == "Standard Resupply":
            pass
            
    def add_objective(self,obj):
        if not obj: return
        obj.mission = self
        self.num_objectives += 1
        self.objectives['{:02}'.format(self.num_objectives)+'- '+obj.name]=obj    
        
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
        if not scenario: scenario = util.scenario
        #if not station: return
        if self.completed: return
        order_token = self.order.split(' ')
        if order_token[0] == 'DOCK': 
            if not hasattr(self.mission,'dock'):
                if not scenario or not station: return
                if not order_token[1] in scenario.stations.keys(): station.logger.warning("Requested docking to a station which doesn't exist!")
                docking_station = scenario.stations[order_token[1]]
                [mod, dock] = docking_station.get_random_dock()
                if not dock: 
                    station.logger.warning("Docking mission: no valid docking points available!")
                    return
                self.mission.module = mod
                self.mission.dock = mod.equipment[dock][3]
                station.begin_docking_approach(mod,dock)
            elif self.mission.dock.open:
                self.completed=True
        elif order_token[0] == 'JOIN':
            if not order_token[1] in scenario.stations.keys(): station.logger.warning("Requested berth to a station which doesn't exist!")
            docking_station = scenario.stations[order_token[1]]
            self.mission.modules = docking_station.modules.values()
            
            dock_station = scenario.stations[order_token[2]] if order_token[2] in scenario.stations.keys() else station
            dock_station.join_station(docking_station)            
            
            self.completed=True
        elif order_token[0] == 'MANIFEST':
            modules=[]
            if order_token[1] == 'MODULE':
                if not order_token[2]:
                    if hasattr(self.mission,'module') and self.mission.module: modules.append(self.mission.module)
                    if hasattr(self.mission,'modules'): modules.extend(self.mission.modules)
                else:
                    modules.append(scenario.modules[order_token[2]])                    
            else:  
                if not order_token[2] in scenario.stations.keys(): station.logger.warning("Requested manifest to a station which doesn't exist!")
                station = scenario.stations[order_token[2]]
                modules.extend(station.modules.values())
            if order_token[3] and order_token[3] == 'RESUPPLY':    
                for module in modules:    
                    module.manifest = manifest.Manifest(module)
                    module.manifest.new_item(tasktype='Unload', taskamt = 'All', itemtype = 'Clutter', subtype = 'Any')
                    module.manifest.new_item(tasktype='Unload', taskamt = 'All', itemtype = 'Equipment', subtype = 'Any')
                    module.manifest.new_item(tasktype='Load', taskamt = 'All', itemtype = 'Clutter', subtype = 'Solid Waste')   
            self.completed=True                    
        elif order_token[0] == 'SPLIT':
            #if not order_token[1] in scenario.modules.keys(): station.logger.warning("Requested split station from a nonexistent module!")
            if order_token[1] in scenario.modules.keys():
                mod = scenario.modules[order_token[1]]                
                splitdock = mod.equipment[mod.get_random_dock(used=True, unused=False)][3]
                #print "New mod is Dragon: ",isinstance(mod,DragonCargoModule), mod.id
            else:
                splitdock = self.mission.dock if self.mission.dock else None
            self.mission.split_dock = splitdock
            if not splitdock: 
                station.logger.warning("Split dock does not exist!")
            self.mission.foreign_station = station.split_station(splitdock)
            if self.mission.foreign_station:
                self.completed=True            
        elif order_token[0] == 'SENDOFF':
            splitdock = self.mission.split_dock if self.mission.split_dock else None
            if splitdock.installed.station.position == 'Approach':
                self.completed = True            
            else:
                result = station.begin_undocking_approach(splitdock.installed,splitdock.get_name())            
        elif order_token[0] == 'DEORBIT':            
            scenario.mission_control.accept_vessel(self.mission.foreign_station)
            self.completed = True
            
            
            
