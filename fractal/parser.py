"""
Docstring parser for extracting tool metadata from Google-style docstrings.
"""
import inspect
import re
from typing import Any, Callable, Dict, Optional


def parse_google_docstring(func: Callable) -> Dict[str, Any]:
    """
    Parse a Google-style docstring to extract function metadata.

    Args:
        func: The function whose docstring to parse

    Returns:
        A dictionary containing:
        - description: Function description
        - parameters: Dict mapping parameter names to their descriptions and types
        - returns: Return value description
    """
    docstring = inspect.getdoc(func)
    if not docstring:
        return {
            "description": func.__name__,
            "parameters": {},
            "returns": None
        }

    # Split docstring into sections
    lines = docstring.split('\n')

    # Extract main description (everything before first section)
    description_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line in ['Args:', 'Arguments:', 'Parameters:', 'Returns:', 'Return:', 'Raises:', 'Examples:', 'Example:']:
            break
        description_lines.append(lines[i])
        i += 1

    description = '\n'.join(description_lines).strip()

    # Parse Args section
    parameters = {}
    returns = None

    current_section = None
    j = i
    while j < len(lines):
        line = lines[j].strip()

        if line in ['Args:', 'Arguments:', 'Parameters:']:
            current_section = 'args'
            j += 1
            continue
        elif line in ['Returns:', 'Return:']:
            current_section = 'returns'
            j += 1
            continue
        elif line in ['Raises:', 'Examples:', 'Example:']:
            current_section = None
            j += 1
            continue

        if current_section == 'args' and line:
            # Parse argument line: "param_name (type): description" or "param_name: description"
            match = re.match(r'(\w+)\s*(?:\(([^)]+)\))?\s*:\s*(.+)', line)
            if match:
                param_name = match.group(1)
                param_type = match.group(2) if match.group(2) else "string"
                param_desc = match.group(3)

                # Continue reading if description spans multiple lines
                k = j + 1
                while k < len(lines) and lines[k] and not lines[k].strip().startswith(tuple('abcdefghijklmnopqrstuvwxyz')):
                    if not lines[k].strip() in ['Returns:', 'Return:', 'Raises:', 'Examples:', 'Example:']:
                        param_desc += ' ' + lines[k].strip()
                        j = k
                    else:
                        break
                    k += 1

                parameters[param_name] = {
                    "type": _map_python_type_to_json(param_type),
                    "description": param_desc.strip()
                }

        elif current_section == 'returns' and line:
            # Parse return description
            if not returns:
                returns = line
            else:
                returns += ' ' + line

        j += 1

    return {
        "description": description if description else func.__name__,
        "parameters": parameters,
        "returns": returns
    }


def _map_python_type_to_json(type_str: str) -> str:
    """
    Map Python type hints to JSON schema types.

    Args:
        type_str: Python type as string

    Returns:
        JSON schema type string
    """
    type_str = type_str.strip().lower()

    type_mapping = {
        'str': 'string',
        'string': 'string',
        'int': 'integer',
        'integer': 'integer',
        'float': 'number',
        'number': 'number',
        'bool': 'boolean',
        'boolean': 'boolean',
        'list': 'array',
        'array': 'array',
        'dict': 'object',
        'object': 'object',
        'any': 'string',
    }

    for py_type, json_type in type_mapping.items():
        if py_type in type_str:
            return json_type

    return 'string'


def function_to_tool_schema(func: Callable) -> Dict[str, Any]:
    """
    Convert a function with Google-style docstring to OpenAI tool schema.

    Args:
        func: The function to convert

    Returns:
        OpenAI tool schema dictionary
    """
    parsed = parse_google_docstring(func)

    # Get function signature for required parameters
    sig = inspect.signature(func)
    required_params = []
    properties = {}

    for param_name, param in sig.parameters.items():
        if param_name == 'self':
            continue

        # Get parameter info from parsed docstring
        param_info = parsed['parameters'].get(param_name, {})

        properties[param_name] = {
            "type": param_info.get('type', 'string'),
            "description": param_info.get('description', '')
        }

        # Check if parameter is required (no default value)
        if param.default == inspect.Parameter.empty:
            required_params.append(param_name)

    schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": parsed['description'],
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_params
            }
        }
    }

    return schema
