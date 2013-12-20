#from pygraph.classes.graph import graph
#from pygraph.algorithms.minmax import heuristic_search
#from pygraph.algorithms.heuristics import euclidean

import networkx as nx
import numpy as np

class PathingWidget(object):
    def __init__(self, owner, node_graph, start, end, pos = None):
        self.owner = owner
        print start,end
        if not nx.has_path(node_graph,start,end): 
            self.valid = False
            return None
        print "----------NEW PATH---------"
        self.path_list = nx.dijkstra_path(node_graph, source=start, target=end)
        self.total_length = nx.dijkstra_path_length(node_graph, source=start, target=end)
        self.current_coords = pos if pos is not None else self.owner.station.loc_to_xyz( start )
        self.completed = False
        self.valid=True
        
    def traverse_step(self,dist):        
        node_vec = self.owner.station.loc_to_xyz( self.path_list[0] ) - self.current_coords
        dist_to_node = np.sqrt( np.vdot( node_vec , node_vec ) )
        #print dist_to_node, dist, self.path_list, self.current_coords, self.owner.station.loc_to_xyz( self.path_list[0] )
        if dist >= dist_to_node:
            #move to new node, recurse
            remainder_dist = dist - dist_to_node
            self.current_coords = self.owner.station.loc_to_xyz( self.path_list[0] ) 
            self.owner.location = self.path_list.pop( 0 )                       
            if not self.path_list: 
                self.completed = True
                self.owner.xyz = self.current_coords
                return True
            self.traverse_step( remainder_dist )            
        else:    
            self.current_coords = self.current_coords + node_vec * dist / dist_to_node            
            self.owner.orientation = node_vec
            self.owner.xyz = self.current_coords

