"""
Graph visualization and path generation for flowchart testing.

This module provides:
1. get_graph() - Creates a simple visualization of the flowchart
2. get_colored_graph() - Creates a visualization with color-coded paths
3. PathGenerator - Calculates edge coverage test paths
"""

import graphviz
import os
from collections import Counter

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)


def get_graph(edges, graph_name='graph'):
    """
    create graph visualization from a list of edges
    
    Args:
        edges: List of tuples (source, label, destination)
        graph_name: Name for the output file
    """
    dot = graphviz.Digraph()
    for edge in edges:
        dot.edge(str(edge[0]), str(edge[2]), label=str(edge[1]))
    
    output_path = os.path.join(RESULTS_DIR, graph_name)
    dot.render(output_path, format='png')
    return output_path + '.png'


def get_colored_graph(paths, edges_extra=[], graph_name='graph'):
    """
    create a graph visualization with color-coded paths
    
    Args:
        paths: List of paths, where each path is a list of edges
        edges_extra: Additional edges to draw in black
        graph_name: Name for the output file
    """
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'cyan', 'magenta', 'gold', 'pink']
    dot = graphviz.Digraph()
    
    for index, path in enumerate(paths):
        color = colors[index % len(colors)]
        for edge in path:
            dot.edge(str(edge[0]), str(edge[2]), label=str(edge[1]), color=color)
    
    for edge in edges_extra:
        dot.edge(str(edge[0]), str(edge[2]), label=str(edge[1]), color='black')
    
    output_path = os.path.join(RESULTS_DIR, graph_name)
    dot.render(output_path, format='png')
    return output_path + '.png'


class PathGenerator:
    """
    generates test paths for test depth level 1 coverage from a flowchart using a greedy approach
    """

    def __init__(self, edges):
        """
        initialize the path generator with a list of edges and calculates
        all possible paths through a flowchart
        
        Args:
            edges: List of tuples (source, label, destination)
        """
        self.edges = self.deduplicate_edge_labels(edges)
        
        #lookup: decision point -> outgoing edges
        self.edge_option_dict = {
            item: self.get_vertex_options(item) 
            for item in self.get_vertices()
        }
        
        #lookup: (source, label) -> destination
        self.find_destination_dict = {
            (item[0], item[1]): item[2] 
            for item in self.edges
        }
        
        # find endpoints
        self.end_points = list(set([item[2] for item in self.edges]) - set([item[0] for item in self.edges]))

        # find all possible paths
        self.all_paths = self.get_all_paths()
        print(f"Total number of paths: {len(self.all_paths)}")

    def deduplicate_edge_labels(self, edges):
        """
        rename duplicate labels for edges with the same origin and destination
        """
        
        edge_counts = Counter([(item[0],item[1]) for item in edges])
        
        edge_seen = {}
        result = []
        
        for edge in edges:
            origin, label, destination = edge
            if edge_counts[(origin, label)] > 1:
                if (origin, label) not in edge_seen:
                    edge_seen[(origin, label)] = 0
                edge_seen[(origin, label)] += 1
                new_label = f"{label}_{edge_seen[(origin, label)]}"
                result.append((origin, new_label, destination))
                
            else:
                result.append(edge)
        return result

    def get_vertices(self):
        """get all unique source vertices"""
        return list(set([item[0] for item in self.edges]))

    def get_vertex_options(self, vertex):
        """get all possible labels (options) leaving a vertex"""
        return [item[1] for item in self.edges if item[0] == vertex]

    def get_all_paths(self):
        """
        find all possible paths through the flowchart from Start to an endpoint:

        uses depth-first search (dfs) with a shared visited_states set to prevent
        re-exploring the same (node, path-so-far) state. This ensures loops are
        traversed at most once per path
        """
        visited_states = set()

        def dfs(origin, value, path):
            next_vertex = self.find_destination_dict[(origin, value)]
            current_path = path + [(origin, value, next_vertex)]

            if next_vertex in self.end_points:
                return [current_path]
            
            current_state = (next_vertex, frozenset(current_path))
            visited_states.add(current_state)
            options = self.edge_option_dict[next_vertex]
            
            all_paths = []
            for val in options:
                future_dest = self.find_destination_dict[(next_vertex, val)]
                future_path = current_path + [(next_vertex, val, future_dest)]
                future_state = (future_dest, frozenset(future_path))

                if future_state in visited_states:
                    continue
                    
                all_paths.extend(dfs(next_vertex, val, current_path))
            
            return all_paths
        
        return dfs('Start', '', [])

    def run_test_level_depth_1_coverage(self):
        """
        find set of paths needed for test level depth 1 coverage
        """
        selected_paths_3syntax = self.find_max_new_coverage(
            list(self.all_paths),
            list(self.edges)
        )
        
        self.edge_coverage_3syntax = selected_paths_3syntax
        print(f"Total paths needed for edge coverage: {len(selected_paths_3syntax)}")
        
        # remove the first edge (Start -> first node)
        return [path[1:] for path in selected_paths_3syntax]

    def find_max_new_coverage(self, all_paths, unique_edges, selected_paths=None):
        """
        greedy algorithm for test level depth 1 coverage:
        at each step, select the path that covers the most uncovered edges. Repeat until all edges are covered
        """
        if selected_paths is None:
            selected_paths = []
            unique_edges = set(tuple(e) for e in unique_edges)
            print('paths')
            print(len(self.all_paths))
            for path in all_paths:
                print(path)
                print()
            print('unique edges')
            print(unique_edges)
        
        # base case: all edges covered
        if not unique_edges:
            return selected_paths
        
        # find path with maximum new coverage
        coverage_dict = {
            index: len(unique_edges.intersection(set(tuple(e) for e in path)))
            for index, path in enumerate(all_paths)
        }
        
        # select the best path: max coverage, then shortest path as tie-breaker
        max_index = max(
            coverage_dict,
            key=lambda i: (coverage_dict[i], -len(all_paths[i]))
        )
        selected_paths.append(all_paths[max_index])
        
        # remove covered edges
        unique_edges = unique_edges.difference(set(tuple(e) for e in all_paths[max_index]))
        all_paths.pop(max_index)
        
        return self.find_max_new_coverage(all_paths, unique_edges, selected_paths)
