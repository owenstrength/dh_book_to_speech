from graph import Graph
from character_extractor import CharacterExtractor
from collections import Counter
import random
import math
import json
import os

class GraphGenerator:
    def __init__(self, data_dir="../Middlemarch-8_books_byCJ"):
        self.data_dir = data_dir
        self.extractor = CharacterExtractor(data_dir)
    
    def create_interaction_graph(self, book_data, weight_by='co_occurrence'):
        G = Graph()
        characters = book_data['characters']
        
        for char_id, name in characters.items():
            dialogue_count = book_data['dialogue_counts'].get(char_id, 0)
            context_count = len(book_data['contexts'].get(char_id, []))
            description = book_data['descriptions'].get(char_id, '')
            
            G.add_node(char_id, 
                      name=name, 
                      dialogue_count=dialogue_count,
                      context_count=context_count,
                      description=description[:200])
        
        if weight_by == 'co_occurrence':
            co_occurrences = book_data['co_occurrences']
            for char1, char_dict in co_occurrences.items():
                for char2, weight in char_dict.items():
                    if char1 < char2:
                        G.add_edge(char1, char2, weight)
        
        elif weight_by == 'interaction_frequency':
            interactions = book_data['interactions']
            edge_weights = Counter()
            for char, connected_chars in interactions.items():
                for connected_char in connected_chars:
                    edge = tuple(sorted([char, connected_char]))
                    edge_weights[edge] += 1
            
            for (char1, char2), weight in edge_weights.items():
                G.add_edge(char1, char2, weight)
        
        return G
    
    def calculate_enhanced_metrics(self, G, book_data):
        centrality_metrics = {
            'degree': G.degree_centrality(),
            'betweenness': G.betweenness_centrality(),
            'closeness': G.closeness_centrality(),
            'eigenvector': G.eigenvector_centrality()
        }
        
        dialogue_counts = book_data['dialogue_counts']
        total_dialogue = sum(dialogue_counts.values()) or 1
        
        dialogue_centrality = {}
        for char_id in G.nodes:
            dialogue_centrality[char_id] = dialogue_counts.get(char_id, 0) / total_dialogue
        
        centrality_metrics['dialogue'] = dialogue_centrality
        
        interaction_strength = {}
        co_occurrences = book_data['co_occurrences']
        
        for char_id in G.nodes:
            total_interactions = sum(co_occurrences.get(char_id, {}).values())
            interaction_strength[char_id] = total_interactions
        
        centrality_metrics['interaction_strength'] = interaction_strength
        
        return centrality_metrics
    
    def generate_force_layout(self, G, iterations=100, k=2):
        positions = {}
        
        for node in G.nodes:
            positions[node] = [random.uniform(-1, 1), random.uniform(-1, 1)]
        
        for iteration in range(iterations):
            forces = {node: [0, 0] for node in G.nodes}
            
            for node1 in G.nodes:
                for node2 in G.nodes:
                    if node1 != node2:
                        dx = positions[node2][0] - positions[node1][0]
                        dy = positions[node2][1] - positions[node1][1]
                        distance = math.sqrt(dx*dx + dy*dy) or 0.01
                        
                        if node2 in G.neighbors(node1):
                            weight = G.get_edge_weight(node1, node2)
                            target_distance = k / (1 + weight * 0.1)
                            force = (distance - target_distance) / distance * 0.1
                            forces[node1][0] += dx * force
                            forces[node1][1] += dy * force
                        else:
                            repulsion = k*k / (distance*distance) * 0.01
                            forces[node1][0] -= dx / distance * repulsion
                            forces[node1][1] -= dy / distance * repulsion
            
            cooling = 1.0 - iteration / iterations
            for node in G.nodes:
                positions[node][0] += forces[node][0] * cooling
                positions[node][1] += forces[node][1] * cooling
        
        return positions
    
    def create_character_map(self, book_number=None, weight_by='co_occurrence'):
        if book_number:
            book_data = self.extractor.process_book(book_number)
            if not book_data:
                raise ValueError(f"Book {book_number} not found")
            map_type = f"book_{book_number}"
        else:
            all_data = self.extractor.process_all_books()
            book_data = all_data['combined']
            map_type = "all_books"
        
        G = self.create_interaction_graph(book_data, weight_by)
        centrality_metrics = self.calculate_enhanced_metrics(G, book_data)
        communities = G.detect_communities_simple()
        
        spring_layout = self.generate_force_layout(G)
        
        character_map = {
            'metadata': {
                'type': map_type,
                'weight_by': weight_by,
                'total_characters': len(G.nodes),
                'total_edges': sum(len(neighbors) for neighbors in G.edges.values()) // 2
            },
            'nodes': [],
            'edges': [],
            'centrality_metrics': centrality_metrics,
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
                'dialogue_count': node_data.get('dialogue_count', 0),
                'context_count': node_data.get('context_count', 0),
                'description': node_data.get('description', ''),
                'centrality': {
                    'degree': centrality_metrics['degree'].get(node_id, 0),
                    'betweenness': centrality_metrics['betweenness'].get(node_id, 0),
                    'closeness': centrality_metrics['closeness'].get(node_id, 0),
                    'eigenvector': centrality_metrics['eigenvector'].get(node_id, 0),
                    'dialogue': centrality_metrics['dialogue'].get(node_id, 0),
                    'interaction_strength': centrality_metrics['interaction_strength'].get(node_id, 0)
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
    
    def export_all_variations(self, output_dir="outputs"):
        os.makedirs(output_dir, exist_ok=True)
        
        variations = []
        
        for weight_method in ['co_occurrence', 'interaction_frequency']:
            try:
                char_map = self.create_character_map(None, weight_method)
                filename = f"all_books_{weight_method}.json"
                
                with open(os.path.join(output_dir, filename), 'w') as f:
                    json.dump(char_map, f, indent=2, ensure_ascii=False)
                
                variations.append({
                    'type': 'all_books',
                    'weight_by': weight_method,
                    'filename': filename,
                    'nodes': len(char_map['nodes']),
                    'edges': len(char_map['edges'])
                })
                
            except Exception as e:
                print(f"Error creating all books {weight_method}: {e}")
        
        for book_num in range(1, 9):
            for weight_method in ['co_occurrence', 'interaction_frequency']:
                try:
                    char_map = self.create_character_map(book_num, weight_method)
                    filename = f"book_{book_num}_{weight_method}.json"
                    
                    with open(os.path.join(output_dir, filename), 'w') as f:
                        json.dump(char_map, f, indent=2, ensure_ascii=False)
                    
                    variations.append({
                        'type': f'book_{book_num}',
                        'weight_by': weight_method,
                        'filename': filename,
                        'nodes': len(char_map['nodes']),
                        'edges': len(char_map['edges'])
                    })
                    
                except Exception as e:
                    print(f"Error creating book {book_num} {weight_method}: {e}")
        
        with open(os.path.join(output_dir, "graph_variations_summary.json"), 'w') as f:
            json.dump(variations, f, indent=2)
        
        return variations

if __name__ == "__main__":
    generator = GraphGenerator()
    variations = generator.export_all_variations()
    
    print(f"Created {len(variations)} graph variations:")
    for var in variations:
        print(f"  {var['filename']}: {var['nodes']} nodes, {var['edges']} edges")