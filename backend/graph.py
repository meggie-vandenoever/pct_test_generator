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

    def __init__(self, edges, test_depth_level):
        """
        initialize the path generator with a list of edges and calculates
        all possible paths through a flowchart
        
        Args:
            edges: List of tuples (source, label, destination)
        """
        self.test_depth_level = test_depth_level
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
    
    def extract_ntuples_from_path(self, path):
        """
        extract all N consecutive edges that appear in a path,
        by sliding a window of size N over the path to find
        all consecutive edge sequences and is used for DFS state tracking

        """
        n = self.test_depth_level
        if len(path) < n:
            return frozenset()
        if n == 1:
            return frozenset(path)
        return frozenset(
            tuple(path[i:i+n]) for i in range(len(path) - n + 1)
        )
    def get_all_paths(self):
        """
        find all paths using N consecutive edge tuples for state tracking,
        where N = test_depth_level. This allows loops to repeat enough times
        to cover all N consecutive edge combinations
        """
        visited_states = set()

        def dfs(origin, value, path):
            next_vertex = self.find_destination_dict[(origin, value)]
            current_path = path + [(origin, value, next_vertex)]

            if next_vertex in self.end_points:
                return [current_path]

            current_state = (next_vertex, self.extract_ntuples_from_path(current_path))
            if current_state[1] != frozenset():
                visited_states.add(current_state)

            options = self.edge_option_dict[next_vertex]
            all_paths = []

            for val in options:
                future_dest = self.find_destination_dict[(next_vertex, val)]
                future_path = current_path + [(next_vertex, val, future_dest)]
                future_state = (future_dest, self.extract_ntuples_from_path(future_path))

                if future_state in visited_states:
                    continue

                all_paths.extend(dfs(next_vertex, val, current_path))

            return all_paths
        return dfs('Start', self.edge_option_dict['Start'][0], [])

    def find_max_new_coverage(self, all_paths, set_consecutive_edges, selected_paths=None):
        """
        greedy algorithm for test depth level N coverage:
        at each step, select the path that covers the most uncovered pair of N consecutive edges. Repeat untill all edges are covered
        """
        if selected_paths is None:
            selected_paths = []
            set_consecutive_edges = set(set_consecutive_edges)

        # base case: all edges covered
        if not set_consecutive_edges:
            return selected_paths
        
        # find path with maximum new coverage
        coverage_dict = {
            index: len(set_consecutive_edges.intersection(set(self.extract_ntuples_from_path(path))))
            for index, path in enumerate(all_paths)
        }
        
        # select the best path: max coverage, then shortest path as tie-breaker
        max_index = max(
            coverage_dict,
            key=lambda i: (coverage_dict[i], -len(all_paths[i]))
        )
        selected_paths.append(all_paths[max_index])
        
        # remove covered edges
        unique_edges = set_consecutive_edges.difference(self.extract_ntuples_from_path(all_paths[max_index]))
        all_paths.pop(max_index)

        return self.find_max_new_coverage(all_paths, unique_edges, selected_paths)

    def run(self):
        """
        find set of paths needed for corresponding test depth level coverage
        """
        set_consecutive_edges = self.get_all_possible_ntuples(self.edges)

        selected_paths_3syntax = self.find_max_new_coverage(
            list(self.all_paths),
            set_consecutive_edges,
        )
        
        self.edge_coverage_3syntax = selected_paths_3syntax
        print(f"Total paths needed for edge coverage: {len(selected_paths_3syntax)}")
        
        return selected_paths_3syntax
    
    def get_all_possible_ntuples(self, list_of_edges):
        """
        computes all combinations of N consecutive edges that could exist
        and is used to define coverage requirements for the greedy algorithm
        """
        if self.test_depth_level == 1:
            return list_of_edges
        
        result = [
            (e1, e2) for e1 in list_of_edges for e2 in list_of_edges
            if e1[2] == e2[0]
        ]
        
        for _ in range(self.test_depth_level - 2):
            result = [
                (*chain, next_edge)
                for chain in result
                for next_edge in list_of_edges
                if chain[-1][2] == next_edge[0]
            ]
        
        return result