#!/usr/bin/env python3

import os
import json
import argparse
from character_extractor import CharacterExtractor
from graph_generator import GraphGenerator

class CharacterAnalysisPipeline:
    def __init__(self, data_dir="../Middlemarch-8_books_byCJ", output_dir="outputs"):
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.extractor = CharacterExtractor(data_dir)
        self.generator = GraphGenerator(data_dir)
        
        os.makedirs(output_dir, exist_ok=True)
    
    def run_full_pipeline(self):
        print("Starting Character Analysis Pipeline")
        print("=" * 50)
        
        print("\nStep 1: Extracting character data...")
        raw_data = self.extractor.save_enhanced_data(self.output_dir)
        print(f"Processed {len(raw_data['individual_books'])} books")
        print(f"Found {len(raw_data['combined']['characters'])} unique characters")
        
        print("\nStep 2: Generating graph variations...")
        variations = self.generator.export_all_variations(self.output_dir)
        print(f"Generated {len(variations)} graph variations")
        
        print("\nStep 3: Creating analysis summary...")
        summary = self._create_analysis_summary(raw_data, variations)
        
        with open(os.path.join(self.output_dir, "analysis_summary.json"), 'w') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print("Analysis summary saved")
        
        print("\nStep 4: Generating insights...")
        insights = self._generate_insights(raw_data)
        
        with open(os.path.join(self.output_dir, "character_insights.json"), 'w') as f:
            json.dump(insights, f, indent=2, ensure_ascii=False)
        
        print("Character insights saved")
        
        print("\n" + "=" * 50)
        print("Pipeline completed successfully!")
        print(f"Output directory: {os.path.abspath(self.output_dir)}")
        
        return summary, insights
    
    def _create_analysis_summary(self, raw_data, variations):
        combined_data = raw_data['combined']
        
        dialogue_stats = combined_data['dialogue_counts']
        total_dialogue = sum(dialogue_stats.values())
        
        top_by_dialogue = sorted(dialogue_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        top_by_interactions = sorted(
            [(char, len(interactions)) for char, interactions in combined_data['interactions'].items()],
            key=lambda x: x[1], reverse=True
        )[:10]
        
        book_stats = []
        for book_data in raw_data['individual_books']:
            book_stats.append({
                'book': book_data['book'],
                'characters': len(book_data['characters']),
                'total_dialogue': sum(book_data['dialogue_counts'].values()),
                'total_interactions': sum(len(interactions) for interactions in book_data['interactions'].values()),
                'unique_character_pairs': len(book_data['co_occurrences'])
            })
        
        return {
            'overview': {
                'total_characters': len(combined_data['characters']),
                'total_dialogue_instances': total_dialogue,
                'total_books_processed': len(raw_data['individual_books']),
                'graph_variations_created': len(variations)
            },
            'top_characters': {
                'by_dialogue': [
                    {'id': char_id, 'name': combined_data['characters'].get(char_id, char_id), 'count': count}
                    for char_id, count in top_by_dialogue
                ],
                'by_interactions': [
                    {'id': char_id, 'name': combined_data['characters'].get(char_id, char_id), 'interactions': count}
                    for char_id, count in top_by_interactions
                ]
            },
            'book_statistics': book_stats,
            'graph_variations': variations
        }
    
    def _generate_insights(self, raw_data):
        combined_data = raw_data['combined']
        
        insights = {
            'character_analysis': {},
            'narrative_patterns': {},
            'relationship_dynamics': {}
        }
        
        for char_id, char_name in combined_data['characters'].items():
            dialogue_count = combined_data['dialogue_counts'].get(char_id, 0)
            interactions = len(combined_data['interactions'].get(char_id, []))
            contexts = len(combined_data['contexts'].get(char_id, []))
            
            prominence_score = (dialogue_count * 0.4) + (interactions * 0.4) + (contexts * 0.2)
            
            insights['character_analysis'][char_id] = {
                'name': char_name,
                'dialogue_count': dialogue_count,
                'interaction_count': interactions,
                'context_appearances': contexts,
                'prominence_score': round(prominence_score, 2),
                'character_type': self._classify_character(dialogue_count, interactions, contexts)
            }
        
        book_progression = []
        for book_data in raw_data['individual_books']:
            book_progression.append({
                'book': book_data['book'],
                'character_activity': sum(book_data['dialogue_counts'].values()),
                'new_characters': len(book_data['characters']),
                'interaction_density': len(book_data['co_occurrences'])
            })
        
        insights['narrative_patterns'] = {
            'book_progression': book_progression,
            'character_evolution': self._analyze_character_evolution(raw_data['individual_books'])
        }
        
        co_occurrences = combined_data['co_occurrences']
        strong_relationships = []
        
        for char1, relationships in co_occurrences.items():
            for char2, strength in relationships.items():
                if strength > 5 and char1 < char2:
                    strong_relationships.append({
                        'character1': combined_data['characters'].get(char1, char1),
                        'character2': combined_data['characters'].get(char2, char2),
                        'interaction_strength': strength
                    })
        
        insights['relationship_dynamics'] = {
            'strong_relationships': sorted(strong_relationships, key=lambda x: x['interaction_strength'], reverse=True)[:20]
        }
        
        return insights
    
    def _classify_character(self, dialogue, interactions, contexts):
        if dialogue > 20 and interactions > 15:
            return "protagonist"
        elif dialogue > 10 and interactions > 8:
            return "major_character"
        elif dialogue > 3 or interactions > 5:
            return "supporting_character"
        else:
            return "minor_character"
    
    def _analyze_character_evolution(self, book_data_list):
        character_evolution = {}
        
        for book_data in book_data_list:
            for char_id, dialogue_count in book_data['dialogue_counts'].items():
                if char_id not in character_evolution:
                    character_evolution[char_id] = []
                
                character_evolution[char_id].append({
                    'book': book_data['book'],
                    'dialogue': dialogue_count,
                    'interactions': len(book_data['interactions'].get(char_id, []))
                })
        
        evolving_characters = {}
        for char_id, evolution in character_evolution.items():
            if len(evolution) >= 3:
                dialogue_trend = [e['dialogue'] for e in evolution]
                if max(dialogue_trend) > min(dialogue_trend) * 2:
                    evolving_characters[char_id] = evolution
        
        return evolving_characters

def main():
    parser = argparse.ArgumentParser(description="Character Analysis Pipeline for Middlemarch")
    parser.add_argument("--data-dir", default="../Middlemarch-8_books_byCJ", help="Directory containing book XML files")
    parser.add_argument("--output-dir", default="outputs", help="Output directory for results")
    parser.add_argument("--book", type=int, help="Process only a specific book (1-8)")
    parser.add_argument("--weight-by", choices=['co_occurrence', 'interaction_frequency'], 
                       default='co_occurrence', help="Edge weighting method")
    
    args = parser.parse_args()
    
    pipeline = CharacterAnalysisPipeline(args.data_dir, args.output_dir)
    
    if args.book:
        print(f"Processing Book {args.book} only...")
        generator = GraphGenerator(args.data_dir)
        char_map = generator.create_character_map(args.book, args.weight_by)
        
        filename = f"book_{args.book}_{args.weight_by}.json"
        output_path = os.path.join(args.output_dir, filename)
        
        with open(output_path, 'w') as f:
            json.dump(char_map, f, indent=2, ensure_ascii=False)
        
        print(f"Book {args.book} analysis complete: {output_path}")
    else:
        summary, insights = pipeline.run_full_pipeline()
        
        print("\nKey Insights:")
        top_char = max(insights['character_analysis'], key=lambda x: insights['character_analysis'][x]['prominence_score'])
        print(f"Most active character: {insights['character_analysis'][top_char]['name']}")
        protagonist_count = sum(1 for char in insights['character_analysis'].values() if char['character_type'] == 'protagonist')
        print(f"Total protagonist-level characters: {protagonist_count}")
        if insights['relationship_dynamics']['strong_relationships']:
            strongest = insights['relationship_dynamics']['strong_relationships'][0]
            print(f"Strongest relationship: {strongest['character1']} - {strongest['character2']}")

if __name__ == "__main__":
    main()