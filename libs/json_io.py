# Copyright (c) 2024 LabelCraft
# Custom JSON format for annotation storage

import json
import os
from datetime import datetime


class LabelCraftJSONWriter:
    """Write annotations in LabelCraft JSON format"""
    
    def __init__(self, img_folder_name, img_file_name, image_shape, filename, local_img_path=None):
        self.img_folder_name = img_folder_name
        self.img_file_name = img_file_name
        self.image_shape = image_shape  # [height, width, depth]
        self.filename = filename
        self.local_img_path = local_img_path or img_file_name
        self.verified = False
        self.shapes = []
    
    def add_bnd_box(self, xmin, ymin, xmax, ymax, label, difficult=0):
        """Add a bounding box annotation"""
        shape = {
            'label': label,
            'type': 'rectangle',
            'bbox': [int(xmin), int(ymin), int(xmax), int(ymax)],
            'points': [
                [int(xmin), int(ymin)],
                [int(xmax), int(ymin)],
                [int(xmax), int(ymax)],
                [int(xmin), int(ymax)]
            ],
            'difficult': bool(difficult),
            'occluded': False
        }
        self.shapes.append(shape)
    
    def add_polygon(self, points, label, difficult=0):
        """Add a polygon annotation"""
        shape = {
            'label': label,
            'type': 'polygon',
            'points': [[int(p[0]), int(p[1])] for p in points],
            'difficult': bool(difficult),
            'occluded': False
        }
        self.shapes.append(shape)
    
    def write(self, target_file=None):
        """Write annotations to JSON file"""
        if target_file is None:
            target_file = self.filename
        
        # Ensure .json extension
        if not target_file.lower().endswith('.json'):
            target_file += '.json'
        
        data = {
            'version': '1.0',
            'image': {
                'path': self.local_img_path,
                'width': self.image_shape[1],
                'height': self.image_shape[0],
                'depth': self.image_shape[2]
            },
            'annotations': [],
            'metadata': {
                'verified': self.verified,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'tool': 'LabelCraft'
            }
        }
        
        # Add shapes with IDs
        for idx, shape in enumerate(self.shapes, 1):
            annotation = {
                'id': idx,
                'label': shape['label'],
                'type': shape.get('type', 'rectangle'),
                'difficult': shape.get('difficult', False),
                'occluded': shape.get('occluded', False)
            }
            
            # Add bbox if rectangle
            if 'bbox' in shape:
                annotation['bbox'] = shape['bbox']
            
            # Add points
            if 'points' in shape:
                annotation['points'] = shape['points']
            
            data['annotations'].append(annotation)
        
        # Write to file
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return target_file


class LabelCraftJSONReader:
    """Read annotations from LabelCraft JSON format"""
    
    def __init__(self, filepath):
        self.filepath = filepath
        self.shapes = []
        self.image_path = None
        self.image_size = None
        self.verified = False
        
        self.parse_json()
    
    def parse_json(self):
        """Parse JSON file and extract annotations"""
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract image info
            if 'image' in data:
                self.image_path = data['image'].get('path')
                self.image_size = (
                    data['image'].get('width', 0),
                    data['image'].get('height', 0),
                    data['image'].get('depth', 3)
                )
            
            # Extract verified status
            if 'metadata' in data:
                self.verified = data['metadata'].get('verified', False)
            
            # Extract annotations
            if 'annotations' in data:
                for ann in data['annotations']:
                    shape = {
                        'label': ann.get('label', ''),
                        'difficult': ann.get('difficult', False),
                        'points': ann.get('points', [])
                    }
                    
                    # Convert bbox to points if needed
                    if 'bbox' in ann and not shape['points']:
                        xmin, ymin, xmax, ymax = ann['bbox']
                        shape['points'] = [
                            [xmin, ymin],
                            [xmax, ymin],
                            [xmax, ymax],
                            [xmin, ymax]
                        ]
                    
                    self.shapes.append(shape)
        
        except Exception as e:
            print(f"Error reading JSON file {self.filepath}: {e}")
            raise
    
    def get_shapes(self):
        """Return parsed shapes"""
        return self.shapes
