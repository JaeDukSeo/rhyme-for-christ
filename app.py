import re 
import nltk
import math
import colorama
import pronouncing
from ansi2html import Ansi2HTMLConverter
from io import StringIO
import sys
import itertools

from sty         import bg 
from flask       import Flask, render_template, request, jsonify
from colorama    import init
from collections import Counter

from g2p_en import G2p
g2p = G2p()


nltk.download('punkt')
nltk.download('cmudict')
nltk.download('averaged_perceptron_tagger_eng')
init()

app     = Flask(__name__)
entries = nltk.corpus.cmudict.entries()

def get_word_pronunciation(word):
    """Get pronunciation using g2p_en"""
    try:
        phones = g2p(word)
        return ' '.join(phones)
    except:
        return None

def get_perfect_rhymes(word):
    """Find perfect rhymes (exact vowel and final consonant match)"""
    phones = get_word_pronunciation(word)
    if not phones:
        return []
    return pronouncing.rhymes(word)

def get_slant_rhymes(word):
    """Find slant rhymes (similar but not identical sounds)"""
    phones = get_word_pronunciation(word)
    if not phones:
        return []
    
    # Get the rhyming part of the word
    rhyming_part = pronouncing.rhyming_part(phones)
    # Search for words with similar ending sounds
    similar = pronouncing.search(rhyming_part)
    # Remove perfect rhymes from slant rhymes
    perfect = set(get_perfect_rhymes(word))
    return [w for w in similar if w not in perfect]

def get_eye_rhymes(word):
    """Find eye rhymes (words that look similar but don't rhyme)"""
    # Get words that end with the same letters but don't rhyme
    word_end = word[-3:] if len(word) >= 3 else word
    eye_rhymes = []
    for entry in entries:
        entry_word = entry[0]
        if entry_word.endswith(word_end) and entry_word != word:
            # Check if they don't rhyme
            if not pronouncing.rhymes(word):
                eye_rhymes.append(entry_word)
    return eye_rhymes

def get_assonance(word):
    """Find words with matching vowel sounds"""
    phones = get_word_pronunciation(word)
    if not phones:
        return []
    
    # Get the stressed vowels from the word
    vowel_sounds = [p for p in phones.split() if p[-1] in '012']
    if not vowel_sounds:
        return []
    
    # Find words with matching vowel sounds
    assonance_words = []
    for entry in entries:
        entry_word = entry[0]
        if entry_word != word:
            entry_phones = get_word_pronunciation(entry_word)
            if entry_phones:
                entry_vowels = [p for p in entry_phones.split() if p[-1] in '012']
                if entry_vowels and vowel_sounds[0] == entry_vowels[0]:
                    assonance_words.append(entry_word)
    return assonance_words

def get_consonance(word):
    """Find words with matching consonant sounds"""
    phones = get_word_pronunciation(word)
    if not phones:
        return []
    
    # Get the consonant sounds from the word
    consonant_sounds = [p for p in phones.split() if p[-1] not in '012']
    if not consonant_sounds:
        return []
    
    # Find words with matching consonant sounds
    consonance_words = []
    for entry in entries:
        entry_word = entry[0]
        if entry_word != word:
            entry_phones = get_word_pronunciation(entry_word)
            if entry_phones:
                entry_consonants = [p for p in entry_phones.split() if p[-1] not in '012']
                if entry_consonants and consonant_sounds[-1] == entry_consonants[-1]:
                    consonance_words.append(entry_word)
    return consonance_words

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/find-simple', methods=['POST'])
def find_simple():
    try:
        pattern = request.json.get('word', '').lower().strip()
        if not pattern:
            return jsonify({'error': 'No pattern provided'}), 400
            
        # Sort results and remove duplicates
        pronunciations = g2p(pattern)
        pronunciations = ' '.join(pronunciations)
        similar_words  = pronouncing.search(pronunciations)
        similar_words  = similar_words 
                
        # Sort by length and limit results
        similar_words = sorted(similar_words)
        
        # Add pronunciation info to response
        return jsonify({
            'rhymes': similar_words,
        })
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Error processing "{pattern}": {str(e)}'}), 500

@app.route('/find-similar', methods=['POST'])
def find_similar():
    try:
        pattern = request.json.get('word', '').lower().strip()
        print(pattern)
        print(pattern)
        print(pattern)
        print(pattern)
        print(pattern)
        if not pattern:
            return jsonify({'error': 'No pattern provided'}), 400
            
        results = {
            'perfect_rhymes': get_perfect_rhymes(pattern),
            'slant_rhymes': get_slant_rhymes(pattern),
            'eye_rhymes': get_eye_rhymes(pattern),
            'assonance': get_assonance(pattern),
            'consonance': get_consonance(pattern)
        }
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


