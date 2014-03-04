import logging

TIME_FACTOR = 24 # 120# 24

ZOOM=6

equipment_targets = dict()

GRAPHICS = None

def quad_mean(x,y,wx=1,wy=1):
    return pow( (1.0*wx*x*x + wy*y*y)/(wx + wy) ,0.5)
    
def seconds(time=1,units='minutes'):
    return time*60 if units == 'minutes' or units == 'minute' \
                                         else time*3600 if units == 'hours' or units == 'hour' \
                                         else time*86400 if units=='days' or units == 'day' \
                                         else time*2592000 if units=='months' or units == 'month' \
                                         else 10    
                                         
                                         
def separate_node(node):
    if not '|' in node: return False, False
    n=node.split('|')
    return n

generic_logger=logging.getLogger("SystemLog")
generic_logger.setLevel(logging.DEBUG)
#DEBUG INFO WARNING ERROR CRITICAL
#create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
#create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#add formatter to ch
ch.setFormatter(formatter)
#add ch to logger
generic_logger.addHandler(ch)

generic_logger.debug("Logger initiated.")

def load_image(filename):
    generic_logger.error("No gui handler initialized!  Probably crashing pretty horribly...")
    
def load_sprite(filename):
    generic_logger.error("No gui handler initialized!  Probably crashing pretty horribly...")    
