import pyglet
import kytten
import os
from clutter import Clutter
from equipment import *
from equipment_science import *

# Default theme, blue-colored
blue_theme = kytten.Theme(os.path.join(os.getcwd(), 'theme'), override={
    "gui_color": [64, 128, 255, 255],
    "font_size": 12
})

# Callback functions for dialogs which may be of interest
def on_escape(dialog):
    dialog.teardown()

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
        
        
    def create_manifest_dialog(self, module=None):
        if module is None: return
        dialog = None
        
        def on_pass(choice):
            pass
        
        action = kytten.Dropdown(['Load','Unload'],on_select=on_pass)
        amount = kytten.Dropdown(['All','Some'],on_select=on_pass) 
        itemtype = kytten.Dropdown(['Clutter','Equipment'],on_select=on_pass)
        subtype = kytten.Dropdown(['Any','Water','Food', 'Solid Waste', 'Dead Science', 'Live Science'],on_select=on_pass)        
        gui=self
        
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
        contentEntries.append(kytten.Label("Stored clutter:"))
        for c in stowage.contents:       
            if isinstance(c,Clutter):
                contentEntries.append(kytten.Label('  '+c.name+': '+str(c.mass)+" kg"))
            elif isinstance(c,Equipment):
                contentEntries.append(kytten.Label('  '+c.name))    
        return contentEntries        
        
    def create_module_dialog(self, module=None):
        if module is None: return
        def on_cancel():
            print "Form canceled."
            on_escape(dialog)
            
        def on_manifest():
            self.create_manifest_dialog(module)
            #on_escape(dialog)        
                
        contentEntries = []
        contentEntries.append(kytten.Label("Installed equipment:"))
        for e in module.equipment.values():
            if e[3]:
                contentEntries.append(kytten.Label('  '+e[3].name))  
                      
        contentEntries.extend(self.clutter_entries(module.stowage))                
                
        entries=[kytten.Label("Module: "+module.short_id)]
        entries.append(kytten.Button("Manifest", on_click=on_manifest))
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
	    
	    
	    
    def create_equipment_dialog(self, module=None, equip_name=''):
        if module is None or not equip_name: return

        e = module.equipment[equip_name][3]

        def on_cancel():
            print "Form canceled."
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
        if isinstance(e,Comms):
            entries.append(kytten.Button("Contact NASA", on_click=on_miss_ctrl))
        if isinstance(e,Storage):
            entries.extend(self.clutter_entries(e.stowage))    
        if isinstance(e,Experiment):
            entries.append(kytten.Label("Science usage: " + '{:3.0f}'.format(100*e.science_percentage()) ))            
        entries.append(kytten.Button("Uninstall", on_click=uninstall))
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
        if isinstance(c,Equipment):
            entries.append(kytten.Button("Install", on_click=install))
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
        
        resupmiss = GUIMission("Resupply Mission (50M)",50000000)
        astromiss = GUIMission("Recruit Astronauts(3) (100M)",100000000)
        destmiss = GUIMission("Add Destiny Module (200M)",200000000)
                
        missions = [] 
        for r in [resupmiss,astromiss]:
            missions.append(r.name if funds > r.cost else '-'+r.name)       

        missiondrop = kytten.Dropdown(missions,on_select=None)
            
        def send_mission():
            mission = missiondrop.selected    
            if mission == resupmiss.name:
                print "sending resupply mission"    
                self.scenario.current_scenario.mission_control.send_resupply_vessel()
            elif mission == astromiss.name:
                print "Send astronaut replacements"
            elif mission == destmiss.name:
                print "Send destiny module"
            on_escape(dialog)
            
        


            
        entries=[kytten.Label("Mission Control")]
        entries.append(kytten.Label('Funds: '+'{:0.2f}'.format(self.scenario.current_scenario.mission_control.player_nasa_funds)))
        
        entries.append(kytten.FoldingSection("Request new mission",kytten.VerticalLayout([missiondrop,kytten.Button("Send!", on_click=send_mission)]),is_open = False))
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



        
