"""
Project management module for LabelCraft
Manages project data and state
"""
import os
import json
from datetime import datetime

# Primary short extension; legacy long form remains readable/writable.
PROJECT_EXT = '.lbc'
PROJECT_EXT_LEGACY = '.labelcraft'
PROJECT_EXTS = (PROJECT_EXT, PROJECT_EXT_LEGACY)


def is_project_file(path):
    """True if path uses a known LabelCraft project extension."""
    if not path:
        return False
    lower = path.lower()
    return any(lower.endswith(ext) for ext in PROJECT_EXTS)


def ensure_project_extension(path, prefer_primary=True):
    """
    Ensure path has a project extension.
    - Already .lbc / .labelcraft → unchanged (preserves legacy files)
    - Otherwise append primary .lbc (or legacy if prefer_primary=False)
    """
    if not path:
        return path
    if is_project_file(path):
        return path
    return path + (PROJECT_EXT if prefer_primary else PROJECT_EXT_LEGACY)


def project_file_filter():
    """QFileDialog filter string (open/save)."""
    return (
        f'LabelCraft Project (*{PROJECT_EXT} *{PROJECT_EXT_LEGACY});;'
        f'LabelCraft Project (*{PROJECT_EXT});;'
        f'LabelCraft Project Legacy (*{PROJECT_EXT_LEGACY});;'
        'All Files (*)'
    )


