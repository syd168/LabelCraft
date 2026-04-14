#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convert properties files to JSON format for the new i18n engine.
"""
import json
import os
from pathlib import Path

def convert_properties_to_json(properties_dir, output_dir):
    """Convert all .properties files to .json format."""
    properties_path = Path(properties_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Map properties file names to language codes
    file_to_lang = {
        'strings.properties': 'en',
        'strings-zh-CN.properties': 'zh-CN',
        'strings-zh-TW.properties': 'zh-TW',
        'strings-ja-JP.properties': 'ja-JP',
        'strings-de-DE.properties': 'de-DE',
        'strings-fr-FR.properties': 'fr-FR',
    }
    
    for prop_file in properties_path.glob('*.properties'):
        lang_code = file_to_lang.get(prop_file.name)
        if not lang_code:
            print(f"Skipping unknown file: {prop_file.name}")
            continue
        
        print(f"Converting {prop_file.name} -> {lang_code}.json")
        
        # Parse properties file
        flat_dict = {}
        with open(prop_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Handle \n escape sequences
                    value = value.replace('\\n', '\n')
                    flat_dict[key.strip()] = value.strip()
        
        # Convert flat keys to nested structure
        nested_dict = {}
        for key, value in flat_dict.items():
            parts = key.split('.')
            current = nested_dict
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        
        # Write JSON file
        output_file = output_path / f"{lang_code}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(nested_dict, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ Created {output_file}")

if __name__ == '__main__':
    # Convert properties files from resources/strings to locales
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    properties_dir = project_root / 'resources' / 'strings'
    output_dir = project_root / 'locales'
    
    if properties_dir.exists():
        convert_properties_to_json(properties_dir, output_dir)
        print("\n✓ Conversion complete!")
    else:
        print(f"Properties directory not found: {properties_dir}")
