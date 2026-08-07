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
    
    def add_bnd_box(self, xmin, ymin, xmax, ymax, label, difficult=0, keypoints=None,
                    shape_type=None, keypoint_names=None, skeleton=None,
                    line_color=None, fill_color=None, line_width=None):
        """Add a bounding box or pose annotation"""
        has_kpts = bool(keypoints)
        ann_type = shape_type or ('pose' if has_kpts else 'rectangle')
        shape = {
            'label': label,
            'type': ann_type,
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
        if line_color is not None:
            shape['line_color'] = list(line_color)
        if fill_color is not None:
            shape['fill_color'] = list(fill_color)
        if line_width is not None:
            shape['line_width'] = float(line_width)
        if has_kpts:
            shape['keypoints'] = []
            for kp in keypoints:
                if isinstance(kp, dict):
                    shape['keypoints'].append([
                        float(kp.get('x', 0)),
                        float(kp.get('y', 0)),
                        int(kp.get('v', 0)),
                    ])
                else:
                    shape['keypoints'].append([
                        float(kp[0]),
                        float(kp[1]),
                        int(kp[2]) if len(kp) > 2 else 2,
                    ])
            if keypoint_names:
                shape['keypoint_names'] = list(keypoint_names)
            if skeleton:
                shape['skeleton'] = [list(e) for e in skeleton]
        self.shapes.append(shape)
    
    def add_polygon(self, points, label, difficult=0,
                    line_color=None, fill_color=None, line_width=None):
        """Add a polygon annotation (keeps all vertices; bbox = axis-aligned bounds)."""
        pts = [[int(round(p[0])), int(round(p[1]))] for p in points]
        if not pts:
            return
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        shape = {
            'label': label,
            'type': 'polygon',
            'bbox': [min(xs), min(ys), max(xs), max(ys)],
            'points': pts,
            'difficult': bool(difficult),
            'occluded': False
        }
        if line_color is not None:
            shape['line_color'] = list(line_color)
        if fill_color is not None:
            shape['fill_color'] = list(fill_color)
        if line_width is not None:
            shape['line_width'] = float(line_width)
        self.shapes.append(shape)

    def add_ellipse(self, xmin, ymin, xmax, ymax, label, difficult=0,
                    shape_type='ellipse', line_color=None, fill_color=None,
                    line_width=None):
        """Add an ellipse/circle (axis-aligned bounding box + type)."""
        ann_type = shape_type if shape_type in ('ellipse', 'circle') else 'ellipse'
        shape = {
            'label': label,
            'type': ann_type,
            'bbox': [int(xmin), int(ymin), int(xmax), int(ymax)],
            'points': [
                [int(xmin), int(ymin)],
                [int(xmax), int(ymin)],
                [int(xmax), int(ymax)],
                [int(xmin), int(ymax)],
            ],
            'difficult': bool(difficult),
            'occluded': False,
        }
        if line_color is not None:
            shape['line_color'] = list(line_color)
        if fill_color is not None:
            shape['fill_color'] = list(fill_color)
        if line_width is not None:
            shape['line_width'] = float(line_width)
        self.shapes.append(shape)
    
    def write(self, target_file=None):
        """Write annotations to JSON file"""
        if target_file is None:
            target_file = self.filename
        
        # Ensure .json extension
        if not target_file.lower().endswith('.json'):
            target_file += '.json'
        
        data = {
            'version': '1.1',
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

            if 'keypoints' in shape:
                annotation['keypoints'] = shape['keypoints']
            if 'keypoint_names' in shape:
                annotation['keypoint_names'] = shape['keypoint_names']
            if 'skeleton' in shape:
                annotation['skeleton'] = shape['skeleton']
            if 'line_color' in shape:
                annotation['line_color'] = shape['line_color']
            if 'fill_color' in shape:
                annotation['fill_color'] = shape['fill_color']
            if 'line_width' in shape:
                annotation['line_width'] = shape['line_width']
            
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
                        'points': ann.get('points', []),
                        'type': ann.get('type', 'rectangle'),
                        'keypoints': ann.get('keypoints', []),
                        'keypoint_names': ann.get('keypoint_names', []),
                        'skeleton': ann.get('skeleton', []),
                        'line_color': ann.get('line_color'),
                        'fill_color': ann.get('fill_color'),
                        'line_width': ann.get('line_width'),
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

    def get_labelcraft_tuples(self):
        """
        Return shapes as load_labels-compatible tuples:
          (label, points, line_color, fill_color, difficult, keypoints, shape_type,
           keypoint_names, skeleton, line_width)
        """
        tuples = []
        for s in self.shapes:
            points = [(float(p[0]), float(p[1])) for p in s.get('points', [])]
            kpts = []
            for kp in s.get('keypoints') or []:
                if isinstance(kp, dict):
                    kpts.append((float(kp['x']), float(kp['y']), int(kp.get('v', 2))))
                else:
                    kpts.append((float(kp[0]), float(kp[1]), int(kp[2]) if len(kp) > 2 else 2))
            lc = s.get('line_color')
            fc = s.get('fill_color')
            tuples.append((
                s.get('label', ''),
                points,
                tuple(lc) if lc else None,
                tuple(fc) if fc else None,
                s.get('difficult', False),
                kpts,
                s.get('type', 'pose' if kpts else 'rectangle'),
                s.get('keypoint_names') or [],
                s.get('skeleton') or [],
                s.get('line_width'),
            ))
        return tuples
