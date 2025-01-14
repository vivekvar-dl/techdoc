import os
import streamlit as st
import google.generativeai as genai
import sentry_sdk
from redis import Redis
from rq import Queue
import logging
from datetime import datetime
from PyPDF2 import PdfReader
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import pandas as pd
import nltk
from nltk.data import path as nltk_data_path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set NLTK data path
nltk_data_dir = os.path.expanduser('~/nltk_data')
if not os.path.exists(nltk_data_dir):
    os.makedirs(nltk_data_dir)
nltk_data_path.append(nltk_data_dir)

# Download required NLTK data
required_nltk_packages = [
    'punkt',
    'averaged_perceptron_tagger',
    'words',
    'maxent_ne_chunker',
    'stopwords',
    'wordnet',
    'omw-1.4'
]

print("Downloading required NLTK packages...")
for package in required_nltk_packages:
    try:
        nltk.download(package, quiet=True, download_dir=nltk_data_dir)
        print(f"Successfully downloaded {package}")
    except Exception as e:
        logger.error(f"Error downloading NLTK package {package}: {str(e)}")
        print(f"Warning: Failed to download {package}. Some features may not work properly.")

# Verify NLTK data is accessible
try:
    # Test tokenizers
    nltk.sent_tokenize("This is a test sentence.")
    nltk.word_tokenize("This is a test sentence.")
    # Test POS tagger
    nltk.pos_tag(['This', 'is', 'a', 'test'])
except Exception as e:
    logger.error(f"Error verifying NLTK functionality: {str(e)}")
    print("Warning: NLTK initialization failed. Some features may not work properly.")

from config import (
    GOOGLE_API_KEY,
    SENTRY_DSN,
    REDIS_HOST,
    REDIS_PORT,
    REDIS_DB,
    GEMINI_MODEL,
    ALLOWED_FILE_TYPES
)
from utils.document_processor import DocumentProcessor
from utils.document_analyzer import DocumentAnalyzer
from utils.content_enhancer import ContentEnhancer
from utils.code_analyzer import CodeAnalyzer
from utils.code_review_analyzer import CodeReviewAnalyzer
from utils.test_generator import TestGenerator

# Initialize analyzers
document_analyzer = DocumentAnalyzer()
code_analyzer = CodeAnalyzer()
code_review_analyzer = CodeReviewAnalyzer()
test_generator = TestGenerator()

# Initialize Sentry for error tracking if DSN is provided
if SENTRY_DSN:
    try:
        sentry_sdk.init(dsn=SENTRY_DSN)
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {str(e)}")

# Configure Gemini API
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)

# Initialize Redis and RQ if available
try:
    redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    queue = Queue(connection=redis_conn)
except Exception as e:
    logger.warning(f"Failed to initialize Redis: {str(e)}")
    redis_conn = None
    queue = None

def analyze_documentation(text: str) -> str:
    """Analyze documentation using Gemini  & llama"""
    try:
        prompt = f"""Analyze the following technical documentation and provide:
        1. A concise summary
        2. Key points and concepts
        3. Suggestions for improvement
        4. Consistency check
        5. Areas that need more detail
        
        Documentation:
        {text}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error analyzing documentation: {str(e)}")
        sentry_sdk.capture_exception(e)
        return "Error analyzing documentation. Please try again later."

def generate_code_documentation(code: str) -> str:
    """Generate documentation from code"""
    try:
        prompt = f"""Generate comprehensive documentation for the following code:
        1. Function descriptions
        2. Parameter explanations
        3. Return value details
        4. Usage examples
        5. Any important notes
        
        Code:
        {code}
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating code documentation: {str(e)}")
        sentry_sdk.capture_exception(e)
        return "Error generating documentation. Please try again later."

def generate_technical_content(topic: str, requirements: str) -> str:
    """Generate technical documentation content"""
    try:
        prompt = f"""Generate comprehensive technical documentation for the following topic:
        
        Topic: {topic}
        
        Requirements: {requirements}
        
        Please provide a complete technical document with the following sections:
        1. Executive Summary
        2. Introduction
        3. Technical Overview
        4. Detailed Specifications
        5. Implementation Guidelines
        6. Best Practices
        7. Security Considerations
        8. Performance Optimization
        9. Troubleshooting Guide
        10. References
        
        Make it detailed, professional, and well-structured.
        """
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating technical content: {str(e)}")
        sentry_sdk.capture_exception(e)
        return "Error generating technical content. Please try again later."