class Project:
    """Represents a LabelCraft annotation project"""
    
    def __init__(self, name=None, project_dir=None, labels=None, format='PASCAL_VOC', version='2.0',
                 task='detect', kpt_shape=None, keypoint_names=None, flip_idx=None, skeleton=None):
        self.name = name or 'Untitled Project'
        self.version = version
        self.created_at = datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
        self.project_dir = project_dir or ''  # Project directory (contains project file and annotations)
        self.annotation_dir = ''  # Will be set to project_dir/annotations
        self.labels = labels or []
        self.format = format  # PASCAL_VOC, YOLO, CREATE_ML, LABELCRAFT_JSON
        self.last_opened_image = None
        self.project_file = None  # Path to .lbc / .labelcraft file

        # Task: 'detect' (bbox) or 'pose' (bbox + keypoints)
        self.task = task or 'detect'
        self.kpt_shape = list(kpt_shape) if kpt_shape else [0, 3]
        self.keypoint_names = list(keypoint_names) if keypoint_names else []
        self.flip_idx = list(flip_idx) if flip_idx is not None else list(range(len(self.keypoint_names)))
        self.skeleton = [list(e) for e in skeleton] if skeleton else []
        
        # Auto-set annotation directory relative to project directory
        if self.project_dir:
            self.annotation_dir = os.path.join(self.project_dir, 'annotations')

    def is_pose_task(self):
        return self.task == 'pose' and int(self.kpt_shape[0] or 0) > 0

    def pose_config_dict(self):
        return {
            'task': self.task,
            'kpt_shape': list(self.kpt_shape),
            'keypoint_names': list(self.keypoint_names),
            'flip_idx': list(self.flip_idx),
            'skeleton': [list(e) for e in self.skeleton],
        }
        
    def save(self, file_path=None):
        """Save project to .lbc (or keep existing .labelcraft path)."""
        if file_path:
            self.project_file = file_path
        
        if not self.project_file:
            raise ValueError("No project file path specified")
        
        # Keep legacy .labelcraft if already used; new files default to .lbc
        self.project_file = ensure_project_extension(self.project_file, prefer_primary=True)
        
        project_data = {
            'name': self.name,
            'version': self.version,
            'created_at': self.created_at,
            'last_modified': datetime.now().isoformat(),
            'project_dir': self.project_dir,
            'annotation_dir': self.annotation_dir,
            'labels': self.labels,
            'format': self.format,
            'last_opened_image': self.last_opened_image,
            'task': self.task,
            'kpt_shape': list(self.kpt_shape),
            'keypoint_names': list(self.keypoint_names),
            'flip_idx': list(self.flip_idx),
            'skeleton': [list(e) for e in self.skeleton],
        }
        
        with open(self.project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        self.last_modified = project_data['last_modified']
        return self.project_file
    
    @staticmethod
    def load(file_path):
        """Load project from .lbc or legacy .labelcraft file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Project file not found: {file_path}")
        if not is_project_file(file_path):
            # Still try load — user may pick via "All Files"
            pass
        
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        project = Project(
            name=project_data.get('name', 'Untitled Project'),
            project_dir=project_data.get('project_dir', ''),
            labels=project_data.get('labels', []),
            format=project_data.get('format', 'PASCAL_VOC'),
            version=project_data.get('version', '2.0'),
            task=project_data.get('task', 'detect'),
            kpt_shape=project_data.get('kpt_shape'),
            keypoint_names=project_data.get('keypoint_names'),
            flip_idx=project_data.get('flip_idx'),
            skeleton=project_data.get('skeleton'),
        )
        
        # Restore annotation_dir from saved data (override auto-generated path)
        if 'annotation_dir' in project_data and project_data['annotation_dir']:
            project.annotation_dir = project_data['annotation_dir']
        
        project.created_at = project_data.get('created_at', datetime.now().isoformat())
        project.last_modified = project_data.get('last_modified', datetime.now().isoformat())
        project.last_opened_image = project_data.get('last_opened_image')
        project.project_file = file_path
        
        return project
    
    def update_last_image(self, image_path):
        """Update the last opened image path"""
        self.last_opened_image = image_path
        self.last_modified = datetime.now().isoformat()
    
    def add_label(self, label):
        """Add a new label if it doesn't exist"""
        if label and label not in self.labels:
            self.labels.append(label)
            self.last_modified = datetime.now().isoformat()
            return True
        return False
    
    def remove_label(self, label):
        """Remove a label if it exists"""
        if label in self.labels:
            self.labels.remove(label)
            self.last_modified = datetime.now().isoformat()
            return True
        return False
    
    def is_valid(self):
        """Check if project has minimum required information"""
        return bool(self.name and self.project_dir)
    
    def get_info_summary(self, tr_func=None):
        """Get a human-readable summary of the project
        
        Args:
            tr_func: Optional translation function. If not provided, uses English labels.
        """
        # Truncate labels for display
        if len(self.labels) <= 5:
            labels_str = ', '.join(self.labels)
        else:
            labels_str = ', '.join(self.labels[:5]) + '...'
        
        # Use translation function if provided, otherwise use English
        if tr_func:
            name_label = tr_func('projectName')
            location_label = tr_func('projectLocation')
            annotation_label = tr_func('annotationDir')
            label_count_label = tr_func('labelCount')
            format_label = tr_func('outputFormat')
            not_set_label = tr_func('notSet')
        else:
            name_label = 'Project Name'
            location_label = 'Location'
            annotation_label = 'Annotation Directory'
            label_count_label = 'Labels'
            format_label = 'Output Format'
            not_set_label = 'Not Set'
        
        task_line = f"Task: {self.task}"
        if self.is_pose_task():
            kpt_names = ', '.join(self.keypoint_names) if self.keypoint_names else str(self.kpt_shape[0])
            task_line += f" (keypoints: {kpt_names})"

        return (
            f"{name_label}: {self.name}\n"
            f"{location_label}: {self.project_dir}\n"
            f"{annotation_label}: {self.annotation_dir or not_set_label}\n"
            f"{label_count_label}: {len(self.labels)} ({labels_str})\n"
            f"{format_label}: {self.format}\n"
            f"{task_line}"
        )


class RecentProjectsManager:
    """Manage recent projects history"""
    
    RECENT_PROJECTS_FILE = 'recent_projects.json'
    MAX_RECENT_PROJECTS = 10
    
    @staticmethod
    def _get_history_file_path():
        """Get the path to recent projects history file in current program directory"""
        import os
        # Store in the same directory as the running program
        program_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level to project root (libs -> root)
        project_root = os.path.dirname(program_dir)
        return os.path.join(project_root, RecentProjectsManager.RECENT_PROJECTS_FILE)
    
    @staticmethod
    def load_recent_projects():
        """Load recent projects list from history file"""
        history_file = RecentProjectsManager._get_history_file_path()
        if not os.path.exists(history_file):
            return []
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                recent_projects = json.load(f)
            return recent_projects
        except Exception as e:
            print(f'Error loading recent projects: {e}')
            return []
    
    @staticmethod
    def save_recent_projects(recent_projects):
        """Save recent projects list to history file"""
        history_file = RecentProjectsManager._get_history_file_path()
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(recent_projects, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f'Error saving recent projects: {e}')
    
    @staticmethod
    def add_project(project_path, project_name=None):
        """Add a project to recent projects list
        
        Args:
            project_path: Path to the .lbc / .labelcraft file
            project_name: Optional project name (will extract from path if not provided)
        """
        recent_projects = RecentProjectsManager.load_recent_projects()
        
        # Extract project name from path if not provided
        if not project_name:
            project_name = os.path.basename(os.path.dirname(project_path))
        
        # Remove if already exists (to move to top)
        recent_projects = [p for p in recent_projects if p['path'] != project_path]
        
        # Add to the beginning
        recent_projects.insert(0, {
            'name': project_name,
            'path': project_path,
            'opened_at': datetime.now().isoformat()
        })
        
        # Keep only MAX_RECENT_PROJECTS items
        recent_projects = recent_projects[:RecentProjectsManager.MAX_RECENT_PROJECTS]
        
        # Save updated list
        RecentProjectsManager.save_recent_projects(recent_projects)
    
    @staticmethod
    def remove_project(project_path):
        """Remove a project from recent projects list"""
        recent_projects = RecentProjectsManager.load_recent_projects()
        recent_projects = [p for p in recent_projects if p['path'] != project_path]
        RecentProjectsManager.save_recent_projects(recent_projects)
