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
                        
                        ann = {
                            'label': label,
                            'bbox': [x, y, w_abs, h_abs],
                            'bbox_xyxy': [x, y, x + w_abs, y + h_abs],
                            'difficult': False,
                            'truncated': False
                        }
                        # YOLO-Pose: remaining tokens are keypoints
                        rest = parts[5:]
                        if len(rest) >= 2 and len(rest) % 3 == 0:
                            kpts = []
                            for i in range(0, len(rest), 3):
                                kx = float(rest[i]) * width
                                ky = float(rest[i + 1]) * height
                                kv = int(float(rest[i + 2]))
                                kpts.append([kx, ky, kv])
                            ann['keypoints'] = kpts
                            ann['type'] = 'pose'
                        annotations.append(ann)
        
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
    def _aabb_from_points(points):
        """Return (xmin, ymin, xmax, ymax) from any non-empty point list."""
        xs = [float(p[0]) for p in points]
        ys = [float(p[1]) for p in points]
        return min(xs), min(ys), max(xs), max(ys)

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
            points = ann.get('points') or []
            ann_type = ann.get('type', 'rectangle')

            # AABB: prefer bbox, else extents of all points (polygon N>=1, ellipse, etc.)
            if 'bbox' in ann and ann['bbox']:
                bbox = ann['bbox']  # [xmin, ymin, xmax, ymax]
                xmin, ymin, xmax, ymax = (
                    float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3])
                )
            elif len(points) >= 1:
                xmin, ymin, xmax, ymax = AnnotationConverter._aabb_from_points(points)
            else:
                print(f"  Skipping annotation (no bbox or points): {ann}")
                continue

            x, y = xmin, ymin
            w, h = max(0.0, xmax - xmin), max(0.0, ymax - ymin)
            print(f"  Annotation: {label}, type={ann_type}, bbox=[{x},{y},{w},{h}]")

            if ann.get('keypoints'):
                ann_type = ann.get('type') or 'pose'

            item = {
                'label': label,
                'bbox': [int(round(x)), int(round(y)), int(round(w)), int(round(h))],
                'bbox_xyxy': [
                    int(round(xmin)), int(round(ymin)),
                    int(round(xmax)), int(round(ymax)),
                ],
                'difficult': ann.get('difficult', False),
                'truncated': ann.get('occluded', False),
                'type': ann_type,
                'points': [[float(p[0]), float(p[1])] for p in points],
            }
            if ann.get('keypoints'):
                item['keypoints'] = ann['keypoints']
            if ann.get('keypoint_names'):
                item['keypoint_names'] = ann['keypoint_names']
            if ann.get('skeleton'):
                item['skeleton'] = ann['skeleton']
            if ann.get('line_color') is not None:
                item['line_color'] = ann['line_color']
            if ann.get('fill_color') is not None:
                item['fill_color'] = ann['fill_color']
            if ann.get('line_width') is not None:
                item['line_width'] = ann['line_width']
            annotations.append(item)
        
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
        """
        Write YOLO Detect TXT (class cx cy w h only).

        Polygon / ellipse / circle / pose boxes are collapsed to axis-aligned
        bounding boxes. Keypoints are intentionally NOT written (use YOLO-Pose
        export for pose rows). YOLO-seg is out of scope for now.
        """
        # Build class to ID mapping
        class_to_id = {cls: idx for idx, cls in enumerate(classes_list)}
        
        width = max(1, int(internal_data['image_width']))
        height = max(1, int(internal_data['image_height']))
        
        lines = []
        skipped_labels = []
        for ann in internal_data['annotations']:
            label = ann['label']
            if label not in class_to_id:
                skipped_labels.append(label)
                print(f"Warning: Label '{label}' not in classes list, skipping")
                continue
            
            class_id = class_to_id[label]
            # Prefer xyxy; fall back to xywh bbox; then points extents
            if ann.get('bbox_xyxy') and len(ann['bbox_xyxy']) >= 4:
                xmin, ymin, xmax, ymax = [float(v) for v in ann['bbox_xyxy'][:4]]
                w = max(0.0, xmax - xmin)
                h = max(0.0, ymax - ymin)
                x, y = xmin, ymin
            elif ann.get('bbox') and len(ann['bbox']) >= 4:
                x, y, w, h = [float(v) for v in ann['bbox'][:4]]
            elif ann.get('points'):
                xmin, ymin, xmax, ymax = AnnotationConverter._aabb_from_points(ann['points'])
                x, y = xmin, ymin
                w, h = max(0.0, xmax - xmin), max(0.0, ymax - ymin)
            else:
                continue

            if w <= 0 or h <= 0 or width <= 0 or height <= 0:
                continue

            # Convert to normalized center format
            x_center = (x + w / 2) / width
            y_center = (y + h / 2) / height
            w_norm = w / width
            h_norm = h / height
            
            # Detect format only — never append keypoints here
            line = f"{class_id} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}"
            lines.append(line)
        
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
    def write_yolo_pose(internal_data, output_path, classes_list, kpt_shape=(3, 3)):
        """Write internal format to YOLO-Pose TXT (alias with explicit kpt padding)."""
        from libs.yolo_pose_io import annotations_to_pose_txt
        return annotations_to_pose_txt(
            internal_data.get('annotations', []),
            internal_data['image_width'],
            internal_data['image_height'],
            classes_list,
            kpt_shape,
            output_path,
        )

    @staticmethod
    def write_yolo_obb(internal_data, output_path, classes_list):
        """Write internal format to YOLO-OBB TXT (cls + 4 normalized corners).

        Only annotations with type=='obb' and >=4 points are written.
        Rectangles / pose / polygons are skipped (use Detect / Pose / Seg).
        """
        from libs.yolo_obb_io import annotations_to_obb_txt
        return annotations_to_obb_txt(
            internal_data.get('annotations', []),
            internal_data['image_width'],
            internal_data['image_height'],
            classes_list,
            output_path,
        )

    @staticmethod
    def write_yolo_seg(internal_data, output_path, classes_list):
        """Write internal format to YOLO-Seg TXT (cls + normalized polygon)."""
        from libs.yolo_seg_io import annotations_to_seg_txt
        return annotations_to_seg_txt(
            internal_data.get('annotations', []),
            internal_data['image_width'],
            internal_data['image_height'],
            classes_list,
            output_path,
        )
    
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
    def write_coco(internal_data, output_path, categories_list, include_segmentation=True):
        """Write internal format to COCO JSON.

        When ``include_segmentation`` is True and the annotation has a usable
        polygon (polygon / obb / ellipse / circle), a COCO ``segmentation``
        field is written. Otherwise only bbox is exported.
        """
        from libs.yolo_seg_io import seg_points_from_ann
        from libs.coco_seg_io import flatten_segmentation, _polygon_area

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
            'categories': [
                {'id': idx + 1, 'name': name, 'supercategory': 'none'}
                for idx, name in enumerate(categories_list)
            ]
        }
        
        ann_id = 1
        for ann in internal_data['annotations']:
            label = ann['label']
            if label not in cat_map:
                print(f"Warning: Label '{label}' not in categories list, skipping")
                continue
            
            x, y, w, h = ann['bbox']
            item = {
                'id': ann_id,
                'image_id': 1,
                'category_id': cat_map[label],
                'bbox': [x, y, w, h],
                'area': w * h,
                'iscrowd': 0
            }
            if include_segmentation:
                pts = seg_points_from_ann(ann)
                if pts and len(pts) >= 3:
                    item['segmentation'] = [flatten_segmentation(pts)]
                    area = _polygon_area(pts)
                    if area > 0:
                        item['area'] = area
            coco_data['annotations'].append(item)
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
        """Write internal format to LabelCraft JSON (preserves type/points/styles)."""
        from datetime import datetime
        
        # Ensure .json extension
        if not output_path.lower().endswith('.json'):
            output_path += '.json'
        
        data = {
            'version': '1.1',
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
            has_kpts = bool(ann.get('keypoints'))
            ann_type = ann.get('type') or ('pose' if has_kpts else 'rectangle')
            xmin, ymin, xmax, ymax = int(x), int(y), int(x + w), int(y + h)

            # Prefer original vertices (polygon / OBB); else AABB 4 corners
            src_pts = ann.get('points') or []
            if ann_type in ('polygon', 'obb') and len(src_pts) >= (3 if ann_type == 'polygon' else 4):
                points = [[int(round(p[0])), int(round(p[1]))] for p in src_pts]
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                xmin, ymin, xmax, ymax = min(xs), min(ys), max(xs), max(ys)
            elif len(src_pts) >= 2 and ann_type in ('ellipse', 'circle', 'rectangle', 'pose'):
                points = [[int(round(p[0])), int(round(p[1]))] for p in src_pts]
            else:
                points = [
                    [xmin, ymin],
                    [xmax, ymin],
                    [xmax, ymax],
                    [xmin, ymax],
                ]

            annotation = {
                'id': idx,
                'label': ann['label'],
                'type': ann_type,
                'bbox': [xmin, ymin, xmax, ymax],
                'points': points,
                'difficult': ann.get('difficult', False),
                'occluded': bool(ann.get('truncated', False)),
            }
            if ann.get('line_color') is not None:
                annotation['line_color'] = list(ann['line_color'])
            if ann.get('fill_color') is not None:
                annotation['fill_color'] = list(ann['fill_color'])
            if ann.get('line_width') is not None:
                annotation['line_width'] = float(ann['line_width'])
            if has_kpts:
                kpts = []
                for kp in ann['keypoints']:
                    if isinstance(kp, dict):
                        kpts.append([
                            float(kp.get('x', 0)),
                            float(kp.get('y', 0)),
                            int(kp.get('v', 2)),
                        ])
                    else:
                        kpts.append([
                            float(kp[0]),
                            float(kp[1]),
                            int(kp[2]) if len(kp) > 2 else 2,
                        ])
                annotation['keypoints'] = kpts
                if ann.get('keypoint_names'):
                    annotation['keypoint_names'] = list(ann['keypoint_names'])
                if ann.get('skeleton'):
                    annotation['skeleton'] = [list(e) for e in ann['skeleton']]
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
            'yolo_obb': AnnotationConverter.write_yolo_obb,
            'yolo_seg': AnnotationConverter.write_yolo_seg,
            'createml': AnnotationConverter.write_createml,
            'coco': AnnotationConverter.write_coco,
            'csv': AnnotationConverter.write_csv,
            'json': AnnotationConverter.write_labelcraft_json
        }
        
        if output_format not in writers:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        # For YOLO and COCO, classes_list is required
        if output_format in ['yolo', 'yolo_obb', 'yolo_seg', 'coco'] and not classes_list:
            raise ValueError(f"classes_list is required for {output_format} format")
        
        if output_format in ('yolo', 'yolo_obb', 'yolo_seg'):
            success = writers[output_format](internal_data, output_path, classes_list)
        elif output_format == 'coco':
            writers[output_format](internal_data, output_path, classes_list)
            success = True
        else:
            writers[output_format](internal_data, output_path)
            success = True
        
        return success
