import re 
import nltk
import math
import colorama
import pronouncing
import Levenshtein
import random

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

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/find-start', methods=['POST'])
def find_start():
    try:
        pattern = request.json.get('word', '').lower().strip()
        if not pattern:
            return jsonify({'error': 'No pattern provided'}), 400
            
        # Sort results and remove duplicates
        pronunciations = g2p(pattern)
        pronunciations = ' '.join(pronunciations)
        similar_words  = pronouncing.search("^" + pronunciations)
        similar_words  = similar_words 
                
        # Sort by length and limit results
        similar_words = sorted(similar_words)
        similar_words_sounds = [' '.join(g2p(word)) for word in similar_words]
        
        
        # Add pronunciation info to response
        return jsonify({'rhymes': similar_words, 'sounds': similar_words_sounds})
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Error processing "{pattern}": {str(e)}'}), 500
    
@app.route('/find-end', methods=['POST'])
def find_end():
    try:
        pattern = request.json.get('word', '').lower().strip()
        if not pattern:
            return jsonify({'error': 'No pattern provided'}), 400
            
        # Sort results and remove duplicates
        pronunciations = g2p(pattern)
        pronunciations = ' '.join(pronunciations)
        similar_words  = pronouncing.search(pronunciations + "$")
        similar_words  = similar_words 
                
        # Sort by length and limit results
        similar_words = sorted(similar_words)
        similar_words_sounds = [' '.join(g2p(word)) for word in similar_words]
        
        # Add pronunciation info to response
        return jsonify({'rhymes': similar_words, 'sounds': similar_words_sounds})
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Error processing "{pattern}": {str(e)}'}), 500







@app.route('/find-end-near', methods=['POST'])
def find_end_near():
    try:
        pattern = request.json.get('word', '').lower().strip()
        if not pattern:
            return jsonify({'error': 'No pattern provided'}), 400

        # Get phonemes and stress pattern for the input word
        input_phonemes = [p for p in g2p(pattern) if p.isalpha()]
        if not input_phonemes:
            return jsonify({'error': f'No phonemes found for "{pattern}"'}), 404
        input_string = ' '.join(input_phonemes)

        # Collect candidate words by searching progressively shorter suffixes
        candidate_words = set()  # Use set to avoid duplicates
        
        # For each suffix starting from full phonemes down to last phoneme
        for i in range(len(input_phonemes)):
            suffix_phonemes = input_phonemes[i:]  # Get suffix from position i to end
            suffix_pattern = ' '.join(suffix_phonemes)
            
            # Find words ending with this suffix pattern
            suffix_words = pronouncing.search(suffix_pattern + "$")
            
            # Filter and add to candidates
            for word in suffix_words:
                if (word != pattern 
                    and word.isalpha() 
                    and len(word) >= 3 
                    and word.islower()):
                    candidate_words.add(word)
        
        candidate_words = list(candidate_words)  # Convert back to list

        # Compute phoneme similarity using Levenshtein
        scored = []
        for word in candidate_words:
            word_phonemes = [p for p in g2p(word) if p.isalpha()]
            if not word_phonemes:
                continue
            word_string = ' '.join(word_phonemes)
            score = Levenshtein.ratio(input_string, word_string)
            if score >= 0.8:
                print(word,score)
                scored.append((word, word_string, score))

        # Sort by alphabet
        scored = sorted(scored, key=lambda x: x[0])

        return jsonify({
            'rhymes': [w for w, _, _ in scored],
            'sounds': [s for _, s, _ in scored],
            'scores': [sc for _, _, sc in scored]
        })

    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Error processing "{pattern}": {str(e)}'}), 500










@app.route('/find-end-looser', methods=['POST'])
def find_end_looser():
    try:
        pattern = request.json.get('word', '').lower().strip()
        if not pattern:
            return jsonify({'error': 'No pattern provided'}), 400
            
        # Sort results and remove duplicates
        pronunciations = g2p(pattern)
        pronunciations = ' '.join(pronunciations)
        similar_words  = pronouncing.search(pronunciations + ".?$")
        similar_words  = similar_words 
                
        # Sort by length and limit results
        similar_words = sorted(similar_words)
        similar_words_sounds = [' '.join(g2p(word)) for word in similar_words]
        
        # Add pronunciation info to response
        return jsonify({'rhymes': similar_words, 'sounds': similar_words_sounds})
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Error processing "{pattern}": {str(e)}'}), 500
    
    
@app.route('/find-anywhere', methods=['POST'])
def find_anywhere():
    print('here')
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
    similar_words_sounds = [' '.join(g2p(word)) for word in similar_words]
    # Add pronunciation info to response
    return jsonify({'rhymes': similar_words, 'sounds': similar_words_sounds})
        
    
@app.route('/find-middle', methods=['POST'])
def find_middle():
    try:
        pattern = request.json.get('word', '').lower().strip()
        if not pattern:
            return jsonify({'error': 'No pattern provided'}), 400
            
        # Sort results and remove duplicates
        pronunciations = g2p(pattern)
        pronunciations = ' '.join(pronunciations)
        similar_words  = pronouncing.search(".+ " + pronunciations + " .+")
        similar_words  = similar_words 
                
        # Sort by length and limit results
        similar_words = sorted(similar_words)
        similar_words_sounds = [' '.join(g2p(word)) for word in similar_words]
        
        # Add pronunciation info to response
        return jsonify({'rhymes': similar_words, 'sounds': similar_words_sounds})
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Error processing "{pattern}": {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)