def create_pdf(content: str) -> BytesIO:
    """Create PDF from generated content"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Create custom style for headers
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    
    # Create story (content flow)
    story = []
    
    # Split content into sections
    sections = content.split('\n')
    
    for section in sections:
        if section.strip():
            if section.startswith('#'):
                # Handle headers
                story.append(Paragraph(section.replace('#', '').strip(), header_style))
            else:
                # Handle regular paragraphs
                story.append(Paragraph(section, styles['Normal']))
            story.append(Spacer(1, 12))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

# Streamlit UI
st.set_page_config(page_title="AI Technical Documentation Assistant", layout="wide")

st.title("AI Technical Documentation Assistant")
st.write("Powered by Google's Gemini & Llama")

# Sidebar for mode selection
mode = st.sidebar.selectbox(
    "Select Mode",
    ["Document Analysis", "Code Documentation", "Content Generation", "Advanced Analysis"]
)

# File upload section
st.sidebar.markdown("### Upload Settings")
allowed_types = ", ".join(ALLOWED_FILE_TYPES.values())
st.sidebar.info(f"Supported file types: {allowed_types}")

if mode == "Document Analysis":
    st.header("Document Analysis")
    
    # File upload or text input
    input_method = st.radio("Choose input method:", ["Upload File", "Paste Text"])
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader("Upload your document", type=list(ext.strip('.') for ext in ALLOWED_FILE_TYPES.values()))
        
        if uploaded_file:
            with st.spinner("Processing document..."):
                result = DocumentProcessor.process_document(uploaded_file)
                
                if result["success"]:
                    doc_text = result["text"]
                    st.success("Document processed successfully!")

                    # Advanced analysis options
                    with st.expander("Advanced Analysis Options"):
                        run_plagiarism = st.checkbox("Check for potential plagiarism")
                        run_readability = st.checkbox("Calculate readability metrics")
                        run_terminology = st.checkbox("Validate technical terminology")

                    if st.button("Analyze Document"):
                        with st.spinner("Analyzing documentation..."):
                            # Basic analysis
                            analysis = analyze_documentation(doc_text)
                            st.markdown("### Analysis Results")
                            st.markdown(analysis)

                            # Advanced analysis if selected
                            if run_plagiarism:
                                st.markdown("### Plagiarism Check")
                                plagiarism_results = document_analyzer.check_plagiarism(doc_text)
                                st.json(plagiarism_results)

                            if run_readability:
                                st.markdown("### Readability Metrics")
                                readability_results = document_analyzer.calculate_readability_score(doc_text)
                                st.json(readability_results)

                            if run_terminology:
                                st.markdown("### Technical Terminology Analysis")
                                terminology_results = document_analyzer.validate_technical_terminology(doc_text, "technical")
                                st.json(terminology_results)

                            # Download options
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            st.download_button(
                                "Download Analysis",
                                analysis,
                                file_name=f"analysis_{timestamp}.md",
                                mime="text/markdown"
                            )
                else:
                    st.error(result["error"])

    else:
        doc_text = st.text_area("Paste your documentation here:", height=300)
        
        if doc_text and st.button("Analyze Documentation"):
            with st.spinner("Analyzing documentation..."):
                analysis = analyze_documentation(doc_text)
                st.markdown("### Analysis Results")
                st.markdown(analysis)

elif mode == "Code Documentation":
    st.header("Code Documentation Generator")
    
    code_text = st.text_area("Paste your code here:", height=300)
    
    # Advanced code analysis options
    with st.expander("Advanced Code Analysis Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Analysis")
            run_quality = st.checkbox("Analyze code quality", value=True)
            run_review = st.checkbox("Generate review comments", value=True)
            run_security = st.checkbox("Security analysis", value=True)
        
        with col2:
            st.markdown("#### Generation")
            generate_tests = st.checkbox("Generate test cases", value=True)
            create_diagram = st.checkbox("Generate sequence diagram", value=True)
            suggest_improvements = st.checkbox("Suggest improvements", value=True)
    
    if st.button("Generate Documentation"):
        if code_text:
            with st.spinner("Processing code..."):
                # Detect language
                language = code_analyzer.detect_language(code_text)
                st.info(f"Detected language: {language}")

                # Basic documentation
                documentation = generate_code_documentation(code_text)
                st.markdown("### Generated Documentation")
                st.markdown(documentation)

                # Advanced analysis if selected
                if run_quality or run_review or run_security:
                    st.markdown("### Code Analysis")
                    
                    if run_quality:
                        quality_results = code_analyzer.analyze_code_quality(code_text, language)
                        st.markdown("#### Code Quality Metrics")
                        st.json(quality_results)
                    
                    if run_review:
                        review_results = code_review_analyzer.generate_review_comments(code_text)
                        st.markdown("#### Code Review Comments")
                        
                        if review_results:
                            for comment in review_results:
                                severity_color = {
                                    'high': '🔴',
                                    'medium': '🟡',
                                    'low': '🟢'
                                }.get(comment['severity'], '⚪')
                                
                                st.markdown(f"{severity_color} **Line {comment['line']}**: {comment['message']}")
                                if 'code' in comment:
                                    st.code(comment['code'], language=language)
                                if 'suggestion' in comment:
                                    st.info(comment['suggestion'])
                        else:
                            st.success("No significant issues found in the code review.")
                    
                    if run_security:
                        context_analysis = code_review_analyzer.analyze_code_context(code_text)
                        if 'security_review' in context_analysis:
                            st.markdown("#### Security Analysis")
                            security = context_analysis['security_review']
                            
                            risk_color = '🔴' if security['risk_level'] == 'high' else '🟢'
                            st.markdown(f"{risk_color} Overall Risk Level: {security['risk_level'].title()}")
                            
                            if security['security_issues']:
                                for issue in security['security_issues']:
                                    st.warning(f"Line {issue['line']}: {issue['message']}")
                            else:
                                st.success("No security issues detected.")

                if generate_tests:
                    st.markdown("### Generated Test Cases")
                    test_cases = test_generator.generate_test_cases(code_text)
                    
                    if test_cases:
                        test_types = {'basic': '📝', 'edge': '🔄', 'error': '❌'}
                        
                        for test in test_cases:
                            with st.expander(f"{test_types.get(test['type'], '🔹')} {test['name']}"):
                                st.code(test['test_template'], language='python')
                    else:
                        st.warning("Could not generate test cases. Make sure the code is valid Python.")

                if create_diagram:
                    st.markdown("### Sequence Diagram")
                    diagram = code_analyzer.generate_sequence_diagram(code_text, language)
                    if diagram:
                        st.image(diagram)
                    else:
                        st.warning("Could not generate sequence diagram for this code.")

                if suggest_improvements:
                    st.markdown("### Suggested Improvements")
                    context_analysis = code_review_analyzer.analyze_code_context(code_text)
                    
                    if 'improvement_suggestions' in context_analysis:
                        suggestions = context_analysis['improvement_suggestions']
                        
                        if suggestions:
                            for suggestion in suggestions:
                                with st.expander(f"✨ {suggestion['category'].title()} Improvements"):
                                    st.markdown(f"**{suggestion['suggestion']}**")
                                    for detail in suggestion['details']:
                                        st.markdown(detail)
                        else:
                            st.success("No significant improvements suggested.")

                # Download options
                st.markdown("### Download Options")
                col3, col4 = st.columns(2)
                
                with col3:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "Download Documentation",
                        documentation,
                        file_name=f"documentation_{timestamp}.md",
                        mime="text/markdown"
                    )
                
                with col4:
                    if generate_tests:
                        test_code = "\n\n".join(test['test_template'] for test in test_cases)
                        st.download_button(
                            "Download Test Cases",
                            test_code,
                            file_name=f"tests_{timestamp}.py",
                            mime="text/x-python"
                        )
        else:
            st.warning("Please enter some code to document.")

elif mode == "Content Generation":
    st.header("Technical Documentation Generator")
    
    # Input fields for content generation
    topic = st.text_input("Topic:", placeholder="Enter the main topic for the technical documentation")
    
    # Template selection
    template_type = st.selectbox(
        "Documentation Type",
        ["technical_spec", "api_documentation", "user_guide"]
    )
    
    st.markdown("### Requirements")
    st.markdown("Specify any specific requirements, sections, or points that should be included:")
    requirements = st.text_area("Requirements:", height=150, 
                               placeholder="Example:\n- Include security considerations\n- Add deployment instructions\n- Cover performance optimization")
    
    # Additional options
    with st.expander("Advanced Options"):
        include_diagrams = st.checkbox("Include placeholder for diagrams", value=True)
        include_code_samples = st.checkbox("Include code samples (if applicable)", value=True)
        add_citations = st.checkbox("Generate citations and references", value=True)
        add_version = st.checkbox("Add version control information", value=True)
        doc_format = st.radio("Output Format", ["PDF", "Markdown"])
        
        if add_version:
            version = st.text_input("Version:", value="1.0.0")
            author = st.text_input("Author:", value="AI Documentation Assistant")
    
    if st.button("Generate Documentation"):
        if topic and requirements:
            with st.spinner("Generating technical documentation..."):
                # Generate base content
                content = generate_technical_content(topic, requirements)
                
                # Apply template
                content = ContentEnhancer.apply_template(content, template_type)
                
                # Add citations if requested
                if add_citations:
                    content, references = ContentEnhancer.generate_citations(content)
                
                # Add version control if requested
                if add_version:
                    content = ContentEnhancer.version_control(content, version, author)
                
                # Show preview
                st.markdown("### Preview")
                st.markdown(content)
                
                # Create and offer download
                if doc_format == "PDF":
                    pdf_buffer = create_pdf(content)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "Download PDF",
                        pdf_buffer,
                        file_name=f"technical_doc_{timestamp}.pdf",
                        mime="application/pdf"
                    )
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "Download Markdown",
                        content,
                        file_name=f"technical_doc_{timestamp}.md",
                        mime="text/markdown"
                    )
        else:
            st.warning("Please enter both topic and requirements to generate documentation.")

elif mode == "Advanced Analysis":
    st.header("Advanced Document Analysis")
    
    # Initialize doc_text as None
    doc_text = None
    
    # Input method selection
    input_method = st.radio("Choose input method:", ["Upload File", "Paste Text"])
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader("Upload your document", type=list(ext.strip('.') for ext in ALLOWED_FILE_TYPES.values()))
        if uploaded_file:
            result = DocumentProcessor.process_document(uploaded_file)
            if result["success"]:
                doc_text = result["text"]
            else:
                st.error(result["error"])
    else:
        doc_text = st.text_area("Paste your text here:", height=200)

    if doc_text:
        # Analysis Options
        st.markdown("### Select Analysis Types")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Content Analysis")
            run_readability = st.checkbox("Readability Analysis", value=True)
            run_terminology = st.checkbox("Technical Terminology Check", value=True)
            run_plagiarism = st.checkbox("Plagiarism Detection", value=True)
            run_tone_analysis = st.checkbox("Tone Analysis", value=True)
            
        with col2:
            st.markdown("#### Document Enhancement")
            add_citations = st.checkbox("Generate Citations", value=True)
            apply_template = st.checkbox("Apply Document Template", value=True)
            add_version_info = st.checkbox("Add Version Control Info", value=True)

        if apply_template:
            template_type = st.selectbox(
                "Select Template Type",
                ["technical_spec", "api_documentation", "user_guide"]
            )

        if add_version_info:
            col3, col4 = st.columns(2)
            with col3:
                version = st.text_input("Version:", value="1.0.0")
            with col4:
                author = st.text_input("Author:", value="AI Documentation Assistant")

        if st.button("Run Advanced Analysis"):
            with st.spinner("Analyzing document..."):
                # Content Analysis
                if run_readability:
                    st.markdown("### Readability Analysis")
                    readability_results = document_analyzer.calculate_readability_score(doc_text)
                    st.json(readability_results)
                    
                    # Interpretation
                    if 'flesch_reading_ease' in readability_results:
                        score = readability_results['flesch_reading_ease']
                        st.info(f"""
                        Flesch Reading Ease Score: {score}
                        - 90-100: Very Easy
                        - 80-89: Easy
                        - 70-79: Fairly Easy
                        - 60-69: Standard
                        - 50-59: Fairly Difficult
                        - 30-49: Difficult
                        - 0-29: Very Difficult
                        """)

                if run_tone_analysis:
                    st.markdown("### Tone Analysis")
                    tone_results = document_analyzer.analyze_tone(doc_text)
                    
                    if 'overall_sentiment' in tone_results:
                        col7, col8 = st.columns(2)
                        with col7:
                            st.markdown("#### Overall Sentiment")
                            polarity = tone_results['overall_sentiment']['polarity']
                            subjectivity = tone_results['overall_sentiment']['subjectivity']
                            st.metric("Document Tone", 
                                    "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral",
                                    f"Polarity: {polarity}")
                            st.metric("Objectivity", 
                                    tone_results['writing_style']['objectivity'].title(),
                                    f"Subjectivity: {subjectivity}")
                        
                        with col8:
                            st.markdown("#### Tone Distribution")
                            dist = tone_results['tone_distribution']
                            st.bar_chart(dist)
                        
                        if tone_results['significant_tone_variations']:
                            st.markdown("#### Significant Tone Variations")
                            for variation in tone_results['significant_tone_variations']:
                                tone_type = "📈 Positive" if variation['tone'] == 'positive' else "📉 Negative"
                                st.markdown(f"**{tone_type}** (Polarity: {variation['polarity']})")
                                st.markdown(f"> {variation['text']}")
                        
                        st.markdown("#### Writing Style Analysis")
                        st.info(f"""
                        - Objectivity: {tone_results['writing_style']['objectivity'].title()}
                        - Tone Consistency: {tone_results['writing_style']['tone_consistency'].title()}
                        """)
                    else:
                        st.error("Error analyzing document tone")

                if run_terminology:
                    st.markdown("### Technical Terminology Analysis")
                    terminology_results = document_analyzer.validate_technical_terminology(doc_text, "technical")
                    
                    # Display terms and inconsistencies
                    if 'technical_terms' in terminology_results:
                        st.markdown("#### Technical Terms Found:")
                        terms_df = pd.DataFrame(terminology_results['technical_terms'], 
                                             columns=['Term', 'Frequency'])
                        st.dataframe(terms_df)
                    
                    if 'inconsistencies' in terminology_results:
                        st.markdown("#### Terminology Inconsistencies:")
                        for issue in terminology_results['inconsistencies']:
                            st.warning(f"Term '{issue['term']}' has variations: {', '.join(issue['variations'])}")

                if run_plagiarism:
                    st.markdown("### Plagiarism Check")
                    plagiarism_results = document_analyzer.check_plagiarism(doc_text)
                    if plagiarism_results.get('has_matches'):
                        st.warning("Potential content matches found:")
                        for match in plagiarism_results['matches']:
                            st.markdown(f"- Match found for: '{match['sentence']}'")
                            st.markdown("  Potential sources:")
                            for source in match['potential_sources']:
                                st.markdown(f"  * {source}")
                    else:
                        st.success("No significant content matches found")

                # Document Enhancement
                enhanced_content = doc_text
                
                if apply_template:
                    enhanced_content = ContentEnhancer.apply_template(enhanced_content, template_type)
                
                if add_citations:
                    enhanced_content, references = ContentEnhancer.generate_citations(enhanced_content)
                    if references:
                        st.markdown("### Generated Citations")
                        for ref in references:
                            st.markdown(f"- [{ref['number']}] {ref['source']}")
                
                if add_version_info:
                    enhanced_content = ContentEnhancer.version_control(enhanced_content, version, author)

                # Display enhanced content
                st.markdown("### Enhanced Document")
                st.markdown(enhanced_content)

                # Download options
                st.markdown("### Download Options")
                col5, col6 = st.columns(2)
                
                with col5:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        "Download as Markdown",
                        enhanced_content,
                        file_name=f"enhanced_doc_{timestamp}.md",
                        mime="text/markdown"
                    )
                
                with col6:
                    pdf_buffer = create_pdf(enhanced_content)
                    st.download_button(
                        "Download as PDF",
                        pdf_buffer,
                        file_name=f"enhanced_doc_{timestamp}.pdf",
                        mime="application/pdf"
                    )

    else:
        st.info("Please provide a document to analyze") 