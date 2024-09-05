import os
import re
from typing import List, Tuple, Dict
from tree_sitter_language_pack import get_language, get_parser

# Map file extensions to languages
LANGUAGE_MAP = {
    'py': 'python', 'js': 'javascript', 'ts': 'typescript', 'tsx': 'typescript',
    'java': 'java', 'c': 'c', 'cpp': 'cpp', 'cs': 'c_sharp', 'go': 'go',
    'rb': 'ruby', 'php': 'php', 'swift': 'swift', 'rs': 'rust', 'kt': 'kotlin',
    'scala': 'scala', 'lua': 'lua', 'sh': 'bash', 'html': 'html', 'css': 'css',
    'scss': 'css', 'sql': 'sql', 'md': 'markdown',
}

# Dictionary to store loaded languages and parsers
loaded_languages: Dict[str, Tuple] = {}

def get_language_and_parser(file_extension: str, io) -> Tuple:
    language_name = LANGUAGE_MAP.get(file_extension.lower(), 'python')
    if language_name not in loaded_languages:
        try:
            language = get_language(language_name)
            parser = get_parser(language_name)
            loaded_languages[language_name] = (language, parser)
        except Exception:
            io.console.print(f"Warning: Language '{language_name}' not supported. Falling back to Python.", style="bold dark_goldenrod")
            language_name = 'python'
            if 'python' not in loaded_languages:
                language = get_language('python')
                parser = get_parser('python')
                loaded_languages['python'] = (language, parser)
    return loaded_languages[language_name]

def should_include_file(file_path: str, tracked_files: set, include_patterns: List[str], exclude_patterns: List[str], repo_working_tree_dir: str) -> bool:
    relative_path = os.path.relpath(file_path, start=repo_working_tree_dir)
    return (
        (relative_path in tracked_files) and
        any(re.match(pattern, os.path.basename(file_path)) for pattern in include_patterns) and
        not any(re.match(re.compile(pattern), os.path.basename(file_path)) for pattern in exclude_patterns)
    )

def analyze_file_with_tree_sitter(file_path: str, level: int, io) -> str:
    with open(file_path, 'rb') as file:
        content = file.read()

    file_extension = os.path.splitext(file_path)[1][1:]
    language, parser = get_language_and_parser(file_extension, io)
    tree = parser.parse(content)

    summary = []
    for node in tree.root_node.children:
        if node.type == 'class_definition':
            class_name = content[node.start_byte:node.end_byte].decode('utf-8').split('\n')[0]
            summary.append(class_name)
            
            if level >= 1:
                # Check for class docstring
                for child in node.children:
                    if child.type == 'block':
                        for grandchild in child.children:
                            if grandchild.type == 'expression_statement':
                                docstring_node = grandchild.children[0]
                                if docstring_node.type == 'string':
                                    docstring = content[docstring_node.start_byte:docstring_node.end_byte].decode('utf-8')
                                    first_line = docstring.split('\n')[0].strip('"""').strip("'''").strip()
                                    summary.append(f"    {first_line}")
                                    break
                        break
            
            if level >= 2:
                # Check for class methods
                for child in node.children:
                    if child.type == 'block':
                        for grandchild in child.children:
                            if grandchild.type == 'function_definition':
                                method_def = content[grandchild.start_byte:grandchild.end_byte].decode('utf-8').split('\n')[0]
                                summary.append(f"    {method_def}")
                                
                                # Check for method docstring
                                for method_child in grandchild.children:
                                    if method_child.type == 'block':
                                        for method_grandchild in method_child.children:
                                            if method_grandchild.type == 'expression_statement':
                                                docstring_node = method_grandchild.children[0]
                                                if docstring_node.type == 'string':
                                                    docstring = content[docstring_node.start_byte:docstring_node.end_byte].decode('utf-8')
                                                    first_line = docstring.split('\n')[0].strip('"""').strip("'''").strip()
                                                    summary.append(f"        {first_line}")
                                                    break
                                        break
        elif node.type in ('function_definition', 'method_definition'):
            definition = content[node.start_byte:node.end_byte].decode('utf-8').split('\n')[0]
            summary.append(definition)
            
            if level >= 1:
                # Check for function docstring
                for child in node.children:
                    if child.type == 'block':
                        for grandchild in child.children:
                            if grandchild.type == 'expression_statement':
                                docstring_node = grandchild.children[0]
                                if docstring_node.type == 'string':
                                    docstring = content[docstring_node.start_byte:docstring_node.end_byte].decode('utf-8')
                                    first_line = docstring.split('\n')[0].strip('"""').strip("'''").strip()
                                    summary.append(f"    {first_line}")
                                    break
                        break
        elif node.type == 'expression_statement':
            # This might catch module-level docstrings or comments
            child = node.children[0]
            if child.type == 'string':
                docstring = content[child.start_byte:child.end_byte].decode('utf-8')
                first_line = docstring.split('\n')[0].strip('"""').strip("'''").strip()
                summary.append(f"{first_line}")

    return '\n'.join(summary)

def generate_tree(repo_path: str, include_patterns: List[str], exclude_patterns: List[str], level: int, tracked_files: list, io) -> str:
    tree = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = os.path.join(root, file)
            if should_include_file(file_path, tracked_files, include_patterns, exclude_patterns, repo_path):
                relative_path = os.path.relpath(file_path, start=repo_path)
                tree.append(f"\n{relative_path}")
                tree.append("=" * len(relative_path))
                summary = analyze_file_with_tree_sitter(file_path, level, io)
                tree.extend(summary.split('\n'))
                tree.append("=" * len(relative_path))
                tree.append("")  # Add an empty line after each file
    
    return '\n'.join(tree)