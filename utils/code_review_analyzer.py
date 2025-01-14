import logging
from typing import Dict, List, Optional
import ast
import re
import radon.metrics
import radon.complexity
from radon.visitors import ComplexityVisitor
import autopep8
import subprocess
import tempfile
import os
from pylint.lint import Run
from pylint.reporters import JSONReporter

logger = logging.getLogger(__name__)

class CodeReviewAnalyzer:
    """Advanced code analysis with context-aware suggestions and automated review comments"""

    def __init__(self):
        self.complexity_threshold = 10
        self.line_length_threshold = 80
        self.patterns = {
            'security_risks': [
                (r'eval\(', 'Avoid using eval() as it can execute arbitrary code'),
                (r'exec\(', 'Avoid using exec() as it can execute arbitrary code'),
                (r'(?<![\w])input\(', 'Consider validating input() to prevent security vulnerabilities'),
                (r'os\.system\(', 'Use subprocess module instead of os.system for better security'),
                (r'(?<![\w])open\(', 'Ensure proper file handling and closing with context managers'),
            ],
            'performance_issues': [
                (r'for\s+\w+\s+in\s+range\(len\(', 'Use enumerate() instead of range(len())'),
                (r'\.append\(.*\)\s+for\s+.*\s+in', 'Consider using list comprehension instead of append in loop'),
                (r'while\s+True:', 'Ensure proper exit condition in while True loops'),
            ],
            'best_practices': [
                (r'print\(', 'Consider using logging instead of print statements'),
                (r'except:', 'Specify exception types instead of using bare except'),
                (r'pass\s*$', 'Avoid empty code blocks with pass'),
            ]
        }

    def analyze_code_context(self, code: str) -> Dict[str, any]:
        """Analyze code context and provide intelligent suggestions"""
        try:
            # Parse the code
            tree = ast.parse(code)
            
            # Initialize results
            context_analysis = {
                'complexity_analysis': self._analyze_complexity(tree),
                'code_patterns': self._analyze_patterns(code),
                'style_suggestions': self._analyze_style(code),
                'security_review': self._analyze_security(code),
                'improvement_suggestions': []
            }

            # Generate context-aware suggestions
            context_analysis['improvement_suggestions'] = self._generate_suggestions(context_analysis)

            return context_analysis
        except Exception as e:
            logger.error(f"Error analyzing code context: {str(e)}")
            return {'error': str(e)}

    def generate_review_comments(self, code: str) -> List[Dict[str, any]]:
        """Generate automated code review comments"""
        try:
            review_comments = []
            
            # Split code into lines for line-specific comments
            lines = code.split('\n')
            
            # Analyze each line
            for i, line in enumerate(lines, 1):
                # Check line length
                if len(line.strip()) > self.line_length_threshold:
                    review_comments.append({
                        'line': i,
                        'type': 'style',
                        'severity': 'low',
                        'message': f'Line exceeds {self.line_length_threshold} characters'
                    })
                
                # Check patterns
                for category, patterns in self.patterns.items():
                    for pattern, message in patterns:
                        if re.search(pattern, line):
                            review_comments.append({
                                'line': i,
                                'type': category,
                                'severity': 'medium' if category == 'best_practices' else 'high',
                                'message': message,
                                'code': line.strip()
                            })

            # Add complexity-based comments
            try:
                tree = ast.parse(code)
                visitor = ComplexityVisitor.from_ast(tree)
                for complexity in visitor.functions:
                    if complexity.complexity > self.complexity_threshold:
                        review_comments.append({
                            'line': complexity.lineno,
                            'type': 'complexity',
                            'severity': 'high',
                            'message': f'Function {complexity.name} has high cyclomatic complexity ({complexity.complexity})',
                            'suggestion': 'Consider breaking down this function into smaller, more manageable pieces'
                        })
            except:
                pass  # Skip complexity analysis if code can't be parsed

            return review_comments
        except Exception as e:
            logger.error(f"Error generating review comments: {str(e)}")
            return []

    def _analyze_complexity(self, tree: ast.AST) -> Dict[str, any]:
        """Analyze code complexity metrics"""
        visitor = ComplexityVisitor.from_ast(tree)
        complexity_scores = []
        
        for item in visitor.functions:
            complexity_scores.append({
                'name': item.name,
                'complexity': item.complexity,
                'line_number': item.lineno,
                'is_complex': item.complexity > self.complexity_threshold
            })

        return {
            'overall_complexity': sum(item.complexity for item in visitor.functions),
            'average_complexity': sum(item.complexity for item in visitor.functions) / len(visitor.functions) if visitor.functions else 0,
            'complex_functions': complexity_scores
        }

    def _analyze_patterns(self, code: str) -> Dict[str, List[Dict[str, any]]]:
        """Analyze code patterns and anti-patterns"""
        results = {}
        for category, patterns in self.patterns.items():
            matches = []
            for pattern, message in patterns:
                for match in re.finditer(pattern, code):
                    matches.append({
                        'pattern': pattern,
                        'message': message,
                        'line': code.count('\n', 0, match.start()) + 1
                    })
            results[category] = matches
        return results

    def _analyze_style(self, code: str) -> Dict[str, any]:
        """Analyze code style and formatting"""
        try:
            # Get style suggestions using autopep8
            fixed_code = autopep8.fix_code(code, options={'aggressive': 1})
            style_diff = fixed_code != code

            # Run pylint analysis
            style_issues = []
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code)
                temp_file.flush()
                
                try:
                    reporter = JSONReporter()
                    Run([temp_file.name], reporter=reporter, exit=False)
                    for message in reporter.messages:
                        style_issues.append({
                            'line': message.line,
                            'message': message.msg,
                            'severity': message.category.lower()
                        })
                except Exception as e:
                    logger.error(f"Error running pylint: {str(e)}")
                finally:
                    os.unlink(temp_file.name)

            return {
                'needs_formatting': style_diff,
                'style_issues': style_issues or self._get_style_issues(code)
            }
        except Exception as e:
            logger.error(f"Error analyzing style: {str(e)}")
            return {'error': str(e)}

    def _analyze_security(self, code: str) -> Dict[str, List[Dict[str, any]]]:
        """Analyze code for security issues"""
        security_issues = []
        
        # Check for common security patterns
        for pattern, message in self.patterns['security_risks']:
            for match in re.finditer(pattern, code):
                security_issues.append({
                    'type': 'security_risk',
                    'message': message,
                    'line': code.count('\n', 0, match.start()) + 1,
                    'severity': 'high'
                })

        return {
            'security_issues': security_issues,
            'risk_level': 'high' if security_issues else 'low'
        }

    def _get_style_issues(self, code: str) -> List[Dict[str, any]]:
        """Get detailed style issues"""
        style_issues = []
        
        # Check line lengths
        for i, line in enumerate(code.split('\n'), 1):
            if len(line.strip()) > self.line_length_threshold:
                style_issues.append({
                    'line': i,
                    'message': f'Line too long ({len(line)} > {self.line_length_threshold} characters)',
                    'severity': 'low'
                })

        # Check indentation
        indent_pattern = r'^\s+'
        for i, line in enumerate(code.split('\n'), 1):
            if match := re.match(indent_pattern, line):
                if len(match.group()) % 4 != 0:
                    style_issues.append({
                        'line': i,
                        'message': 'Indentation should be a multiple of 4 spaces',
                        'severity': 'low'
                    })

        return style_issues

    def _generate_suggestions(self, analysis: Dict[str, any]) -> List[Dict[str, str]]:
        """Generate context-aware improvement suggestions"""
        suggestions = []

        # Complexity-based suggestions
        if 'complexity_analysis' in analysis:
            complex_funcs = [f for f in analysis['complexity_analysis'].get('complex_functions', []) 
                           if f['is_complex']]
            if complex_funcs:
                suggestions.append({
                    'category': 'complexity',
                    'suggestion': 'Consider refactoring these complex functions:',
                    'details': [f"- {func['name']} (complexity: {func['complexity']})" 
                              for func in complex_funcs]
                })

        # Pattern-based suggestions
        if 'code_patterns' in analysis:
            for category, patterns in analysis['code_patterns'].items():
                if patterns:
                    suggestions.append({
                        'category': category,
                        'suggestion': f'Address {category.replace("_", " ")}:',
                        'details': [f"- Line {p['line']}: {p['message']}" for p in patterns]
                    })

        # Style-based suggestions
        if 'style_suggestions' in analysis:
            style = analysis['style_suggestions']
            if style.get('needs_formatting'):
                suggestions.append({
                    'category': 'style',
                    'suggestion': 'Code style improvements needed:',
                    'details': [f"- {issue['message']}" for issue in style.get('style_issues', [])]
                })

        return suggestions 