
from equipment import Equipment, Machinery, Rack
import clutter
import util
import atmospherics
from filtering import Searcher
     
class MysteryBoxRack(Rack):
    '''Mysterious box of boxy mystery.  Dare you enter its magical realm?'''
    
    def __init__(self):
        super(MysteryBoxRack, self).__init__()         
        
    def update(self,dt):
        super(MysteryBoxRack, self).update(dt)        
        if self.installed and not self.task or self.task.task_ended():
            #work on the box    
            self.task = Task(''.join(['Stare at Mystery Box']), owner = self, timeout=86400, task_duration = 86400, severity='LOW', fetch_location_method=Searcher(self,self.installed.station).search )
            self.installed.station.tasks.add_task(self.task)
