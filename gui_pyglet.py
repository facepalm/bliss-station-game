import pyglet
import kytten
import os

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
        print self.window, self.batch, self.fg_group
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
	    anchor=kytten.ANCHOR_CENTER,
	    theme=blue_theme, on_escape=on_escape)



        
