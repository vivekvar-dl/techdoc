import logging
from typing import Dict, List, Optional
import ast
import re
import radon.metrics
import radon.complexity
import subprocess
import tempfile
import os
import autopep8
from graphviz import Digraph

logger = logging.getLogger(__name__)

class CodeAnalyzer:
    SUPPORTED_LANGUAGES = {
        'python': ['.py'],
        'javascript': ['.js', '.jsx', '.ts', '.tsx'],
        'java': ['.java'],
        'cpp': ['.cpp', '.hpp', '.h'],
        'csharp': ['.cs']
    }

    @staticmethod
    def detect_language(code: str) -> str:
        """Detect programming language from code"""
        # Simple heuristics for language detection
        patterns = {
            'python': r'def\s+\w+\s*\(|import\s+\w+|from\s+\w+\s+import',
            'javascript': r'function\s+\w+\s*\(|const\s+\w+\s*=|let\s+\w+\s*=|var\s+\w+\s*=',
            'java': r'public\s+class|private\s+class|protected\s+class',
            'cpp': r'#include\s*<|namespace\s+\w+|::\w+',
            'csharp': r'namespace\s+\w+|using\s+\w+;|public\s+class'
        }

        for lang, pattern in patterns.items():
            if re.search(pattern, code):
                return lang
        return 'unknown'

    def analyze_code_quality(self, code: str, language: str) -> Dict[str, any]:
        """Analyze code quality metrics"""
        try:
            if language == 'python':
                return self._analyze_python_code(code)
            # Add support for other languages here
            return {'error': 'Language not supported for quality analysis'}
        except Exception as e:
            logger.error(f"Error analyzing code quality: {str(e)}")
            return {'error': str(e)}

    def _analyze_python_code(self, code: str) -> Dict[str, any]:
        """Analyze Python code quality"""
        try:
            # Calculate metrics
            mi = radon.metrics.mi_visit(code)
            cc = radon.complexity.cc_visit(code)
            
            # Run pylint
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name

            try:
                pylint_output = subprocess.check_output(['pylint', temp_file], stderr=subprocess.STDOUT, text=True)
            except subprocess.CalledProcessError as e:
                pylint_output = e.output
            finally:
                os.unlink(temp_file)
            
            # Format code
            formatted_code = autopep8.fix_code(code)
            
            return {
                'maintainability_index': mi,
                'cyclomatic_complexity': [{'name': c.name, 'complexity': c.complexity} for c in cc],
                'lint_output': pylint_output,
                'formatted_code': formatted_code
            }
        except Exception as e:
            logger.error(f"Error in Python code analysis: {str(e)}")
            return {'error': str(e)}

    def generate_test_cases(self, code: str, language: str) -> List[Dict]:
        """Generate test cases based on code documentation"""
        try:
            if language == 'python':
                return self._generate_python_tests(code)
            # Add support for other languages here
            return [{'error': 'Language not supported for test generation'}]
        except Exception as e:
            logger.error(f"Error generating test cases: {str(e)}")
            return [{'error': str(e)}]

    def _generate_python_tests(self, code: str) -> List[Dict]:
        """Generate Python test cases"""
        try:
            tree = ast.parse(code)
            test_cases = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract function information
                    func_name = node.name
                    args = [arg.arg for arg in node.args.args]
                    docstring = ast.get_docstring(node)
                    
                    # Generate test case template
                    test_case = {
                        'function_name': func_name,
                        'test_name': f'test_{func_name}',
                        'parameters': args,
                        'docstring': docstring,
                        'test_template': self._create_test_template(func_name, args)
                    }
                    test_cases.append(test_case)
            
            return test_cases
        except Exception as e:
            logger.error(f"Error generating Python tests: {str(e)}")
            return [{'error': str(e)}]

    @staticmethod
    def _create_test_template(func_name: str, args: List[str]) -> str:
        """Create a test function template"""
        args_str = ', '.join(['None'] * len(args))
        return f"""
def test_{func_name}():
    # Arrange
    {', '.join(args)} = {args_str}
    expected_result = None
    
    # Act
    result = {func_name}({', '.join(args)})
    
    # Assert
    assert result == expected_result
"""

    def generate_sequence_diagram(self, code: str, language: str) -> Optional[bytes]:
        """Generate sequence diagram from code"""
        try:
            if language == 'python':
                return self._generate_python_sequence_diagram(code)
            # Add support for other languages here
            return None
        except Exception as e:
            logger.error(f"Error generating sequence diagram: {str(e)}")
            return None

    def _generate_python_sequence_diagram(self, code: str) -> Optional[bytes]:
        """Generate sequence diagram for Python code"""
        try:
            tree = ast.parse(code)
            dot = Digraph(comment='Sequence Diagram')
            dot.attr(rankdir='TB')
            
            # Track function calls
            calls = []
            
            class FunctionCallVisitor(ast.NodeVisitor):
                def visit_Call(self, node):
                    if isinstance(node.func, ast.Name):
                        calls.append({
                            'caller': None,  # Will be set later
                            'callee': node.func.id
                        })
                    self.generic_visit(node)
            
            visitor = FunctionCallVisitor()
            visitor.visit(tree)
            
            # Add nodes and edges
            for call in calls:
                dot.node(call['callee'], call['callee'])
                if call['caller']:
                    dot.edge(call['caller'], call['callee'])
            
            return dot.pipe(format='png')
        except Exception as e:
            logger.error(f"Error generating Python sequence diagram: {str(e)}")
            return None 