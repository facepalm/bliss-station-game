#from pygraph.classes.graph import graph
#from pygraph.algorithms.minmax import heuristic_search
#from pygraph.algorithms.heuristics import euclidean

import networkx as nx
import numpy as np
from util import separate_node

class PathingWidget(object):
    def __init__(self, owner, node_graph, start, end, pos = None, end_pos=None):
        self.owner = owner
        #print start,end
        if not nx.has_path(node_graph,start,end): 
            self.valid = False
            return None
        #print "----------NEW PATH---------"
        self.path_list = nx.dijkstra_path(node_graph, source=start, target=end)
        self.total_length = nx.dijkstra_path_length(node_graph, source=start, target=end)
        self.current_coords = pos if pos is not None else self.owner.station.loc_to_xyz( start )
        self.end_pos = end_pos
        self.completed = False
        self.valid=True
        
    def traverse_step(self,dist):
        goal_xyz = self.owner.station.loc_to_xyz( self.path_list[0] ) if self.path_list else self.end_pos
        if goal_xyz==None: return False
        node_vec = goal_xyz - self.current_coords
        dist_to_node = np.sqrt( np.vdot( node_vec , node_vec ) )
        if dist >= dist_to_node:
            if not self.path_list:
                self.completed = True
                self.owner.xyz = self.end_pos
                return True
            #move to new node, recurse
            remainder_dist = dist - dist_to_node
            self.current_coords = self.owner.station.loc_to_xyz( self.path_list[0] ) 
            mod_call = self.owner.station.get_module_from_loc 
            if mod_call( self.owner.location ) != mod_call( self.path_list[0] ):
                self.owner.transfer_node( self.path_list[0] )            
            self.owner.location = self.path_list.pop( 0 )                       
            if not self.path_list: 
                #print self.owner.xyz, self.current_coords
                self.completed = True
                self.owner.xyz = self.current_coords
                #print self.owner.xyz, self.owner.station.loc_to_xyz( self.owner.location ), self.owner.location 
                return True
            self.traverse_step( remainder_dist )            
        else:    
            self.current_coords = self.current_coords + node_vec * dist / dist_to_node            
            self.owner.orientation = node_vec
            self.owner.xyz = self.current_coords
        return True

