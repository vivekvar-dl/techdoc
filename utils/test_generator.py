import logging
from typing import Dict, List, Optional
import ast
import re
import inspect
from dataclasses import dataclass
from unittest.mock import MagicMock

logger = logging.getLogger(__name__)

@dataclass
class FunctionInfo:
    name: str
    args: List[str]
    returns: Optional[str]
    docstring: Optional[str]
    is_async: bool
    decorators: List[str]

class TestGenerator:
    """Generates automated test cases for Python code"""

    def __init__(self):
        self.mock_types = {
            'str': '',
            'int': 0,
            'float': 0.0,
            'bool': False,
            'list': [],
            'dict': {},
            'set': set(),
            'tuple': (),
        }

    def generate_test_cases(self, code: str) -> List[Dict[str, any]]:
        """Generate test cases for the given code"""
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Extract functions and classes
            functions = self._extract_functions(tree)
            
            # Generate test cases
            test_cases = []
            for func in functions:
                test_cases.extend(self._generate_function_tests(func))
            
            return test_cases
        except Exception as e:
            logger.error(f"Error generating test cases: {str(e)}")
            return []

    def _extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
        """Extract function information from AST"""
        functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Get function arguments
                args = []
                for arg in node.args.args:
                    args.append(arg.arg)
                
                # Get return type hint if available
                returns = None
                if node.returns:
                    returns = ast.unparse(node.returns)
                
                # Get docstring if available
                docstring = ast.get_docstring(node)
                
                # Check if async
                is_async = isinstance(node, ast.AsyncFunctionDef)
                
                # Get decorators
                decorators = [ast.unparse(d) for d in node.decorator_list]
                
                functions.append(FunctionInfo(
                    name=node.name,
                    args=args,
                    returns=returns,
                    docstring=docstring,
                    is_async=is_async,
                    decorators=decorators
                ))
        
        return functions

    def _generate_function_tests(self, func: FunctionInfo) -> List[Dict[str, any]]:
        """Generate test cases for a single function"""
        test_cases = []
        
        # Generate basic test case template
        test_template = self._generate_test_template(func)
        test_cases.append({
            'name': f'test_{func.name}_basic',
            'function': func.name,
            'test_template': test_template,
            'type': 'basic'
        })
        
        # Generate edge cases
        edge_cases = self._generate_edge_cases(func)
        test_cases.extend(edge_cases)
        
        # Generate error cases
        error_cases = self._generate_error_cases(func)
        test_cases.extend(error_cases)
        
        return test_cases

    def _generate_test_template(self, func: FunctionInfo) -> str:
        """Generate basic test template for a function"""
        # Create function signature
        args = []
        setup_lines = []
        
        for arg in func.args:
            if arg == 'self':
                continue
            
            # Generate mock value based on type hint if available
            mock_value = self._get_mock_value(arg)
            args.append(mock_value)
            setup_lines.append(f"    {arg} = {mock_value}")
        
        args_str = ', '.join(args)
        
        # Create test function
        test_code = [
            f"def test_{func.name}_basic():",
            "    # Setup",
            *setup_lines,
            "",
            "    # Execute",
            f"    result = {func.name}({args_str})",
            "",
            "    # Assert",
            "    assert result is not None  # Replace with specific assertions",
            ""
        ]
        
        return '\n'.join(test_code)

    def _generate_edge_cases(self, func: FunctionInfo) -> List[Dict[str, any]]:
        """Generate edge case tests"""
        edge_cases = []
        
        # Empty/None values test
        edge_template = [
            f"def test_{func.name}_edge_cases():",
            "    # Test with empty/None values",
            *[f"    {arg} = None" for arg in func.args if arg != 'self'],
            "",
            "    # Execute and verify it handles edge cases gracefully",
            f"    result = {func.name}({', '.join(arg for arg in func.args if arg != 'self')})",
            "",
            "    # Assert handles None/empty values",
            "    assert result is not None  # Replace with specific assertions",
            ""
        ]
        
        edge_cases.append({
            'name': f'test_{func.name}_edge_cases',
            'function': func.name,
            'test_template': '\n'.join(edge_template),
            'type': 'edge'
        })
        
        return edge_cases

    def _generate_error_cases(self, func: FunctionInfo) -> List[Dict[str, any]]:
        """Generate error case tests"""
        error_cases = []
        
        # Type error test
        error_template = [
            f"def test_{func.name}_error_cases():",
            "    # Test with invalid types",
            "    with pytest.raises(TypeError):",
            f"        {func.name}({', '.join('invalid_value' for _ in func.args if _ != 'self')})",
            "",
            "    # Test with invalid values",
            "    with pytest.raises(ValueError):",
            f"        {func.name}({', '.join('-1' for _ in func.args if _ != 'self')})",
            ""
        ]
        
        error_cases.append({
            'name': f'test_{func.name}_error_cases',
            'function': func.name,
            'test_template': '\n'.join(error_template),
            'type': 'error'
        })
        
        return error_cases

    def _get_mock_value(self, arg_name: str) -> str:
        """Get appropriate mock value based on argument name"""
        # Common naming patterns
        patterns = {
            'name': '"test_name"',
            'id': '1',
            'count': '0',
            'data': '{"test": "data"}',
            'list': '[]',
            'dict': '{}',
            'flag': 'False',
            'enabled': 'True',
            'date': '"2024-01-14"',
            'path': '"test/path"',
            'url': '"http://example.com"',
            'email': '"test@example.com"',
            'config': '{"test": "config"}',
            'options': '{"test": "options"}',
        }
        
        # Check for common patterns in argument name
        for pattern, value in patterns.items():
            if pattern in arg_name.lower():
                return value
        
        # Default to None for unknown types
        return 'None' 