# Copyright (c) 2024 LabelCraft
# CSV format writer for object detection annotations

import csv
import os


class CSVWriter:
    """Writer for CSV format annotations (compatible with TensorFlow Object Detection API)"""
    
    def __init__(self, img_folder_name, img_file_name, image_shape, filename, local_img_path=None):
        self.img_folder_name = img_folder_name
        self.img_file_name = img_file_name
        self.image_height = image_shape[0]
        self.image_width = image_shape[1]
        self.image_channels = image_shape[2]
        self.filename = filename
        self.local_img_path = local_img_path or img_file_name
        
        # Annotations list
        self.annotations = []
        self.verified = False
    
    def add_bnd_box(self, x_min, y_min, x_max, y_max, label, difficult=0):
        """Add a bounding box annotation"""
        annotation = {
            'filename': self.img_file_name,
            'width': self.image_width,
            'height': self.image_height,
            'class': label,
            'xmin': x_min,
            'ymin': y_min,
            'xmax': x_max,
            'ymax': y_max
        }
        self.annotations.append(annotation)
    
    def write(self, target_file=None):
        """Write CSV format file"""
        if target_file is None:
            target_file = self.filename
        
        # CSV header
        fieldnames = ['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax']
        
        # Write to file
        with open(target_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for annotation in self.annotations:
                writer.writerow(annotation)
        
        return True
