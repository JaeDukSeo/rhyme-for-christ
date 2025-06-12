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
        similar_words_sounds = [' '.join(g2p(word)) for word in similar_words]
        
        # Add pronunciation info to response
        return jsonify({'rhymes': similar_words, 'sounds': similar_words_sounds})
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': f'Error processing "{pattern}": {str(e)}'}), 500
    
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


