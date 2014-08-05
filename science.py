import random
from equipment_science import Experiment


class SciencePath(object):
    def __init__(self,name='Physics'):
        self.name = name
        self.level = {'Knowledge':1, 'Engineering':1, 'Production':1}
        self.progress = {'Knowledge':0, 'Engineering':0, 'Production':0}
        ''' Different types of research needed to produce products:
        Knowledge: theoretical ideas of how tech can work.  Increased with experiments.
        Engineering: prototypes of tech working.  Expensive as hell one-offs.  Increased with prototypes.
        Production: tech can be used freely with no increase in cost.  Increased with background production. '''
        
        
      
    def add_progress(self, prog_type='Knowledge', prog_level=1, prog_amt = 0):
        if prog_type == 'Production' and self.level['Production'] >= self.level['Engineering']: return
        if prog_type == 'Engineering' and self.level['Engineering'] >= self.level['Knowledge']: return
        self.progress[prog_type] += max(0,pow(prog_amt,(prog_level-self.level[prog_type] + 1))) #allows for "alien artifact" tech boosts, slow grindy progress
        if self.progress[prog_type] > 1000: #if the "artifact" was hugely advanced, allow for multiple boosts
            self.level[prog_type] += 2
            self.progress[prog_type] = 0
        elif self.progress[prog_type] > 100:
            self.level[prog_type] += 1
            self.progress[prog_type] = 0
        #TODO trickle higher-level knowledge into lower-level later types
            
class Science(object):
    #for SCIENCE!
    def __init__(self, init_years=10):
        self.field = dict()
        
        #TODO move science into json folder
        #'pure' sciences - not used for much atm, aside from experiment filler
        self.field['Physics'] = SciencePath('Physics')
        self.field['Biology'] = SciencePath('Biology')
        self.field['Astronomy'] = SciencePath('Astronomy')
        
        #'applied' sciences - used for equipment/stuff requirements
        self.field['Medicine'] = SciencePath('Medicine')        
        self.field['Materials'] = SciencePath('Materials')
        self.field['Electronics'] = SciencePath('Electronics')
        self.field['Thermodynamics'] = SciencePath('Thermodynamics')
        self.field['Software'] = SciencePath('Software')

        self.last_update=0                                
                
        for i in range(init_years):
            self.yearly_update()
        
    def yearly_update(self,dt = 3600*24*365):
        for f in self.field.values():
            for t in f.level.keys():
                f.add_progress(prog_type=t,prog_level=f.level[t],prog_amt = 40*random.random()*random.random())
                
    def status_update(self):
        for f in self.field.keys():
            print f+" "+str(self.field[f].level['Knowledge'])+"-"+str(self.field[f].level['Engineering'])+"-"+str(self.field[f].level['Production'])
            
    def process_experiment(self,item):
        if not item.no_more_SCIENCE: return
        
        points = 20 #Tier 1 journal
        if random.random() > 0.05:
            if random.random() > 0.3:
                points = 2 #Tier 3 journal
            else:
                points = 5 #Tier 2 journal
        
        self.field[item.field].add_progress('Knowledge',item.level,points*random.random())
            
                
                
if __name__ == '__main__':
    science = Science()
    for i in range(40):
        science.yearly_update()
        science.status_update()
