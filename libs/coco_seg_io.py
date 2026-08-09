# Copyright (c) 2024-2026 LabelCraft
# COCO instance-segmentation dataset export

"""
Exports a COCO-style dataset with polygon ``segmentation`` fields:

  export_dir/
    images/
    annotations/
      instances_default.json
"""

from __future__ import annotations

import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

from libs.yolo_seg_io import seg_points_from_ann


def _polygon_area(points: Sequence[Sequence[float]]) -> float:
    """Shoelace formula (absolute value)."""
    n = len(points)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = float(points[i][0]), float(points[i][1])
        x2, y2 = float(points[(i + 1) % n][0]), float(points[(i + 1) % n][1])
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def _aabb_xywh(points: Sequence[Sequence[float]]) -> List[float]:
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    xmin, ymin = min(xs), min(ys)
    xmax, ymax = max(xs), max(ys)
    return [xmin, ymin, max(0.0, xmax - xmin), max(0.0, ymax - ymin)]


def flatten_segmentation(points: Sequence[Sequence[float]]) -> List[float]:
    """COCO polygon: [x1,y1,x2,y2,...] in absolute pixels."""
    flat: List[float] = []
    for p in points:
        flat.append(float(p[0]))
        flat.append(float(p[1]))
    return flat


def export_coco_seg_dataset(
    items: Sequence[Dict[str, Any]],
    output_dir: str,
    class_list: Sequence[str],
    copy_images: bool = True,
    ann_filename: str = 'instances_default.json',
) -> str:
    """
    Build a multi-image COCO segmentation JSON.

    Each item:
      {
        'image_path': str,
        'annotations': [ {label, type, points=[[x,y],...]}, ... ]
      }
    """
    images_dir = os.path.join(output_dir, 'images')
    ann_dir = os.path.join(output_dir, 'annotations')
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(ann_dir, exist_ok=True)

    cat_map = {name: idx + 1 for idx, name in enumerate(class_list)}
    categories = [
        {'id': idx + 1, 'name': name, 'supercategory': 'none'}
        for idx, name in enumerate(class_list)
    ]

    coco = {
        'info': {
            'description': 'LabelCraft COCO Segmentation Export',
            'url': '',
            'version': '1.0',
            'year': datetime.now().year,
            'contributor': 'LabelCraft',
            'date_created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        },
        'licenses': [],
        'images': [],
        'annotations': [],
        'categories': categories,
    }

    ann_id = 1
    img_id = 1
    for item in items:
        image_path = item.get('image_path') or ''
        if not image_path or not os.path.isfile(image_path):
            continue

        from PySide6.QtGui import QImage
        img = QImage(image_path)
        if img.isNull():
            continue
        width, height = img.width(), img.height()
        file_name = os.path.basename(image_path)
        dst_img = os.path.join(images_dir, file_name)
        if copy_images:
            if os.path.abspath(image_path) != os.path.abspath(dst_img):
                shutil.copy2(image_path, dst_img)

        coco['images'].append({
            'id': img_id,
            'file_name': file_name,
            'width': width,
            'height': height,
            'license': 0,
            'date_captured': '',
        })

        for ann in item.get('annotations', []):
            label = ann.get('label', '')
            if label not in cat_map:
                # Allow late-add so sparse class lists still work
                cat_map[label] = len(cat_map) + 1
                coco['categories'].append({
                    'id': cat_map[label],
                    'name': label,
                    'supercategory': 'none',
                })
            pts = ann.get('points')
            if not pts or len(pts) < 3:
                pts = seg_points_from_ann(ann)
            if not pts or len(pts) < 3:
                continue
            bbox = _aabb_xywh(pts)
            area = _polygon_area(pts)
            if area <= 0:
                area = float(bbox[2] * bbox[3])
            coco['annotations'].append({
                'id': ann_id,
                'image_id': img_id,
                'category_id': cat_map[label],
                'segmentation': [flatten_segmentation(pts)],
                'bbox': bbox,
                'area': area,
                'iscrowd': 0,
            })
            ann_id += 1
        img_id += 1

    # Sync category list order by id
    coco['categories'] = sorted(coco['categories'], key=lambda c: c['id'])

    out_json = os.path.join(ann_dir, ann_filename)
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump(coco, f, indent=2, ensure_ascii=False)
    return out_json
