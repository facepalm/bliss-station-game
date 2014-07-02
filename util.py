import logging
import numpy as np
import string

TIME_FACTOR = 168 # 1 irl hour = 1 week
#TIME_FACTOR = 24 # 1 irl hour = 1 day
#TIME_FACTOR = 120

ZOOM = 15

equipment_targets = dict()

GRAPHICS = None
GLOBAL_X=0
GLOBAL_Y=0

def quad_mean(x,y,wx=1,wy=1):
    return pow( (1.0*wx*x*x + wy*y*y)/(wx + wy) ,0.5)
    
def timestring(seconds):
    seconds = int(seconds)
    time=''
    div, rem = (seconds/(2592000*12),seconds%(2592000*12))    
    if div: time = ''.join([time,str(div),' year ' if div==1 else ' years ' ])
    seconds = rem
    div, rem = (seconds/(2592000),seconds%(2592000))    
    if div: time = ''.join([time,str(div),' month ' if div==1 else ' months ' ])
    seconds = rem
    div, rem = (seconds/(86400),seconds%(86400))    
    if div: time = ''.join([time,str(div),' day ' if div==1 else ' days ' ])
    seconds = rem
    div, rem = (seconds/(3600),seconds%(3600))    
    if div: time = ''.join([time,str(div),' hour ' if div==1 else ' hours ' ])
    seconds = rem
    time = ''.join([time,str(seconds),' seconds' ])
    return time    
    
    
    
def seconds(time=1,units='minutes'):
    return time*60 if units == 'minutes' or units == 'minute' \
                                         else time*3600 if units == 'hours' or units == 'hour' \
                                         else time*86400 if units=='days' or units == 'day' \
                                         else time*2592000 if units=='months' or units == 'month' \
                                         else time*2592000*12 if units=='years' or units == 'year' \
                                         else 10    
                                         
                                         
def short_id(long_id):
    return string.upper(long_id[0:6])                                                
                                         
def separate_node(node):
    if not '|' in node: return False, False
    n=node.split('|')
    return n

def vec_dist(a,b):
    diff = b-a
    return np.sqrt( np.vdot( diff , diff ) )

generic_logger=logging.getLogger("SystemLog")
generic_logger.setLevel(logging.DEBUG)
#DEBUG INFO WARNING ERROR CRITICAL
#create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
#create formatter
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
#formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
#add formatter to ch
ch.setFormatter(formatter)
#add ch to logger
generic_logger.addHandler(ch)

generic_logger.debug("Logger initiated.")

def load_image(filename):
    generic_logger.error("No gui handler initialized!  Probably crashing pretty horribly...")

def make_solid_image():
    generic_logger.error("No gui handler initialized!  Probably crashing pretty horribly...")
    
def load_sprite(filename):
    generic_logger.error("No gui handler initialized!  Probably crashing pretty horribly...") 
    
def image_to_sprite():
    pass       
    
def make_solid_sprite():
    pass    
    
def contact_mission_control():
    pass
    
station_batch = None
actor_batch = None
parent_group = None     

scenario = None

