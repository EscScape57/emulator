import json
import base64
import os

class VFSNode:
    def __init__(self, name, type, content=None, children=None):
        self.name = name
        self.type = type  # 'directory' or 'file'
        self.content = content # For files, base64 encoded string
        self.children = children if children is not None else {} # For directories

    def to_dict(self):
        if self.type == 'file':
            return {
                'name': self.name,
                'type': self.type,
                'content': self.content
            }
        else: # directory
            return {
                'name': self.name,
                'type': self.type,
                'children': {name: node.to_dict() for name, node in self.children.items()}
            }

    @staticmethod
    def from_dict(data):
        name = data['name']
        type = data['type']
        if type == 'file':
            content = data.get('content')
            return VFSNode(name, type, content=content)
        else: # directory
            children_data = data.get('children', {})
            children = {name: VFSNode.from_dict(child_data) for name, child_data in children_data.items()}
            return VFSNode(name, type, children=children)

class VFS:
    def __init__(self):
        self.root = VFSNode('/', 'directory')
        self.current_path = ['/']

    def load_from_json(self, json_path):
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"VFS file not found: {json_path}")
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            self.root = VFSNode.from_dict(data)
            self.current_path = ['/'] # Reset current path on load
        except json.JSONDecodeError:
            raise ValueError(f"Invalid VFS JSON format: {json_path}")
        except Exception as e:
            raise RuntimeError(f"Error loading VFS: {e}")

    def create_default_vfs(self):
        # Создаем минимальную VFS по умолчанию
        self.root = VFSNode('/', 'directory')
        self.root.children['home'] = VFSNode('home', 'directory')
        self.root.children['home'].children['user'] = VFSNode('user', 'directory')
        self.root.children['home'].children['user'].children['hello.txt'] = VFSNode('hello.txt', 'file', content=base64.b64encode(b'Hello, VFS!').decode('utf-8'))
        self.root.children['bin'] = VFSNode('bin', 'directory')
        self.root.children['bin'].children['echo'] = VFSNode('echo', 'file', content=base64.b64encode(b'#!/bin/bash\necho "This is a VFS echo!"').decode('utf-8'))
        self.current_path = ['/']

    def get_node(self, path_parts):
        current_node = self.root
        for part in path_parts:
            if part == '/' and current_node == self.root: # Handle root special case
                continue
            if part not in current_node.children:
                return None
            current_node = current_node.children[part]
        return current_node

    def get_current_node(self):
        return self.get_node(self.current_path)

    def list_directory(self, path=None):
        target_path_parts = self._resolve_path(path)
        node = self.get_node(target_path_parts)
        if node is None:
            return None, "Директория не найдена."
        if node.type == 'file':
            return None, f"{'/'.join(target_path_parts)} является файлом, а не директорией."
        return sorted(node.children.keys()), None

    def change_directory(self, path):
        resolved_path_parts = self._resolve_path(path)
        node = self.get_node(resolved_path_parts)
        if node is None:
            return False, "Директория не найдена."
        if node.type == 'file':
            return False, f"{path} является файлом, а не директорией."
        self.current_path = resolved_path_parts
        return True, None

    def _resolve_path(self, path):
        if path is None or path == '':
            return self.current_path

        if path.startswith('/'):
            resolved_parts = ['/']
        else:
            resolved_parts = list(self.current_path)
        
        components = [comp for comp in path.split('/') if comp]

        for comp in components:
            if comp == '.':
                continue
            elif comp == '..':
                if len(resolved_parts) > 1: # Don't go above root
                    resolved_parts.pop()
            else:
                resolved_parts.append(comp)
        
        # Ensure root is always represented as ['/']
        if not resolved_parts:
            return ['/']
        if len(resolved_parts) == 1 and resolved_parts[0] == '':
            return ['/']
        
        return resolved_parts

    def get_absolute_path(self):
        return '/' + '/'.join(self.current_path[1:])
