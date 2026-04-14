#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Annotation Converter Module

Provides unified annotation format conversion between different formats.
All conversions go through an internal intermediate format to ensure consistency.

Internal Format Structure:
{
    "image_path": str,           # Path to the image file
    "image_width": int,          # Image width in pixels
    "image_height": int,         # Image height in pixels
    "annotations": [             # List of annotations
        {
            "label": str,        # Object class label
            "bbox": [x, y, w, h],  # Bounding box (x, y) is top-left corner
            "difficult": bool,   # Whether the object is difficult to recognize
            "truncated": bool,   # Whether the object is truncated
            "polygon": [[x1,y1], [x2,y2], ...]  # Optional: polygon points
        }
    ]
}
"""

import os
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom


class AnnotationConverter:
    """Unified annotation format converter"""
    
    @staticmethod
    def read_voc(xml_path):
        """Read PASCAL VOC XML format and convert to internal format"""
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # Get image info
        filename = root.find('filename').text
        size = root.find('size')
        width = int(size.find('width').text)
        height = int(size.find('height').text)
        
        # Build image path (assume same directory as XML)
        image_path = os.path.join(os.path.dirname(xml_path), filename)
        
        # Parse annotations
        annotations = []
        for obj in root.findall('object'):
            label = obj.find('name').text
            bbox_elem = obj.find('bndbox')
            xmin = int(bbox_elem.find('xmin').text)
            ymin = int(bbox_elem.find('ymin').text)
            xmax = int(bbox_elem.find('xmax').text)
            ymax = int(bbox_elem.find('ymax').text)
            
            difficult = obj.find('difficult')
            difficult = int(difficult.text) if difficult is not None else 0
            
            truncated = obj.find('truncated')
            truncated = int(truncated.text) if truncated is not None else 0
            
            annotations.append({
                'label': label,
                'bbox': [xmin, ymin, xmax - xmin, ymax - ymin],
                'difficult': bool(difficult),
                'truncated': bool(truncated)
            })
        
        return {
            'image_path': image_path,
            'image_width': width,
            'image_height': height,
            'annotations': annotations
        }
    
    @staticmethod
    def read_yolo(txt_path, classes_file=None):
        """Read YOLO TXT format and convert to internal format"""
        # Find corresponding image file
        base_name = os.path.splitext(os.path.basename(txt_path))[0]
        txt_dir = os.path.dirname(txt_path)
        
        # Try multiple locations for the image file
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
        image_path = None
        
        # Strategy 1: Look in the same directory as the annotation file
        for ext in image_extensions:
            candidate = os.path.join(txt_dir, base_name + ext)
            if os.path.exists(candidate):
                image_path = candidate
                break
        
        # Strategy 2: Look in 'images' subdirectory of parent directory
        if not image_path:
            parent_dir = os.path.dirname(txt_dir)
            images_dir = os.path.join(parent_dir, 'images')
            if os.path.exists(images_dir):
                for ext in image_extensions:
                    candidate = os.path.join(images_dir, base_name + ext)
                    if os.path.exists(candidate):
                        image_path = candidate
                        break
        
        # Strategy 3: Look in parent directory
        if not image_path:
            parent_dir = os.path.dirname(txt_dir)
            for ext in image_extensions:
                candidate = os.path.join(parent_dir, base_name + ext)
                if os.path.exists(candidate):
                    image_path = candidate
                    break
        
        if not image_path:
            raise FileNotFoundError(f"Cannot find image file for {txt_path}")
        
        # Read image dimensions
        from PySide6.QtGui import QImage
        img = QImage(image_path)
        width = img.width()
        height = img.height()
        
        # Load classes if provided
        classes = []
        if classes_file and os.path.exists(classes_file):
            with open(classes_file, 'r') as f:
                classes = [line.strip() for line in f.readlines()]
            print(f"[read_yolo] Loaded {len(classes)} classes from {classes_file}")
            if len(classes) > 0:
                print(f"[read_yolo] First few classes: {classes[:5]}")
        
        # Parse annotations
        annotations = []
        if os.path.exists(txt_path):
            with open(txt_path, 'r') as f:
                for line in f.readlines():
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        class_id = int(parts[0])
                        x_center = float(parts[1])
                        y_center = float(parts[2])
                        w = float(parts[3])
                        h = float(parts[4])
                        
                        # Convert from normalized to absolute coordinates
                        x = int((x_center - w / 2) * width)
                        y = int((y_center - h / 2) * height)
                        w_abs = int(w * width)
                        h_abs = int(h * height)
                        
                        # Get label name
                        label = classes[class_id] if class_id < len(classes) else str(class_id)
                        
                        # Debug: log first annotation conversion
                        if len(annotations) == 0 and classes:
                            print(f"[read_yolo] Converting class_id={class_id} -> label='{label}' (classes has {len(classes)} entries)")
                        
                        annotations.append({
                            'label': label,
                            'bbox': [x, y, w_abs, h_abs],
                            'difficult': False,
                            'truncated': False
                        })
        
        return {
            'image_path': image_path,
            'image_width': width,
            'image_height': height,
            'annotations': annotations
        }
    
    @staticmethod
    def read_createml(json_path):
        """Read CreateML JSON format and convert to internal format"""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # CreateML format is a list, find the entry for this file
        base_name = os.path.basename(json_path)
        
        for entry in data:
            if entry.get('image') == base_name or entry.get('image').startswith(os.path.basename(json_path).replace('.json', '')):
                image_path = os.path.join(os.path.dirname(json_path), entry['image'])
                
                # Get image dimensions
                from PySide6.QtGui import QImage
                img = QImage(image_path)
                width = img.width()
                height = img.height()
                
                # Parse annotations
                annotations = []
                for annotation in entry.get('annotations', []):
                    label = annotation['label']
                    coords = annotation['coordinates']
                    
                    # CreateML uses x, y, width, height
                    x = int(coords['x'])
                    y = int(coords['y'])
                    w = int(coords['width'])
                    h = int(coords['height'])
                    
                    annotations.append({
                        'label': label,
                        'bbox': [x, y, w, h],
                        'difficult': False,
                        'truncated': False
                    })
                
                return {
                    'image_path': image_path,
                    'image_width': width,
                    'image_height': height,
                    'annotations': annotations
                }
        
        raise ValueError(f"Cannot find matching entry in CreateML file: {json_path}")
    
    @staticmethod
    def read_coco(json_path, image_id=None):
        """Read COCO JSON format and convert to internal format"""
        with open(json_path, 'r') as f:
            coco_data = json.load(f)
        
        # Build category map
        categories = {cat['id']: cat['name'] for cat in coco_data.get('categories', [])}
        
        # Find image
        images = coco_data.get('images', [])
        if image_id is not None:
            image_info = next((img for img in images if img['id'] == image_id), None)
        else:
            # Use first image
            image_info = images[0] if images else None
        
        if not image_info:
            raise ValueError("Cannot find image in COCO file")
        
        # Get image dimensions
        width = image_info['width']
        height = image_info['height']
        image_path = image_info.get('file_name', '')
        
        # Parse annotations for this image
        annotations = []
        for ann in coco_data.get('annotations', []):
            if ann['image_id'] == image_info['id']:
                bbox = ann['bbox']  # [x, y, width, height]
                category_id = ann['category_id']
                label = categories.get(category_id, str(category_id))
                
                annotations.append({
                    'label': label,
                    'bbox': [int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])],
                    'difficult': False,
                    'truncated': False
                })
        
        return {
            'image_path': image_path,
            'image_width': width,
            'image_height': height,
            'annotations': annotations
        }
    
    @staticmethod
    def read_csv(csv_path):
        """Read CSV format and convert to internal format"""
        import csv
        
        # Find corresponding image file
        base_name = os.path.splitext(os.path.basename(csv_path))[0]
        csv_dir = os.path.dirname(csv_path)
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff']
        image_path = None
        
        # Strategy 1: Look in the same directory as the annotation file
        for ext in image_extensions:
            candidate = os.path.join(csv_dir, base_name + ext)
            if os.path.exists(candidate):
                image_path = candidate
                break
        
        # Strategy 2: Look in 'images' subdirectory of parent directory
        if not image_path:
            parent_dir = os.path.dirname(csv_dir)
            images_dir = os.path.join(parent_dir, 'images')
            if os.path.exists(images_dir):
                for ext in image_extensions:
                    candidate = os.path.join(images_dir, base_name + ext)
                    if os.path.exists(candidate):
                        image_path = candidate
                        break
        
        # Strategy 3: Look in parent directory
        if not image_path:
            parent_dir = os.path.dirname(csv_dir)
            for ext in image_extensions:
                candidate = os.path.join(parent_dir, base_name + ext)
                if os.path.exists(candidate):
                    image_path = candidate
                    break
        
        if not image_path:
            raise FileNotFoundError(f"Cannot find image file for {csv_path}")
        
        # Read image dimensions
        from PySide6.QtGui import QImage
        img = QImage(image_path)
        width = img.width()
        height = img.height()
        
        # Parse annotations
        annotations = []
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Expected columns: filename, width, height, class, xmin, ymin, xmax, ymax
                label = row.get('class', row.get('label', ''))
                xmin = int(row.get('xmin', 0))
                ymin = int(row.get('ymin', 0))
                xmax = int(row.get('xmax', 0))
                ymax = int(row.get('ymax', 0))
                
                annotations.append({
                    'label': label,
                    'bbox': [xmin, ymin, xmax - xmin, ymax - ymin],
                    'difficult': False,
                    'truncated': False
                })
        
        return {
            'image_path': image_path,
            'image_width': width,
            'image_height': height,
            'annotations': annotations
        }
    
    @staticmethod
    def read_labelcraft_json(json_path):
        """Read LabelCraft JSON format and convert to internal format"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get image info
        image_info = data.get('image', {})
        image_path = image_info.get('path', '')
        
        # If path is relative, resolve it
        if not os.path.isabs(image_path):
            image_path = os.path.join(os.path.dirname(json_path), image_path)
        
        width = image_info.get('width', 0)
        height = image_info.get('height', 0)
        
        # If dimensions are not available, read from image file
        if width == 0 or height == 0:
            from PySide6.QtGui import QImage
            if os.path.exists(image_path):
                img = QImage(image_path)
                width = img.width()
                height = img.height()
        
        print(f"DEBUG read_labelcraft_json: image={image_path}, size={width}x{height}")
        
        # Parse annotations
        annotations = []
        for ann in data.get('annotations', []):
            label = ann.get('label', '')
            
            # Get bbox from points if bbox not directly available
            if 'bbox' in ann:
                bbox = ann['bbox']  # [xmin, ymin, xmax, ymax]
                x, y, w, h = bbox[0], bbox[1], bbox[2] - bbox[0], bbox[3] - bbox[1]
                print(f"  Annotation: {label}, bbox=[{x},{y},{w},{h}]")
            elif 'points' in ann and len(ann['points']) >= 4:
                # Convert polygon points to bbox
                points = ann['points']
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                x = min(xs)
                y = min(ys)
                w = max(xs) - x
                h = max(ys) - y
                print(f"  Annotation: {label}, points->bbox=[{x},{y},{w},{h}]")
            else:
                print(f"  Skipping annotation (no bbox or points): {ann}")
                continue
            
            annotations.append({
                'label': label,
                'bbox': [int(x), int(y), int(w), int(h)],
                'difficult': ann.get('difficult', False),
                'truncated': False
            })
        
        print(f"DEBUG: Total annotations parsed: {len(annotations)}")
        
        return {
            'image_path': image_path,
            'image_width': width,
            'image_height': height,
            'annotations': annotations
        }
    
    @staticmethod
    def write_voc(internal_data, output_path):
        """Write internal format to PASCAL VOC XML"""
        root = ET.Element('annotation')
        
        # Add folder (optional)
        folder = ET.SubElement(root, 'folder')
        folder.text = os.path.basename(os.path.dirname(internal_data['image_path']))
        
        # Add filename
        filename = ET.SubElement(root, 'filename')
        filename.text = os.path.basename(internal_data['image_path'])
        
        # Add source (optional)
        source = ET.SubElement(root, 'source')
        database = ET.SubElement(source, 'database')
        database.text = 'Unknown'
        
        # Add size
        size = ET.SubElement(root, 'size')
        width = ET.SubElement(size, 'width')
        width.text = str(internal_data['image_width'])
        height = ET.SubElement(size, 'height')
        height.text = str(internal_data['image_height'])
        depth = ET.SubElement(size, 'depth')
        depth.text = '3'
        
        # Add segmented (optional)
        segmented = ET.SubElement(root, 'segmented')
        segmented.text = '0'
        
        # Add objects
        for ann in internal_data['annotations']:
            obj = ET.SubElement(root, 'object')
            
            name = ET.SubElement(obj, 'name')
            name.text = ann['label']
            
            pose = ET.SubElement(obj, 'pose')
            pose.text = 'Unspecified'
            
            truncated = ET.SubElement(obj, 'truncated')
            truncated.text = '1' if ann.get('truncated', False) else '0'
            
            difficult = ET.SubElement(obj, 'difficult')
            difficult.text = '1' if ann.get('difficult', False) else '0'
            
            bndbox = ET.SubElement(obj, 'bndbox')
            xmin = ET.SubElement(bndbox, 'xmin')
            xmin.text = str(ann['bbox'][0])
            ymin = ET.SubElement(bndbox, 'ymin')
            ymin.text = str(ann['bbox'][1])
            xmax = ET.SubElement(bndbox, 'xmax')
            xmax.text = str(ann['bbox'][0] + ann['bbox'][2])
            ymax = ET.SubElement(bndbox, 'ymax')
            ymax.text = str(ann['bbox'][1] + ann['bbox'][3])
        
        # Write with pretty printing
        xml_str = ET.tostring(root, encoding='unicode')
        dom = minidom.parseString(xml_str)
        pretty_xml = dom.toprettyxml(indent='  ')
        
        # Remove extra blank lines
        lines = [line for line in pretty_xml.split('\n') if line.strip()]
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    @staticmethod
    def write_yolo(internal_data, output_path, classes_list):
        """Write internal format to YOLO TXT"""
        # Build class to ID mapping
        class_to_id = {cls: idx for idx, cls in enumerate(classes_list)}
        
        width = internal_data['image_width']
        height = internal_data['image_height']
        
        lines = []
        skipped_labels = []
        for ann in internal_data['annotations']:
            label = ann['label']
            if label not in class_to_id:
                skipped_labels.append(label)
                print(f"Warning: Label '{label}' not in classes list, skipping")
                continue
            
            class_id = class_to_id[label]
            x, y, w, h = ann['bbox']
            
            # Convert to normalized center format
            x_center = (x + w / 2) / width
            y_center = (y + h / 2) / height
            w_norm = w / width
            h_norm = h / height
            
            lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}")
        
        # Only write file if there are valid annotations
        if lines:
            with open(output_path, 'w') as f:
                f.write('\n'.join(lines))
                f.write('\n')
            return True
        else:
            # Don't create empty file
            print(f"Skipping {os.path.basename(output_path)}: all labels not in classes list {skipped_labels}")
            return False
    
    @staticmethod
    def write_createml(internal_data, output_path):
        """Write internal format to CreateML JSON"""
        image_filename = os.path.basename(internal_data['image_path'])
        
        annotations = []
        for ann in internal_data['annotations']:
            x, y, w, h = ann['bbox']
            annotations.append({
                'label': ann['label'],
                'coordinates': {
                    'x': x,
                    'y': y,
                    'width': w,
                    'height': h
                }
            })
        
        data = [{
            'image': image_filename,
            'annotations': annotations
        }]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def write_coco(internal_data, output_path, categories_list):
        """Write internal format to COCO JSON"""
        # Build category map
        cat_map = {name: idx + 1 for idx, name in enumerate(categories_list)}
        
        coco_data = {
            'info': {
                'description': 'Converted from LabelCraft',
                'version': '1.0'
            },
            'licenses': [],
            'images': [{
                'id': 1,
                'file_name': os.path.basename(internal_data['image_path']),
                'width': internal_data['image_width'],
                'height': internal_data['image_height']
            }],
            'annotations': [],
            'categories': [{'id': idx + 1, 'name': name} for idx, name in enumerate(categories_list)]
        }
        
        ann_id = 1
        for ann in internal_data['annotations']:
            label = ann['label']
            if label not in cat_map:
                print(f"Warning: Label '{label}' not in categories list, skipping")
                continue
            
            x, y, w, h = ann['bbox']
            coco_data['annotations'].append({
                'id': ann_id,
                'image_id': 1,
                'category_id': cat_map[label],
                'bbox': [x, y, w, h],
                'area': w * h,
                'iscrowd': 0
            })
            ann_id += 1
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def write_csv(internal_data, output_path):
        """Write internal format to CSV"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax'])
            
            image_filename = os.path.basename(internal_data['image_path'])
            width = internal_data['image_width']
            height = internal_data['image_height']
            
            for ann in internal_data['annotations']:
                x, y, w, h = ann['bbox']
                writer.writerow([
                    image_filename,
                    width,
                    height,
                    ann['label'],
                    x,
                    y,
                    x + w,
                    y + h
                ])
    
    @staticmethod
    def write_labelcraft_json(internal_data, output_path):
        """Write internal format to LabelCraft JSON"""
        from datetime import datetime
        
        # Ensure .json extension
        if not output_path.lower().endswith('.json'):
            output_path += '.json'
        
        data = {
            'version': '1.0',
            'image': {
                'path': os.path.basename(internal_data['image_path']),
                'width': internal_data['image_width'],
                'height': internal_data['image_height'],
                'depth': 3
            },
            'annotations': [],
            'metadata': {
                'verified': False,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'tool': 'LabelCraft'
            }
        }
        
        # Add annotations
        for idx, ann in enumerate(internal_data['annotations'], 1):
            x, y, w, h = ann['bbox']
            annotation = {
                'id': idx,
                'label': ann['label'],
                'type': 'rectangle',
                'bbox': [int(x), int(y), int(x + w), int(y + h)],
                'points': [
                    [int(x), int(y)],
                    [int(x + w), int(y)],
                    [int(x + w), int(y + h)],
                    [int(x), int(y + h)]
                ],
                'difficult': ann.get('difficult', False),
                'occluded': False
            }
            data['annotations'].append(annotation)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    @staticmethod
    def convert(input_path, input_format, output_path, output_format, classes_list=None):
        """
        Convert annotation from one format to another
        
        Args:
            input_path: Path to input annotation file
            input_format: Input format ('voc', 'yolo', 'createml', 'coco', 'csv', 'json')
            output_path: Path to output annotation file
            output_format: Output format ('voc', 'yolo', 'createml', 'coco', 'csv')
            classes_list: List of class names (required for YOLO format)
            
        Returns:
            bool: True if conversion was successful and file was created
        """
        # Read input format to internal format
        readers = {
            'voc': AnnotationConverter.read_voc,
            'yolo': AnnotationConverter.read_yolo,
            'createml': AnnotationConverter.read_createml,
            'coco': AnnotationConverter.read_coco,
            'csv': AnnotationConverter.read_csv,
            'json': AnnotationConverter.read_labelcraft_json
        }
        
        if input_format not in readers:
            raise ValueError(f"Unsupported input format: {input_format}")
        
        # For YOLO input, classes_list is needed to convert class IDs to names
        if input_format == 'yolo':
            # Create a temporary classes file from classes_list
            if classes_list:
                print(f"[YOLO Conversion] Converting with {len(classes_list)} classes: {classes_list[:5]}...")
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                    for cls in classes_list:
                        f.write(cls + '\n')
                    temp_classes_file = f.name
                
                try:
                    internal_data = readers[input_format](input_path, classes_file=temp_classes_file)
                    print(f"[YOLO Conversion] Successfully read annotations from {os.path.basename(input_path)}")
                    if internal_data.get('annotations'):
                        sample_labels = [ann['label'] for ann in internal_data['annotations'][:3]]
                        print(f"[YOLO Conversion] Sample labels: {sample_labels}")
                finally:
                    # Clean up temporary file
                    if os.path.exists(temp_classes_file):
                        os.remove(temp_classes_file)
            else:
                # No classes provided, will use numeric IDs as labels
                print(f"Warning: No classes_list provided for YOLO input. Using numeric IDs as labels.")
                internal_data = readers[input_format](input_path)
        else:
            internal_data = readers[input_format](input_path)
        
        # Write internal format to output format
        writers = {
            'voc': AnnotationConverter.write_voc,
            'yolo': AnnotationConverter.write_yolo,
            'createml': AnnotationConverter.write_createml,
            'coco': AnnotationConverter.write_coco,
            'csv': AnnotationConverter.write_csv,
            'json': AnnotationConverter.write_labelcraft_json
        }
        
        if output_format not in writers:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # For YOLO and COCO, classes_list is required
        if output_format in ['yolo', 'coco'] and not classes_list:
            raise ValueError(f"classes_list is required for {output_format} format")
        
        if output_format == 'yolo':
            success = writers[output_format](internal_data, output_path, classes_list)
        elif output_format == 'coco':
            writers[output_format](internal_data, output_path, classes_list)
            success = True
        else:
            writers[output_format](internal_data, output_path)
            success = True
        
        return success
