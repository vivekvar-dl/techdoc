# AI Technical Documentation Assistant

An AI-powered documentation assistant that leverages Google's Gemini API to analyze and generate technical documentation.

## Features

- **Document Analysis**: Analyzes existing documentation and provides:
  - Concise summaries
  - Key points and concepts
  - Improvement suggestions
  - Consistency checks
  - Areas needing more detail

- **Code Documentation Generation**: Automatically generates documentation from code:
  - Function descriptions
  - Parameter explanations
  - Return value details
  - Usage examples
  - Important notes

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add your Google API key:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
4. Run the application:
   ```bash
   streamlit run app.py
   ```

## Requirements

- Python 3.8+
- Google API key with access to Gemini API
- Required packages listed in requirements.txt

## Usage

1. Select mode from the sidebar (Document Analysis or Code Documentation)
2. Paste your content in the text area
3. Click the respective button to analyze or generate documentation
4. View the AI-generated results

## Limitations

- Requires domain-specific context for best results
- May need human review for complex technical concepts
- API rate limits may apply based on your Google API key 