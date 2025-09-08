from collections import defaultdict, Counter
import math

class Graph:
    def __init__(self):
        self.nodes = {}
        self.edges = defaultdict(list)
        self.edge_weights = defaultdict(int)
    
    def add_node(self, node_id, **attributes):
        self.nodes[node_id] = attributes
    
    def add_edge(self, node1, node2, weight=1):
        if node1 not in self.nodes or node2 not in self.nodes:
            return
        
        edge_key = tuple(sorted([node1, node2]))
        self.edge_weights[edge_key] += weight
        
        if node2 not in self.edges[node1]:
            self.edges[node1].append(node2)
        if node1 not in self.edges[node2]:
            self.edges[node2].append(node1)
    
    def degree(self, node_id):
        return len(self.edges[node_id])
    
    def neighbors(self, node_id):
        return self.edges[node_id]
    
    def get_edge_weight(self, node1, node2):
        edge_key = tuple(sorted([node1, node2]))
        return self.edge_weights[edge_key]
    
    def degree_centrality(self):
        if len(self.nodes) <= 1:
            return {node: 0 for node in self.nodes}
        
        max_degree = len(self.nodes) - 1
        return {node: self.degree(node) / max_degree for node in self.nodes}
    
    def betweenness_centrality(self):
        centrality = {node: 0.0 for node in self.nodes}
        
        for source in self.nodes:
            distances, predecessors = self._shortest_paths(source)
            
            for target in self.nodes:
                if source != target:
                    paths = self._count_paths(source, target, predecessors)
                    if paths > 0:
                        for intermediate in self.nodes:
                            if intermediate != source and intermediate != target:
                                paths_through = self._count_paths_through(source, target, intermediate, predecessors)
                                if paths > 0:
                                    centrality[intermediate] += paths_through / paths
        
        n = len(self.nodes)
        if n > 2:
            normalize = 2.0 / ((n - 1) * (n - 2))
            for node in centrality:
                centrality[node] *= normalize
        
        return centrality
    
    def closeness_centrality(self):
        centrality = {}
        
        for node in self.nodes:
            distances, _ = self._shortest_paths(node)
            total_distance = sum(d for d in distances.values() if d != float('inf'))
            
            if total_distance > 0:
                centrality[node] = (len(self.nodes) - 1) / total_distance
            else:
                centrality[node] = 0.0
        
        return centrality
    
    def eigenvector_centrality(self, max_iter=100, tolerance=1e-6):
        centrality = {node: 1.0 for node in self.nodes}
        
        for _ in range(max_iter):
            new_centrality = {node: 0.0 for node in self.nodes}
            
            for node in self.nodes:
                for neighbor in self.neighbors(node):
                    new_centrality[node] += centrality[neighbor]
            
            norm = math.sqrt(sum(v * v for v in new_centrality.values()))
            if norm > 0:
                new_centrality = {node: val / norm for node, val in new_centrality.items()}
            
            converged = all(abs(new_centrality[node] - centrality[node]) < tolerance 
                          for node in self.nodes)
            
            centrality = new_centrality
            if converged:
                break
        
        return centrality
    
    def _shortest_paths(self, source):
        distances = {node: float('inf') for node in self.nodes}
        predecessors = {node: [] for node in self.nodes}
        distances[source] = 0
        
        queue = [source]
        visited = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            for neighbor in self.neighbors(current):
                new_distance = distances[current] + 1
                
                if new_distance < distances[neighbor]:
                    distances[neighbor] = new_distance
                    predecessors[neighbor] = [current]
                    if neighbor not in queue:
                        queue.append(neighbor)
                elif new_distance == distances[neighbor]:
                    if current not in predecessors[neighbor]:
                        predecessors[neighbor].append(current)
        
        return distances, predecessors
    
    def _count_paths(self, source, target, predecessors):
        if source == target:
            return 1
        
        memo = {}
        
        def count_recursive(node):
            if node == source:
                return 1
            if node in memo:
                return memo[node]
            
            count = sum(count_recursive(pred) for pred in predecessors[node])
            memo[node] = count
            return count
        
        return count_recursive(target)
    
    def _count_paths_through(self, source, target, intermediate, predecessors):
        paths_source_to_intermediate = self._count_paths(source, intermediate, predecessors)
        
        distances_from_intermediate, preds_from_intermediate = self._shortest_paths(intermediate)
        paths_intermediate_to_target = self._count_paths(intermediate, target, preds_from_intermediate)
        
        distances_source, _ = self._shortest_paths(source)
        if (distances_source[intermediate] + distances_from_intermediate[target] == 
            distances_source[target]):
            return paths_source_to_intermediate * paths_intermediate_to_target
        
        return 0
    
    def detect_communities_simple(self):
        visited = set()
        communities = {}
        community_id = 0
        
        for node in self.nodes:
            if node not in visited:
                component = self._dfs_component(node, visited)
                for n in component:
                    communities[n] = community_id
                community_id += 1
        
        return communities
    
    def _dfs_component(self, start, visited):
        component = []
        stack = [start]
        
        while stack:
            node = stack.pop()
            if node not in visited:
                visited.add(node)
                component.append(node)
                for neighbor in self.neighbors(node):
                    if neighbor not in visited:
                        stack.append(neighbor)
        
        return component