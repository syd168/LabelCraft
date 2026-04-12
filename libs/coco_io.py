# Copyright (c) 2024 LabelCraft
# COCO format writer for object detection annotations

import json
import os
from datetime import datetime


class COCOWriter:
    """Writer for COCO format annotations"""
    
    def __init__(self, img_folder_name, img_file_name, image_shape, filename, local_img_path=None):
        self.img_folder_name = img_folder_name
        self.img_file_name = img_file_name
        self.image_height = image_shape[0]
        self.image_width = image_shape[1]
        self.image_channels = image_shape[2]
        self.filename = filename
        self.local_img_path = local_img_path or img_file_name
        
        # COCO structure
        self.categories = {}  # category_id -> category_name
        self.annotations = []
        self.annotation_id = 1
        self.verified = False
    
    def add_bnd_box(self, x_min, y_min, x_max, y_max, label, difficult=0):
        """Add a bounding box annotation"""
        # Add category if not exists
        if label not in self.categories.values():
            category_id = len(self.categories) + 1
            self.categories[category_id] = label
        
        # Find category_id for this label
        category_id = None
        for cat_id, cat_name in self.categories.items():
            if cat_name == label:
                category_id = cat_id
                break
        
        # Calculate width and height
        width = x_max - x_min
        height = y_max - y_min
        
        # Create annotation
        annotation = {
            'id': self.annotation_id,
            'image_id': 1,  # Will be set when writing
            'category_id': category_id,
            'bbox': [x_min, y_min, width, height],  # COCO format: [x, y, width, height]
            'area': width * height,
            'iscrowd': 0,
            'ignore': difficult
        }
        
        self.annotations.append(annotation)
        self.annotation_id += 1
    
    def write(self, target_file=None):
        """Write COCO format JSON file"""
        if target_file is None:
            target_file = self.filename
        
        # Build COCO structure
        coco_data = {
            'info': {
                'description': 'LabelCraft COCO Export',
                'url': '',
                'version': '1.0',
                'year': datetime.now().year,
                'contributor': 'LabelCraft',
                'date_created': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            },
            'licenses': [],
            'images': [
                {
                    'id': 1,
                    'width': self.image_width,
                    'height': self.image_height,
                    'file_name': self.img_file_name,
                    'license': 0,
                    'flickr_url': '',
                    'coco_url': '',
                    'date_captured': ''
                }
            ],
            'annotations': self.annotations,
            'categories': [
                {
                    'id': cat_id,
                    'name': cat_name,
                    'supercategory': 'none'
                }
                for cat_id, cat_name in sorted(self.categories.items())
            ]
        }
        
        # Write to file
        with open(target_file, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, indent=2, ensure_ascii=False)
        
        return True
