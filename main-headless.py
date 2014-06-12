import util
import logging
from scenario import ScenarioMaster

def load_image(filename, anchor_x=None, anchor_y=None):    
    return None
    
util.load_image = load_image    

def load_sprite(filename, anchor_x=None, anchor_y=None):
    return None
    
util.load_sprite = load_sprite
                                      
if __name__ == "__main__":
    from time import sleep     

    logger=logging.getLogger("Universe")
    logger.setLevel(logging.DEBUG)
    #DEBUG INFO WARNING ERROR CRITICAL
    #create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    #create formatter
    formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
    #add formatter to ch
    ch.setFormatter(formatter)
    #add ch to logger
    logger.addHandler(ch)

    scenario = ScenarioMaster(scenario='DOCKINGTEST',logger=logger)
            
    for i in range(1,10000):
        scenario.system_tick(1/20.0)
        scenario.status_update(1/20.0)
        sleep(1/20.0)
        
