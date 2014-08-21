import pyglet
import kytten
import os
from clutter import Clutter
from equipment.general import *
from equipment.science import *
from equipment.lifesupport import *
from equipment.workshop import *
import math

# Default theme, blue-colored
blue_theme = kytten.Theme(os.path.join(os.getcwd(), 'theme'), override={
    "gui_color": [64, 128, 255, 255],
    "font_size": 12
})

# Callback functions for dialogs which may be of interest
def on_escape(dialog):
    dialog.teardown()

def color(color='DEFAULT'):
    if color=='red':
        c = [255, 128, 128, 255]
    elif color=='green':
        c = [128, 255, 128, 255]
    else:
        c = [255, 255, 255, 255]
    return c

class gui():
    '''gui layer for game interaction'''
    def __init__(self,window=None):
        self.scenario = None
        self.window = window
        self.user_selected = None
        self.batch = pyglet.graphics.Batch()
        #bg_group = pyglet.graphics.OrderedGroup(0)
        self.fg_group = pyglet.graphics.OrderedGroup(1)          
        
    def on_mouse_press(self, x, y, button, modifiers):
        x -= self.window.width//2
        y -= self.window.height//2
        for station in self.scenario.get_stations():
            for a in station.actors.values():
                if a.sprite.contains(x,y):
                    self.create_actor_dialog(a)
                    return True
            for m in station.modules.values():
                if m.sprite.contains(x,y):
                    for e in m.equipment.keys():
                        if m.equipment[e][3] and m.equipment[e][3].sprite.contains(x,y):
                            self.create_equipment_dialog(m,e)
                            return True
                    for c in m.stowage.contents:
                        if c.sprite.contains(x,y):
                            self.create_clutter_dialog(m,c)
                            
                            return True
                    self.create_module_dialog(m)
                    return True
        print 'Mouse pressed at: ',(x,y)
        return False     
        
    def on_mouse_motion_skip(self, x, y, dx,dy):
        x -= self.window.width//2
        y -= self.window.height//2
        for station in self.scenario.get_stations():
            for m in station.modules.values():
                if m.sprite.contains(x,y):
                    print 'Module',m.short_id
                    return True
        print 'Mouse pressed at: ',(x,y)
        return False         
    
    def on_draw2(self):    
        #self.window.dispatch_event('on_update', .05)    
        self.batch.draw()
        
    def create_options_menu(self):        
        def on_cancel():
            print "Form canceled."
            on_escape(dialog) 
         
            
        def on_set(value):
	        gv.config['TIME FACTOR'] = 24 * value * value
            
                                                         
        entries=[]
        entries.append(kytten.Label("Game Options"))
        entries.append(kytten.Label("Simulation speed:"))
        entries.append(kytten.Label("24<-     ->2400"))
        entries.append(kytten.Slider( math.sqrt(gv.config['TIME FACTOR']/24.0), 1, 10, steps=15, on_set=on_set))
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=250, height=450)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_CENTER,
	    theme=blue_theme, on_escape=on_escape)      
        
    def create_escape_menu(self):        
        def on_cancel():
            print "Form canceled."
            on_escape(dialog) 
         
        def on_just_quit():
            print "Quitting."
            self.window.close()             
            
        def on_save_and_quit():
            print "Saving."
            util.autosave()
            on_just_quit()     
                                                         
        entries=[]
        entries.append(kytten.Button("Options", on_click=self.create_options_menu))
        entries.append(kytten.Button("Return to game", on_click=on_cancel))
        entries.append(kytten.Button("Save and Quit", on_click=on_save_and_quit))
        entries.append(kytten.Button("Just Quit", on_click=on_just_quit))        
                            
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=250, height=450)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_CENTER,
	    theme=blue_theme, on_escape=on_escape)    
        
        
    def create_manifest_dialog(self, module=None):
        if module is None: return
        dialog = None
        
        def on_pass(choice):
            pass
            
        
        action = kytten.Dropdown(['Load','Unload'],on_select=on_pass)
        amount = kytten.Dropdown(['All','Some'],on_select=on_pass) 
        
        subtype = kytten.Dropdown(['ERROR'],on_select=on_pass)        
        gui=self
        
            
        def on_type(choice):
            if choice == 'Clutter':
                subtype.options=['Any','Water','Food', 'Solid Waste']
            elif choice == 'Equipment':
                subtype.options=['Any','Dead Science', 'Live Science']
            elif choice == 'Actors':
                subtype.options=['All']
                subtype.options.extend([ a.name for a in module.station.actors.values()])
            subtype.selected=subtype.options[0]
        
        itemtype = kytten.Dropdown(['Clutter','Equipment','Actors'],on_select=on_type)
        on_type('Clutter')
        
        def on_cancel():
            print "Form canceled."
            on_escape(dialog)
        
        def wipe_manifest():
            module.manifest = None
            print "Manifest wiped."
            on_escape(dialog)
            gui.create_manifest_dialog(module)
        
        class DeleteItem():
            def __init__(self,item,module,gui):
                self.item_to_delete = item
                self.module = module
                self.gui=gui
                
            def delete_item(self):
                if self.item_to_delete and module.manifest:
                    for i in module.manifest.item:
                        if i is self.item_to_delete:
                            i.cancel()
                            module.manifest.item.remove(i)
                            on_escape(dialog)
                            self.gui.create_manifest_dialog(self.module)
                            return
                                                                
        def new_item():
            print "New item to add:",action.selected,amount.selected,itemtype.selected,subtype.selected
            if not module.manifest:
                module.new_manifest()
            module.manifest.new_item(tasktype=action.selected, taskamt = amount.selected, 
                                     itemtype = itemtype.selected, subtype = subtype.selected)
                                     
            on_escape(dialog)
            gui.create_manifest_dialog(module)                                    
		
        entries=[kytten.Label("Manifest for "+module.short_id)]
        if module.manifest:
            for i in module.manifest.item:
                color = 'color (128, 255, 128, 255)' if i.check_satisfaction() else 'color (255, 128, 128, 255)'
                manentry = pyglet.text.decode_attributed(''.join(["  {bold True}{",color,"}",i.tasktype,' ',i.taskamt,' ',i.itemtype,' ',i.subtype,"{color (255, 255, 255, 255}{bold False}"]))
                entries.append( kytten.HorizontalLayout( [ kytten.Document( manentry, width=200 ) , kytten.Button( "X" , on_click = DeleteItem( i , module, self).delete_item ) ] ) )                                                                 
            entries.append(kytten.FoldingSection("Delete manifest", kytten.Button("Are you sure?", on_click=wipe_manifest), is_open=False ) )
            
        entries.append(kytten.FoldingSection("New manifest item:", 
                    kytten.VerticalLayout ( [ kytten.HorizontalLayout( [ action , amount, itemtype , subtype ] ),
                    kytten.Button("Add item!", on_click=new_item) ] ) , is_open=False))  
                                      
        entries.append(kytten.Button("Close", on_click=on_cancel))            
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=250, height=450)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_TOP_RIGHT,
	    theme=blue_theme, on_escape=on_escape)
	    
        
    def clutter_entries(self,stowage):
        contentEntries = [kytten.Label("Free space: "+'{:.2f}'.format(stowage.free_space)+' m3')]
        if stowage.contents:
            contentEntries.append(kytten.Label("Stored:"))
            for c in stowage.contents:       
                if isinstance(c,Clutter):
                    contentEntries.append(kytten.Label('  '+c.name+': {:.2f}'.format(c.mass)+" kg"))
                    '''contentEntries.append(kytten.Label("    Misc Qualities:"))
                    for q in c.quality.keys():
                        contentEntries.append(kytten.Label("    "+q+" "+'{:.2f}'.format(c.quality[q])))'''
                elif isinstance(c,Equipment):
                    contentEntries.append(kytten.Label('  '+c.name))    
        return contentEntries
        
    def atmo_entries(self,atmo):
        entries=[kytten.Label('Total pressure: '+'{:.2f}'.format(atmo.pressure)+' kPa')]        
        for c in atmo.composition.keys():
            if atmo.composition[c] > 0:
                entries.append(kytten.Label(''.join(['  ',c,': ','{:.2f}'.format(atmo.partial_pressure(c)),' kPa']))) 
        return entries   
        
    def create_module_dialog(self, module=None):
        if module is None: return
        def on_cancel():
            print "Form canceled."
            on_escape(dialog)
            
        def on_manifest():
            self.create_manifest_dialog(module)
            #on_escape(dialog)        
            
        def quick_install_all():
            for c in module.stowage.contents:
                if isinstance(c, Equipment):
                    c.install_task(module.station)
           
        def install_checked(*args):
            module.player_installable = not module.player_installable   
        
        optionEntries = []
        optionEntries.append(kytten.Button("Install Equip",on_click = quick_install_all))
        optionEntries.append(kytten.Button("Cargo Manifest", on_click=on_manifest))
        optionEntries.append( kytten.Checkbox("Permit installation", is_checked = module.player_installable, on_click=install_checked) )
                
        contentEntries = []        
        contentEntries.append(kytten.Label("Installed equipment:"))
        for e in module.equipment.values():
            if e[3]:
                contentEntries.append(kytten.Label('  '+e[3].name))  
                       
        contentEntries.append(kytten.Label("Loose stowage:"))
        contentEntries.extend(self.clutter_entries(module.stowage))
                                                       
        entries=[kytten.Label("Module: "+module.short_id)]
        entries.append(kytten.Label("Atmospherics:"))
        entries.extend(self.atmo_entries(module.atmo))
        
        entries.append(kytten.FoldingSection("Options:",
            kytten.VerticalLayout(optionEntries), is_open=False))
        
        entries.append(kytten.FoldingSection("Contents:",
            kytten.VerticalLayout(contentEntries), is_open=False))
        
        
        entries.append(kytten.Button("Close", on_click=on_cancel))                    
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=250, height=450)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_TOP_RIGHT,
	    theme=blue_theme, on_escape=on_escape)
	    
	    
	    
	def create_workshop_dialog(self,module=None, equip=None):
	    if module is None or equip is None: return
	    entries=[kytten.Label("Workshop menu")]
	    
	    #if isinstance(e,WorkbenchRack):
        #    entries.append(kytten.Button("", on_click=on_miss_ctrl))
        
	    
	    dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=200, height=450)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_TOP_RIGHT,
	    theme=blue_theme, on_escape=on_escape)
	    
	    
	    
    def create_equipment_dialog(self, module=None, equip_name=''):
        if module is None or not equip_name: return

        e = module.equipment[equip_name][3]

        def on_cancel():
            print "Form canceled."
            on_escape(dialog)
            
        def refresh():
            self.create_equipment_dialog(module, equip_name)
            on_escape(dialog)    
            
        def on_miss_ctrl():
            print "Contacting Mission Control!"
            on_escape(dialog)    
            e.spawn_mc_task()
            #self.create_mission_control_dialog()
            
        def uninstall():    
            e.uninstall_task()
            on_escape(dialog)            
                
        entries=[kytten.Label("Equipment: " + equip_name)]
        if isinstance(e,Machinery):
            entries.append(kytten.Label("Last maint (hrs):"+'{:3.0f}'.format( e.operating_time_since_last_maintenance/3600.0 ) ) )
            entries.append(kytten.Label("Wear:"+'{:0.2f}'.format( e.wear ) ) )
        if isinstance(e,Comms):
            entries.append(kytten.Button("Contact NASA", on_click=on_miss_ctrl))
        if isinstance(e,Storage):
            entries.extend(self.clutter_entries(e.stowage)) 
            entries.append(kytten.Button("Dump", on_click=lambda: e.dump_task()))
        if hasattr(e,'tank'):
            entries.extend(self.clutter_entries(e.tank))   
        if isinstance(e,Experiment):
            entries.append(kytten.Label( e.field+'{:2.0f}'.format(e.level) ) )
            entries.append(kytten.Label("Science usage: " + '{:3.2f}'.format(100*e.science_percentage())+'%' )) 
        if isinstance(e,RegenerableCO2Filter):            
            entries.append(kytten.Label("Current CO2 level: "+'{:3.2f}'.format( e.last_co2_reading ), color=color('green' if e.last_co2_reading < 1.0 else 'red' ) ) ) 
        if isinstance(e,Battery):
            if e.avg_charge > 0:
                entries.append(kytten.Label('Charging: '+'{:3.2f}'.format( e.avg_charge ) +' kW', color=color('green') ) )                
            elif e.avg_charge < 0:
                entries.append(kytten.Label('Disharging: '+'{:3.2f}'.format( e.avg_charge ) +' kW', color=color('red') ) )
            entries.append(kytten.Label( '({:3.2f} kW max)'.format( module.station.resources.resources['Electricity'].previously_available ) ) )                                
            entries.append(kytten.Label('Available: '+'{:3.2f}'.format( e.charge ) +' kWh') )            
        if isinstance(e,DockingRing):           
            def dockbutton(*args):
                e.toggle_player_usable()
            check = kytten.Checkbox("Permitted", is_checked = e.player_usable, on_click=dockbutton, disabled = (e.docked==True))
            entries.append( check )
        if not e.in_vaccuum: entries.append(kytten.Button("Uninstall", on_click=uninstall))
        entries.append(kytten.Button("Close", on_click=on_cancel))    
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=200, height=450)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_TOP_RIGHT,
	    theme=blue_theme, on_escape=on_escape)	    
	    
	    
    def create_clutter_dialog(self, module = None, clutter = None):
        if module is None or clutter is None: return

        c=clutter

        def on_cancel():
            print "Form canceled."
            on_escape(dialog)            
            
        def install():    
            if hasattr(c,'install_task'): c.install_task(module.station)
            on_escape(dialog)            
                
        entries=[kytten.Label("Clutter: " + c.name)]
        entries.append(kytten.Label("Mass: " + '{:0.2f}'.format(c.mass)+ ' kg') )
        entries.append(kytten.Label("Volume: "+'{:0.2f}'.format(c.volume)+ ' m3') )        
        if isinstance(c,Equipment):
            entries.append(kytten.Button("Install", on_click=install))
        elif hasattr(c,'quality') and c.quality:
            entries.append(kytten.Label("Misc Qualities:"))
            for q in c.quality.keys():
                entries.append(kytten.Label("  "+q+" "+str(c.quality[q])))
        entries.append(kytten.Button("Close", on_click=on_cancel))    
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=200, height=150)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_TOP_RIGHT,
	    theme=blue_theme, on_escape=on_escape)    
	    
    def create_actor_dialog(self, actor = None):
        if actor is None: return

        a=actor
        
        taskLabel = kytten.Label( '' )
        def refresh_task(dt=0):
            taskLabel.set_text('Task:'+ a.task.name if a.task else 'Idling')
        refresh_task()
        
        pyglet.clock.schedule_interval(refresh_task,1)

        def on_cancel():
            print "Form canceled."
            on_escape(dialog)                                           
        
        needEntries=[]
        for n in a.needs.keys():
            needEntries.append(kytten.Label(a.needs[n].name+" "+a.needs[n].current_severity()))
                
        entries=[kytten.Label(a.name)]
        entries.append(kytten.FoldingSection("Needs:",
            kytten.VerticalLayout(needEntries), is_open=False))
        entries.append(taskLabel)
        entries.append(kytten.Button("Close", on_click=on_cancel))    
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=300, height=250)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_TOP_RIGHT,
	    theme=blue_theme, on_escape=on_escape)    
	    
	    
    def create_resupply_mission_dialog(self,inventory=[]):    
        mass = [0]
        mass_label = kytten.Label('Current mass: ERR' )
        cost = [0]
        cost_label = kytten.Label('Current cost: ERR' )
        
        def compute_mass_cost():
            mass[0]=0
            cost[0]=0                
            for i in inventory:
                if isinstance(i,Equipment) or isinstance(i,Clutter):
                    mass[0] += i.mass
                    cost[0] += 1                            
                    
        def refresh():
            #global mass, cost
            compute_mass_cost()            
            cost_label.set_text( 'Current cost: {:0.2f}'.format(cost[0]))
            mass_label.set_text( 'Current mass: {:0.2f}'.format(mass[0]))
                    
        refresh()
                    
        def inv_search(_id):
            for i in inventory: #TODO likely a subtyping bug here
                if isinstance(i,util.equipment_targets[_id]):
                    return i
            return None
                
        def add_inv(_id,add):
            i = inv_search(_id)
            if add:
                if i is None: inventory.append(util.equipment_targets[_id]())
            else:
                if i: inventory.remove(i)
            refresh()
            
        def send_mission():
            print 'Sending!', inventory
                
        mc=self.scenario.current_scenario.mission_control
        equip_list = mc.get_available_equipment()
        
        entries=[]
        
        entries.append(cost_label)
        entries.append(mass_label)
        entries.append( kytten.Label('--Equipment--') )
        for e in equip_list:
            inst = util.equipment_targets[e]()
            entries.append( kytten.Checkbox( inst.name, id=e, is_checked = inv_search(e), on_click=add_inv ) )
        
        entries.append(kytten.Button("Send Resupply", on_click=send_mission))
        
    
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=250, height=350)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_CENTER,
	    theme=blue_theme, on_escape=on_escape)
	    
    def create_mission_control_dialog(self):          
    
        class GUIMission():
            def __init__(self,name,cost):
                self.name=name
                self.cost=cost
                
            def action(self):
                pass                
          
        def on_cancel():
            print "Form canceled."
            on_escape(dialog)                
        
        funds=self.scenario.current_scenario.mission_control.player_nasa_funds     
        fundsLabel = kytten.Label('Funds: '+'{:0.2f}'.format(funds))  
        
        def refresh_funds(dt):
            funds=self.scenario.current_scenario.mission_control.player_nasa_funds 
            fundsLabel.set_text('Funds: '+'{:0.2f}'.format(funds))
                
        pyglet.clock.schedule_interval(refresh_funds,5)        
                
        missions = self.scenario.current_scenario.mission_control.get_available_missions()     
        missiondrop = kytten.Dropdown(sorted([k if funds > missions[k][0] else "-"+k for k in missions.keys() ],key=lambda x:missions[x][1]),on_select=None)
            
        def resupply_dialog():
            self.create_resupply_mission_dialog()
            on_escape(dialog)
            
        def send_mission():
            mission = missiondrop.selected                
            missions[mission][1]()
            on_escape(dialog)                    
                        
        entries=[kytten.Label("Mission Control")]
        entries.append(fundsLabel)
        
        entries.append(kytten.FoldingSection("Request new module",kytten.VerticalLayout([missiondrop,kytten.Button("Send!", on_click=send_mission, disabled=not self.scenario.current_scenario.mission_control.module_available)]),is_open = False))
        entries.append(kytten.Button("Request resupply", on_click=resupply_dialog))
        
        entries.append(kytten.Button("Close", on_click=on_cancel))
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout(entries, align=kytten.HALIGN_LEFT),
	        width=250, height=350)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_TOP_RIGHT,
	    theme=blue_theme, on_escape=on_escape)		    



        
