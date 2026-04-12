"""
Project management module for LabelCraft
Manages project data and state
"""
import os
import json
from datetime import datetime


class Project:
    """Represents a LabelCraft annotation project"""
    
    def __init__(self, name=None, project_dir=None, labels=None, format='PASCAL_VOC', version='2.0'):
        self.name = name or 'Untitled Project'
        self.version = version
        self.created_at = datetime.now().isoformat()
        self.last_modified = datetime.now().isoformat()
        self.project_dir = project_dir or ''  # Project directory (contains project file and annotations)
        self.annotation_dir = ''  # Will be set to project_dir/annotations
        self.labels = labels or []
        self.format = format  # PASCAL_VOC, YOLO, CREATE_ML
        self.last_opened_image = None
        self.project_file = None  # Path to .labelcraft file
        
        # Auto-set annotation directory relative to project directory
        if self.project_dir:
            self.annotation_dir = os.path.join(self.project_dir, 'annotations')
        
    def save(self, file_path=None):
        """Save project to .labelcraft file"""
        if file_path:
            self.project_file = file_path
        
        if not self.project_file:
            raise ValueError("No project file path specified")
        
        # Ensure file has .labelcraft extension
        if not self.project_file.endswith('.labelcraft'):
            self.project_file += '.labelcraft'
        
        project_data = {
            'name': self.name,
            'version': self.version,
            'created_at': self.created_at,
            'last_modified': datetime.now().isoformat(),
            'project_dir': self.project_dir,
            'annotation_dir': self.annotation_dir,
            'labels': self.labels,
            'format': self.format,
            'last_opened_image': self.last_opened_image
        }
        
        with open(self.project_file, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, ensure_ascii=False)
        
        self.last_modified = project_data['last_modified']
        return self.project_file
    
    @staticmethod
    def load(file_path):
        """Load project from .labelcraft file"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Project file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        project = Project(
            name=project_data.get('name', 'Untitled Project'),
            project_dir=project_data.get('project_dir', ''),
            labels=project_data.get('labels', []),
            format=project_data.get('format', 'PASCAL_VOC'),
            version=project_data.get('version', '2.0')
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
    
    def get_info_summary(self):
        """Get a human-readable summary of the project"""
        return (
            f"Project: {self.name}\n"
            f"Location: {self.project_dir}\n"
            f"Annotations: {self.annotation_dir}\n"
            f"Labels: {len(self.labels)} ({', '.join(self.labels[:5])}{'...' if len(self.labels) > 5 else ''})\n"
            f"Format: {self.format}"
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
            project_path: Path to the .labelcraft file
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
