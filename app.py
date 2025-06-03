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

def get_phrase_pronunciation(phrase):
    """Get the pronunciation of a phrase"""
    words = phrase.lower().split()
    phones = []
    for word in words:
        word_phones = pronouncing.phones_for_word(word)
        if word_phones:
            phones.extend(word_phones[0].split())
    return ' '.join(phones)

def get_phrase_stress(phrase):
    """Get the stress pattern of a phrase"""
    phones = get_phrase_pronunciation(phrase)
    if not phones:
        return ''
    return pronouncing.stresses(phones)

def get_multisyllabic_rhymes(phrase):
    """Find multisyllabic rhymes for a phrase"""
    # Get the stress pattern and pronunciation of the input phrase
    phrase_stress = get_phrase_stress(phrase)
    phrase_phones = get_phrase_pronunciation(phrase)
    
    if not phrase_stress or not phrase_phones:
        return []
    
    # Get the number of words in the input phrase
    num_words = len(phrase.split())
    
    # Find potential rhyming phrases
    rhyming_phrases = []
    
    # Create combinations of words that could form phrases
    for i in range(2, min(5, num_words + 2)):  # Try phrases of 2-4 words
        for words in itertools.combinations(entries, i):
            # Create a potential phrase
            potential_phrase = ' '.join(word[0] for word in words)
            
            # Skip if it's the same as input phrase
            if potential_phrase.lower() == phrase.lower():
                continue
                
            # Get the stress pattern of the potential phrase
            potential_stress = get_phrase_stress(potential_phrase)
            potential_phones = get_phrase_pronunciation(potential_phrase)
            
            # Check if the stress patterns match
            if potential_stress == phrase_stress:
                # Get the rhyming parts of both phrases
                phrase_rhyming = pronouncing.rhyming_part(phrase_phones)
                potential_rhyming = pronouncing.rhyming_part(potential_phones)
                
                # If the rhyming parts match, it's a valid multisyllabic rhyme
                if phrase_rhyming == potential_rhyming:
                    rhyming_phrases.append(potential_phrase)
    
    return rhyming_phrases[:20]  # Limit to 20 results for performance

def get_perfect_rhymes(word):
    """Find perfect rhymes (exact vowel and final consonant match)"""
    return pronouncing.rhymes(word)

def get_slant_rhymes(word):
    """Find slant rhymes (similar but not identical sounds)"""
    # Get the pronunciation of the word
    phones = pronouncing.phones_for_word(word)
    if not phones:
        return []
    
    # Get the rhyming part of the word
    rhyming_part = pronouncing.rhyming_part(phones[0])
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
    phones = pronouncing.phones_for_word(word)
    if not phones:
        return []
    
    # Get the stressed vowels from the word
    phones_str = phones[0]
    vowel_sounds = [p for p in phones_str.split() if p[-1] in '012']
    if not vowel_sounds:
        return []
    
    # Find words with matching vowel sounds
    assonance_words = []
    for entry in entries:
        entry_word = entry[0]
        if entry_word != word:
            entry_phones = pronouncing.phones_for_word(entry_word)
            if entry_phones:
                entry_vowels = [p for p in entry_phones[0].split() if p[-1] in '012']
                if entry_vowels and vowel_sounds[0] == entry_vowels[0]:
                    assonance_words.append(entry_word)
    return assonance_words 

def get_consonance(word):
    """Find words with matching consonant sounds"""
    phones = pronouncing.phones_for_word(word)
    if not phones:
        return []
    
    # Get the consonant sounds from the word
    phones_str = phones[0]
    consonant_sounds = [p for p in phones_str.split() if p[-1] not in '012']
    if not consonant_sounds:
        return []
    
    # Find words with matching consonant sounds
    consonance_words = []
    for entry in entries:
        entry_word = entry[0]
        if entry_word != word:
            entry_phones = pronouncing.phones_for_word(entry_word)
            if entry_phones:
                entry_consonants = [p for p in entry_phones[0].split() if p[-1] not in '012']
                if entry_consonants and consonant_sounds[-1] == entry_consonants[-1]:
                    consonance_words.append(entry_word)
    return consonance_words 

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/find-similar', methods=['POST'])
def find_similar():
    try:
        pattern = request.json.get('word', '').lower().strip()
        if not pattern:
            return jsonify({'error': 'No pattern provided'}), 400
            
        results = {
            'perfect_rhymes': get_perfect_rhymes(pattern),
            'slant_rhymes': get_slant_rhymes(pattern),
            'eye_rhymes': get_eye_rhymes(pattern),
            'assonance': get_assonance(pattern),
            'consonance': get_consonance(pattern),
            'multisyllabic_rhymes': get_multisyllabic_rhymes(pattern)
        }
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


