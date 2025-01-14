import logging
from typing import Dict, List, Optional
import re
from textblob import TextBlob
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.tag import pos_tag
from collections import Counter
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class DocumentAnalyzer:
    def __init__(self):
        """Initialize the DocumentAnalyzer"""
        pass

    def check_plagiarism(self, text: str) -> Dict[str, any]:
        """Check for potential plagiarism by searching for similar content"""
        try:
            # Split text into sentences using simple regex
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            results = []
            
            # Check random sample of sentences (to avoid API limits)
            for sentence in sentences[:5]:
                if len(sentence.split()) > 10:  # Only check substantial sentences
                    # Search for similar content
                    query = f'"{sentence}"'  # Exact match search
                    response = requests.get(
                        f"https://api.duckduckgo.com/?q={query}&format=json"
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('Results'):
                            results.append({
                                'sentence': sentence,
                                'potential_sources': [r['FirstURL'] for r in data['Results'][:3]]
                            })

            return {
                'has_matches': bool(results),
                'matches': results,
                'checked_sentences': len(sentences),
                'matched_sentences': len(results)
            }
        except Exception as e:
            logger.error(f"Error checking plagiarism: {str(e)}")
            return {'error': str(e)}

    def calculate_readability_score(self, text: str) -> Dict[str, float]:
        """Calculate various readability metrics"""
        try:
            # Split text into sentences and words using simple regex
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            words = [w.strip() for w in re.split(r'\s+', text) if w.strip()]
            
            # Basic calculations
            total_sentences = len(sentences)
            total_words = len(words)
            total_syllables = sum(self._count_syllables(word) for word in words)
            
            # Calculate scores
            flesch_reading_ease = 206.835 - 1.015 * (total_words / total_sentences) - 84.6 * (total_syllables / total_words)
            gunning_fog = 0.4 * ((total_words / total_sentences) + self._count_complex_words(words))
            
            return {
                'flesch_reading_ease': round(flesch_reading_ease, 2),
                'gunning_fog_index': round(gunning_fog, 2),
                'avg_sentence_length': round(total_words / total_sentences, 2),
                'avg_word_length': round(sum(len(word) for word in words) / total_words, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating readability: {str(e)}")
            return {'error': str(e)}

    def validate_technical_terminology(self, text: str, domain: str) -> Dict[str, any]:
        """Validate technical terminology usage and consistency"""
        try:
            # Split text into words using simple regex
            words = [w.strip() for w in re.split(r'\s+', text) if w.strip()]
            
            # Use basic POS tagging
            pos_tags = pos_tag(words)
            
            # Identify potential technical terms
            technical_terms = []
            term_frequencies = Counter()
            
            for word, pos in pos_tags:
                if pos in ['NN', 'NNP'] and len(word) > 3:  # Nouns that might be technical terms
                    technical_terms.append(word)
                    term_frequencies[word] += 1
            
            # Check consistency
            inconsistencies = []
            for term, freq in term_frequencies.items():
                variations = self._find_term_variations(text, term)
                if len(variations) > 1:
                    inconsistencies.append({
                        'term': term,
                        'variations': variations
                    })
            
            return {
                'technical_terms': list(term_frequencies.items()),
                'inconsistencies': inconsistencies,
                'term_count': len(technical_terms),
                'unique_terms': len(term_frequencies)
            }
        except Exception as e:
            logger.error(f"Error validating terminology: {str(e)}")
            return {'error': str(e)}

    def _count_syllables(self, word: str) -> int:
        """Count the number of syllables in a word"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"
        on_vowel = False
        in_diphthong = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not on_vowel:
                count += 1
            on_vowel = is_vowel

        # Adjust for special cases
        if word.endswith('e'):
            count -= 1
        if word.endswith('le') and len(word) > 2 and word[-3] not in vowels:
            count += 1
        if count == 0:
            count = 1

        return count

    def _count_complex_words(self, words: List[str]) -> float:
        """Count the percentage of complex words (words with 3+ syllables)"""
        complex_words = sum(1 for word in words if self._count_syllables(word) >= 3)
        return (complex_words / len(words)) * 100 if words else 0

    def _find_term_variations(self, text: str, term: str) -> List[str]:
        """Find variations of a technical term in the text"""
        variations = set()
        pattern = re.compile(rf'\b{re.escape(term)}[a-zA-Z]*\b', re.IGNORECASE)
        matches = pattern.finditer(text)
        for match in matches:
            variations.add(match.group())
        return list(variations) 

    def analyze_tone(self, text: str) -> Dict[str, any]:
        """Analyze the tone and sentiment of the documentation"""
        try:
            # Use TextBlob for sentiment analysis
            blob = TextBlob(text)
            
            # Get overall sentiment
            sentiment = blob.sentiment
            
            # Analyze sentences for tone variations
            sentence_tones = []
            for sentence in blob.sentences:
                if abs(sentence.sentiment.polarity) > 0.3:  # Only include significant tone changes
                    sentence_tones.append({
                        'text': str(sentence),
                        'polarity': round(sentence.sentiment.polarity, 2),
                        'subjectivity': round(sentence.sentiment.subjectivity, 2),
                        'tone': 'positive' if sentence.sentiment.polarity > 0 else 'negative'
                    })
            
            # Calculate tone statistics
            total_sentences = len(blob.sentences)
            positive_sentences = sum(1 for s in blob.sentences if s.sentiment.polarity > 0.1)
            negative_sentences = sum(1 for s in blob.sentences if s.sentiment.polarity < -0.1)
            neutral_sentences = total_sentences - positive_sentences - negative_sentences
            
            return {
                'overall_sentiment': {
                    'polarity': round(sentiment.polarity, 2),
                    'subjectivity': round(sentiment.subjectivity, 2)
                },
                'tone_distribution': {
                    'positive_percentage': round((positive_sentences / total_sentences) * 100, 1),
                    'negative_percentage': round((negative_sentences / total_sentences) * 100, 1),
                    'neutral_percentage': round((neutral_sentences / total_sentences) * 100, 1)
                },
                'significant_tone_variations': sentence_tones,
                'writing_style': {
                    'objectivity': 'high' if sentiment.subjectivity < 0.3 else 'medium' if sentiment.subjectivity < 0.6 else 'low',
                    'tone_consistency': 'high' if len(sentence_tones) < total_sentences * 0.1 else 'medium' if len(sentence_tones) < total_sentences * 0.2 else 'low'
                }
            }
        except Exception as e:
            logger.error(f"Error analyzing tone: {str(e)}")
            return {'error': str(e)} 