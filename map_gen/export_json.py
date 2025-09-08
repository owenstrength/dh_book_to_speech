import json
from graph_generator import create_character_map

def export_character_map_json(output_file="middlemarch_character_map.json", data_dir="../Middlemarch-8_books_byCJ"):
    character_map = create_character_map(data_dir)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(character_map, f, indent=2, ensure_ascii=False)
    
    return output_file

def export_d3_format(output_file="middlemarch_d3.json", data_dir="../Middlemarch-8_books_byCJ"):
    character_map = create_character_map(data_dir)
    
    d3_format = {
        "nodes": character_map['nodes'],
        "links": [
            {
                "source": edge['source'],
                "target": edge['target'],
                "value": edge['weight']
            }
            for edge in character_map['edges']
        ]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(d3_format, f, indent=2, ensure_ascii=False)
    
    return output_file

def export_cytoscape_format(output_file="middlemarch_cytoscape.json", data_dir="../Middlemarch-8_books_byCJ"):
    character_map = create_character_map(data_dir)
    
    cytoscape_format = {
        "elements": {
            "nodes": [
                {
                    "data": {
                        "id": node['id'],
                        "name": node['name'],
                        "degree": node['degree'],
                        "community": node['community'],
                        **node['centrality']
                    },
                    "position": {
                        "x": node.get('spring_x', 0) * 100,
                        "y": node.get('spring_y', 0) * 100
                    }
                }
                for node in character_map['nodes']
            ],
            "edges": [
                {
                    "data": {
                        "id": f"{edge['source']}-{edge['target']}",
                        "source": edge['source'],
                        "target": edge['target'],
                        "weight": edge['weight']
                    }
                }
                for edge in character_map['edges']
            ]
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cytoscape_format, f, indent=2, ensure_ascii=False)
    
    return output_file

if __name__ == "__main__":
    print("Exporting character map in multiple formats...")
    
    json_file = export_character_map_json()
    print(f"Exported full character map: {json_file}")
    
    d3_file = export_d3_format()
    print(f"Exported D3.js format: {d3_file}")
    
    cytoscape_file = export_cytoscape_format()
    print(f"Exported Cytoscape format: {cytoscape_file}")
    
    print("\nFiles ready for web visualization!")