# compiler_scanner.py
import os
import ast

class DependencyScanner:
    @staticmethod
    def scan(directory):
        imports = set()
        exclude_dirs = {'venv', '.venv', 'env', '.env', '__pycache__', 'build', 'dist', '.git', '.python_ide_venvs'}
        
        for root_dir, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                if file.endswith('.py'):
                    try:
                        with open(os.path.join(root_dir, file), 'r', encoding='utf-8') as f:
                            tree = ast.parse(f.read())
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    imports.add(alias.name.split('.')[0])
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    imports.add(node.module.split('.')[0])
                    except Exception:
                        pass
        return list(imports)