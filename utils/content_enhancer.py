import logging
from typing import Dict, List, Optional
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentEnhancer:
    # Industry-specific templates
    TEMPLATES = {
        'api_documentation': {
            'sections': [
                'API Overview',
                'Authentication',
                'Endpoints',
                'Request/Response Format',
                'Error Handling',
                'Rate Limits',
                'Examples'
            ]
        },
        'user_guide': {
            'sections': [
                'Introduction',
                'Getting Started',
                'Features',
                'Installation',
                'Configuration',
                'Usage Examples',
                'Troubleshooting'
            ]
        },
        'technical_spec': {
            'sections': [
                'System Architecture',
                'Components',
                'Data Flow',
                'Security',
                'Performance Requirements',
                'Integration Points',
                'Deployment'
            ]
        }
    }

    @staticmethod
    def apply_template(content: str, template_type: str) -> str:
        """Apply industry-specific template to content"""
        try:
            if template_type not in ContentEnhancer.TEMPLATES:
                return content

            template_sections = ContentEnhancer.TEMPLATES[template_type]['sections']
            formatted_content = f"# {template_type.replace('_', ' ').title()}\n\n"
            
            for section in template_sections:
                formatted_content += f"## {section}\n\n"
                # Extract relevant content for each section if it exists
                section_pattern = re.compile(f"{section}.*?\n(.*?)(?=##|\Z)", re.DOTALL)
                match = section_pattern.search(content)
                if match:
                    formatted_content += match.group(1).strip() + "\n\n"
                else:
                    formatted_content += "[Section content to be added]\n\n"

            return formatted_content
        except Exception as e:
            logger.error(f"Error applying template: {str(e)}")
            return content

    @staticmethod
    def generate_citations(content: str) -> tuple[str, List[Dict]]:
        """Generate citations and references for the content"""
        try:
            references = []
            modified_content = content

            # Pattern for identifying potential references
            patterns = [
                r'(?i)according to\s+([^,.]+)',
                r'(?i)as stated (?:in|by)\s+([^,.]+)',
                r'(?i)referenced (?:in|by)\s+([^,.]+)',
                r'(?i)cited (?:in|by)\s+([^,.]+)'
            ]

            ref_number = 1
            for pattern in patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    source = match.group(1).strip()
                    citation_mark = f"[{ref_number}]"
                    
                    # Add citation mark in content
                    modified_content = modified_content.replace(
                        match.group(0),
                        f"{match.group(0)} {citation_mark}"
                    )

                    # Add to references list
                    references.append({
                        'number': ref_number,
                        'source': source,
                        'date_accessed': datetime.now().strftime("%Y-%m-%d")
                    })
                    ref_number += 1

            # Add references section if any found
            if references:
                modified_content += "\n\n## References\n"
                for ref in references:
                    modified_content += f"{ref['number']}. {ref['source']} (Accessed: {ref['date_accessed']})\n"

            return modified_content, references
        except Exception as e:
            logger.error(f"Error generating citations: {str(e)}")
            return content, []

    @staticmethod
    def version_control(content: str, version: str, author: str) -> str:
        """Add version control information to the document"""
        try:
            version_info = f"""
# Version Control Information
- Version: {version}
- Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- Author: {author}

---

"""
            return version_info + content
        except Exception as e:
            logger.error(f"Error adding version control: {str(e)}")
            return content 