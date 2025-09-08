from graph import Graph
from collections import Counter
from character_extractor import process_middlemarch_data
import random
import math

def create_character_graph(characters, interactions):
    G = Graph()
    
    for char_id, name in characters.items():
        G.add_node(char_id, name=name, label=name)
    
    edge_weights = Counter()
    for char, connected_chars in interactions.items():
        for connected_char in connected_chars:
            edge = tuple(sorted([char, connected_char]))
            edge_weights[edge] += 1
    
    for (char1, char2), weight in edge_weights.items():
        G.add_edge(char1, char2, weight)
    
    return G

def calculate_centrality_metrics(G):
    return {
        'degree': G.degree_centrality(),
        'betweenness': G.betweenness_centrality(),
        'closeness': G.closeness_centrality(),
        'eigenvector': G.eigenvector_centrality()
    }

def detect_communities(G):
    return G.detect_communities_simple()

def generate_spring_layout(G, iterations=50, k=3):
    positions = {}
    
    for node in G.nodes:
        positions[node] = [random.uniform(-1, 1), random.uniform(-1, 1)]
    
    for _ in range(iterations):
        forces = {node: [0, 0] for node in G.nodes}
        
        for node1 in G.nodes:
            for node2 in G.nodes:
                if node1 != node2:
                    dx = positions[node2][0] - positions[node1][0]
                    dy = positions[node2][1] - positions[node1][1]
                    distance = math.sqrt(dx*dx + dy*dy) or 0.01
                    
                    if node2 in G.neighbors(node1):
                        force = (distance - k) / distance * 0.1
                        forces[node1][0] += dx * force
                        forces[node1][1] += dy * force
                    else:
                        repulsion = k*k / (distance*distance) * 0.01
                        forces[node1][0] -= dx / distance * repulsion
                        forces[node1][1] -= dy / distance * repulsion
        
        for node in G.nodes:
            positions[node][0] += forces[node][0]
            positions[node][1] += forces[node][1]
    
    return positions

def create_character_map(data_dir="../Middlemarch-8_books_byCJ"):
    characters, interactions = process_middlemarch_data(data_dir)
    
    G = create_character_graph(characters, interactions)
    
    centrality_metrics = calculate_centrality_metrics(G)
    communities = detect_communities(G)
    spring_layout = generate_spring_layout(G)
    
    character_map = {
        'nodes': [],
        'edges': [],
        'metrics': centrality_metrics,
        'communities': communities,
        'layouts': {'spring': spring_layout}
    }
    
    for node_id in G.nodes:
        node_data = G.nodes[node_id]
        
        node_info = {
            'id': node_id,
            'name': node_data['name'],
            'degree': G.degree(node_id),
            'community': communities.get(node_id, 0),
            'centrality': {
                'degree': centrality_metrics['degree'].get(node_id, 0),
                'betweenness': centrality_metrics['betweenness'].get(node_id, 0),
                'closeness': centrality_metrics['closeness'].get(node_id, 0),
                'eigenvector': centrality_metrics['eigenvector'].get(node_id, 0)
            }
        }
        
        if node_id in spring_layout:
            node_info['spring_x'] = spring_layout[node_id][0]
            node_info['spring_y'] = spring_layout[node_id][1]
        
        character_map['nodes'].append(node_info)
    
    for node1 in G.nodes:
        for node2 in G.neighbors(node1):
            if node1 < node2:
                edge_data = {
                    'source': node1,
                    'target': node2,
                    'weight': G.get_edge_weight(node1, node2)
                }
                character_map['edges'].append(edge_data)
    
    return character_map

if __name__ == "__main__":
    character_map = create_character_map()
    print(f"Generated character map with {len(character_map['nodes'])} nodes and {len(character_map['edges'])} edges")
    
    top_central = sorted(character_map['nodes'], key=lambda x: x['centrality']['degree'], reverse=True)[:5]
    print("\nTop 5 most central characters:")
    for char in top_central:
        print(f"  {char['name']}: {char['centrality']['degree']:.3f}")