#!/usr/bin/env python3

from export_json import export_character_map_json, export_d3_format, export_cytoscape_format
from graph_generator import create_character_map
import os
import json

def generate_character_maps(data_dir="../Middlemarch-8_books_byCJ", output_dir="."):
    print("Generating character maps from Middlemarch data...")
    
    if not os.path.exists(data_dir):
        print(f"Error: Data directory {data_dir} not found")
        return
    
    character_map = create_character_map(data_dir)
    
    print(f"Generated character map:")
    print(f"  - {len(character_map['nodes'])} characters")
    print(f"  - {len(character_map['edges'])} relationships")
    print(f"  - {len(set(character_map['communities'].values()))} communities detected")
    
    json_file = os.path.join(output_dir, "middlemarch_character_map.json")
    d3_file = os.path.join(output_dir, "middlemarch_d3.json")
    cytoscape_file = os.path.join(output_dir, "middlemarch_cytoscape.json")
    
    export_character_map_json(json_file, data_dir)
    export_d3_format(d3_file, data_dir)
    export_cytoscape_format(cytoscape_file, data_dir)
    
    print(f"\nExported files:")
    print(f"  - {json_file} (full data)")
    print(f"  - {d3_file} (D3.js format)")
    print(f"  - {cytoscape_file} (Cytoscape format)")
    
    top_characters = sorted(character_map['nodes'], key=lambda x: x['centrality']['degree'], reverse=True)[:5]
    print(f"\nTop 5 most central characters:")
    for i, char in enumerate(top_characters, 1):
        print(f"  {i}. {char['name']} (degree: {char['centrality']['degree']:.3f})")
    
    return {
        'character_map': character_map,
        'files': {
            'full': json_file,
            'd3': d3_file,
            'cytoscape': cytoscape_file
        }
    }

if __name__ == "__main__":
    result = generate_character_maps()
    print("\nCharacter maps generated successfully!")