import pyglet
import kytten
import os
from equipment import *

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
        
    def create_module_dialog(self, module=None):
        if module is None: return
        def on_cancel():
            print "Form canceled."
            on_escape(dialog)
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout([
                kytten.Label("Module: "+module.short_id),                
				kytten.Button("Close", on_click=on_cancel),
		    ], align=kytten.HALIGN_LEFT),
	        width=200, height=150)
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
                
        entries=[kytten.Label("Equipment: " + equip_name)]
        if isinstance(e,Comms):
            entries.append(kytten.Button("Phone Home", on_click=on_miss_ctrl))
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
        def on_cancel():
            print "Form canceled."
            on_escape(dialog)
            
        dialog = kytten.Dialog(
        kytten.Frame(
            kytten.Scrollable(
            kytten.VerticalLayout([
                kytten.Label("Mission Control Dialog:"),                
				kytten.Button("Close", on_click=on_cancel),
		    ], align=kytten.HALIGN_LEFT),
	        width=200, height=150)
	    ),
	    window=self.window, batch=self.batch, group=self.fg_group,
	    anchor=kytten.ANCHOR_TOP_RIGHT,
	    theme=blue_theme, on_escape=on_escape)		    



        
