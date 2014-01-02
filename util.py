
TIME_FACTOR = 240 # 120# 24

equipment_targets = dict()

def quad_mean(x,y,wx=1,wy=1):
    return pow( (1.0*wx*x*x + wy*y*y)/(wx + wy) ,0.5)
    
def seconds(time=1,units='minutes'):
    return time*60 if units == 'minutes' else time*3600 if units == 'hours' \
                                         else time*86400 if units=='days' \
                                         else time*2592000 if units=='months' \
                                         else 10    
                                         
                                         
def separate_node(node):
    if not '|' in node: return False, False
    n=node.split('|')
    return n
                                         
                                         
