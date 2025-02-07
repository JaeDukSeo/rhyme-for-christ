import re 
import nltk
import math
import colorama
import pronouncing
from ansi2html import Ansi2HTMLConverter
from io import StringIO
import sys

from sty         import bg 
from flask       import Flask, render_template, request, jsonify
from colorama    import init
from collections import Counter

init()

class Rhyme_pair:
    """
    A pair of rhyming chunks, according to specified rhyming thresholds.
    """
    def __init__(self, idx, chunk1, chunk2, rhyme_nums):
        self.idx = idx
        if chunk1.color == chunk2.color:
            self.color = chunk1.color
        else:
            self.color = chunk1.color  # maybe make half rhymes grey (128,128,128)
        self.rhyme_nums = rhyme_nums   # the distance, allit score, and stress score for the rhyme pair
        self.idx1 = chunk1.idx
        self.idx2 = chunk2.idx
        self.chunk1 = chunk1
        self.chunk2 = chunk2
        

class Alliteration_pair:
    """
    A pair of alliterating consonant groups, according to specified alliteration threshold.
    """
    def __init__(self, congrp1, congrp2, score):
        self.score = score
        self.idx1 = congrp1.idx
        self.idx2 = congrp2.idx
        self.color = congrp1.color
        self.congrp1 = congrp1
    
    def get_color(self):
        return self.congrp1.get_color()


class Chunk:
    """
    A chunk consisting of a vowel and the consonant group which appears after it.
    """
    def __init__(self, vowel, congrp, idx):
        self.vowel = vowel
        self.congrp = congrp
        self.color = vowel.color
        self.root_word = vowel.root_word
        self.name = vowel.name
        self.idx = idx
        self.vowel_idx = vowel.idx
        
    def __lt__(self, other):  # allows sorting based on class attributes
        return self.idx < other.idx
    
    def compare_to_chunk(self, other_chunk):  # USE FOR RHYME DETECTION
        """
        Look at how similar the vowels in each chunk are, and how similar the consonants in each chunks congrp is.
        These comparisons are compared to a threshold to decide if two chunks rhyme or not.
        """
        vowel_dist = self.vowel.distanceFromPoint(other_chunk.vowel)
        con_dist = self.congrp.compare_to_congrp(other_chunk.congrp)
        stress_dist = self.vowel.stressCompare(other_chunk.vowel)
        return vowel_dist, con_dist, stress_dist


class Con_grp:
    """
    A group of consonants, either occuring before (bv) or after a vowel.
    """
    def __init__(self, idx):
        self.congrp_list = []
        self.consonant_list = []
        self.idx = idx
        self.color = (255, 255, 255)
    
    def __lt__(self, other):  # allows sorting based on class attributes
        return self.idx < other.idx
        
    def add_consonant(self, consonant):
        self.consonant_list.append(consonant)
        return self.consonant_list
    
    def get_consonant(self, idx):
        return self.consonant_list[idx]
    
    def get_color(self): 
        if len(self.consonant_list) > 0:
            self.color = self.consonant_list[0].color
        else:
            self.color = (255, 255, 255)
        return self.color
    
    def compare_to_congrp(self, other_congrp):  # USE FOR ALLITERATION DETECTION
        """
        The consonant similarities are calculated and compared to the alliteration threshold.
        """
        con_list = self.consonant_list
        other_list = other_congrp.consonant_list
        compar_list = [(n, m) for n in con_list for m in other_list]
        con_compars = [compar_list[i][0].distanceFromPoint(compar_list[i][1]) for i in range(len(compar_list))]
        
        if len(self.consonant_list) > 0 or len(other_list) > 0:
            if len(self.consonant_list) == 0 or len(other_list) == 0:
                score = 3  # need to fix this, works for rhymes like this
                # (bay and bane should rhyme) but not for alliteration
                # (and and sand shouldn't alliterate)
            else:
                score = sum(con_compars)/max(len(self.consonant_list), len(other_list))
                # ensure that all the consonants score highly for similarity in congrp,
                # avoids things like get and hemmed showing up as rhyme
        else:
            if len(other_list) == 0: # if both lists are empty say they alliterate
                score = 3
#            else:
#                score = 0  # if one is empty and the other isn't then they can't alliterate
        return score


class Consonant:
    """
    A single consonant object.
    """
    def __init__(self, idx, name, position, color, root_word): # name as in the representative arpabet symbol
        self.position = position
        self.name = name
        self.color = color
        self.root_word = root_word
        self.idx = idx  # position in lyric
        
    def __lt__(self, other):  # allows sorting based on class attributes
        return self.idx < other.idx
        
    def getX(self):  # used only for shorthand
        return self.position[0]

    def getY(self):  # used only for shorthand
        return self.position[1]    
        
    def getZ(self):  # used only for shorthand
        return self.position[2] 
        
    def distanceFromPoint(self, otherP):
        """
        Get the 'distance' from this consonant to an another, i.e. compare the coordinates 
        of each consonant as they lie in the consonant space defined by consonant_color_dict
        """
        score = 0
        if otherP.getX() == self.position[0]:
            score += 1
            if otherP.getY() == self.position[1]:
                score += 1
                if otherP.getZ() == self.position[2]:
                    score += 1
        return score  # Same group; score 1, same subgp; score 2, same consonant; score 3


class Vowel:
    """
    A single vowel object.
    """
    def __init__(self, idx, name, position, color, root_word, stress):
        self.position = position
        self.name = name
        self.color= color
        self.root_word = root_word
        self.idx = idx
        self.stress = stress
        
    def getX(self):  # used only for shorthand
        return self.position[0]

    def getY(self):  # used only for shorthand
        return self.position[1]    
        
    def getZ(self):  # used only for shorthand
        return self.position[2] 
    
    def getStress(self):  # used only for shorthand
        return self.stress
        
    def distanceFromPoint(self, otherP):
        """
        Get the 'distance' from this vowel to an another, i.e. compare the coordinates 
        of each vowel as they lie in the vowel space defined by vowel_color_dict
        """
        dx = (otherP.getX() - self.position[0])
        dy = (otherP.getY() - self.position[1])
        dz = (otherP.getZ() - self.position[2])
        return math.sqrt(dz**2 + dy**2 + dx**2)
    
    def stressCompare(self, other):
        return abs(other.stress-self.stress), other.stress+self.stress
        # if the sum is zero, then we know both stresses are zero.

# Vowel colors optimized for black background visibility
vowel_color_dict = {'AA': [(0, 255, 0), (4, 0, 0)],      # bright green
                    'AE': [(255, 200, 0), (0, 1, 0)],     # golden yellow
                    'AH': [(0, 255, 128), (4, 2, 0)],     # spring green
                    'AO': [(0, 191, 255), (4, 2, 2)],     # deep sky blue
                    'AW': [(64, 224, 208), (1.5, 2.5, 1)],# turquoise
                    'AX': [(192, 192, 192), (2, 3, 1)],   # silver
                    'AY': [(255, 165, 0), (0.5, 2.5, 0)], # orange
                    'EH': [(255, 140, 0), (0, 2, 0)],     # dark orange
                    'ER': [(173, 255, 47), (2, 2, 0)],    # green yellow
                    'EY': [(255, 69, 0), (0, 4, 0)],      # red orange
                    'IH': [(255, 20, 147), (1, 5, 0)],    # deep pink
                    'IX': [(255, 105, 180), (2, 6, 0)],   # hot pink
                    'IY': [(255, 0, 255), (0, 6, 0)],     # magenta
                    'OW': [(30, 144, 255), (3.5, 4.5, 2)],# dodger blue
                    'OY': [(147, 112, 219), (2.5, 3.5, 1)],# medium purple
                    'UH': [(138, 43, 226), (3, 5, 2)],    # blue violet
                    'UW': [(0, 0, 255), (4, 6, 2)],       # blue
                    'UX': [(148, 0, 211), (2, 6, 2)]}     # dark violet

# Consonant colors optimized for black background visibility
consonant_color_dict = {'B': [(255, 128, 0), (1, 1, 0)],  # dark orange
                       'P': [(255, 128, 0), (1, 1, 1)],
                       'D': [(255, 140, 0), (1, 2, 0)],    # orange red
                       'T': [(255, 140, 0), (1, 2, 1)],
                       'G': [(255, 69, 0), (1, 3, 0)],     # red orange
                       'K': [(255, 69, 0), (1, 3, 1)],
                       'F': [(0, 255, 127), (2, 1, 0)],    # spring green
                       'V': [(0, 255, 127), (2, 1, 1)],
                       'S': [(60, 179, 113), (2, 2, 0)],   # medium sea green
                       'Z': [(60, 179, 113), (2, 2, 1)],
                       'SH': [(46, 139, 87), (2, 3, 0)],   # sea green
                       'TH': [(46, 139, 87), (2, 3, 1)],
                       'DH': [(32, 178, 170), (2, 4, 0)],  # light sea green
                       'HH': [(32, 178, 170), (2, 4, 1)],
                       'CH': [(127, 255, 0), (3, 1, 0)],   # chartreuse
                       'JH': [(127, 255, 0), (3, 1, 1)],
                       'M': [(255, 0, 255), (4, 1, 1)],    # magenta
                       'N': [(255, 20, 147), (4, 1, 2)],   # deep pink
                       'NG': [(255, 105, 180), (4, 1, 3)], # hot pink
                       'W': [(0, 255, 255), (5, 1, 0)],    # cyan
                       'Y': [(0, 206, 209), (5, 2, 0)],    # dark turquoise
                       'L': [(72, 209, 204), (5, 3, 0)],   # medium turquoise
                       'R': [(64, 224, 208), (5, 4, 0)]}   # turquoise

T1 = 2.5  # Rhyme stressed vowel threshold
T2 = 1    # Rhyme stressed vowel consonance threshold
T3 = 4    # Rhyme unstressed vowel threshold
T4 = 1    # Rhyme unstressed vowel consonance threshold
T5 = 3    # Alliteration threshold

app = Flask(__name__)
nltk.download('cmudict')
entries = nltk.corpus.cmudict.entries()

def split_lyrics_pronouncing(text):
    """
    Convert text to phonetic pronunciations using the pronouncing library
    """
    line_arpas = []
    arpa_words = []
    
    for word in text:
        if word == '\n':
            line_arpas.append('LINEBREAK')
            arpa_words.append('LINEBREAK')
            continue
            
        pronunciations = pronouncing.phones_for_word(word.lower())
        if pronunciations:
            phones = pronunciations[0].split()
            line_arpas.extend(phones)
            arpa_words.extend([word] * len(phones))
    
    return line_arpas, arpa_words

def contain_nums(s):
    return any(i.isdigit() for i in s)

def generate_pairs(chunks):
    """
    Generate all possible permutations of length 2 (order doesn't matter)
    """
    outcomes = chunks
    length = 2
    ans = set([()])
    for dummy_idx in range(length):
        temp = set()
        for seq in ans:
            for item in outcomes:
                if item not in seq:
                    new_seq = list(seq)
                    new_seq.append(item)
                    temp.add(tuple(new_seq))
        ans = temp
    sorted_sequences = [tuple(sorted(sequence)) for sequence in ans]
    return set(sorted_sequences)

def get_components(line_arpas, arpa_words):
    """
    Extract the vowels and consonants from the lyrics
    """
    # Check for empty inputs
    if not line_arpas or not arpa_words:
        return [], [], []

    vowels = []
    for i in range(len(line_arpas)):
        # Skip empty strings and linebreaks
        if not line_arpas[i] or line_arpas[i] == 'LINEBREAK':
            continue
        # Only process if contains numbers and is a valid vowel
        if contain_nums(line_arpas[i]):
            cleaned_arpa = re.sub(r'\d+', '', line_arpas[i])
            if cleaned_arpa in vowel_color_dict:
                vowels.append(Vowel(
                    i, 
                    line_arpas[i], 
                    vowel_color_dict[cleaned_arpa][1],
                    vowel_color_dict[cleaned_arpa][0], 
                    arpa_words[i], 
                    int(re.sub('[^0-9]', '', line_arpas[i]))
                ))
    
    consonants = []
    for i in range(len(line_arpas)):
        # Skip empty strings and linebreaks
        if not line_arpas[i] or line_arpas[i] == 'LINEBREAK':
            continue
        # Only process if doesn't contain numbers and is a valid consonant
        if not contain_nums(line_arpas[i]):
            cleaned_arpa = re.sub(r'\d+', '', line_arpas[i])
            if cleaned_arpa in consonant_color_dict:
                consonants.append(Consonant(
                    i,
                    line_arpas[i],
                    consonant_color_dict[cleaned_arpa][1],
                    consonant_color_dict[cleaned_arpa][0],
                    arpa_words[i]
                ))
    
    vowel_words = [vow.root_word for vow in vowels]
    
    return vowels, consonants, vowel_words

def group_components(vowels, consonants, vowel_words):
    """
    group the component vowels and consonants into 3 groups; the group of consonants that come after each vowel in a word,
    the group of consonants that come before each vowel in a word, and chunks, which are pairings of vowels and the
    consonant group which immediately follows it.
    """
    
    congrps = [Con_grp(i) for i in range(len(vowel_words))]
    # these are the groups of consonants that come after a vowel in a word,
    # 1 letter words like "a" will generate an empty group

    for i in range(len(vowel_words)):  # add consonants that appear after vowels to the consonant groups
        for con in consonants:
            if con.root_word == vowel_words[i] and con.idx>vowels[i].idx:
                if i < (len(vowel_words)-1):
                    if con.idx < vowels[i+1].idx:  # make sure we don't get consonants after next syllables in word too
                        congrps[i].add_consonant(con)
                else:
                     congrps[i].add_consonant(con)
                               
    congrps_bv = [Con_grp(i) for i in range(len(vowel_words))]

    for i in range(len(vowel_words)):  # add consonants that appear before vowels to the consonant groups
        for con in consonants:
            if con.root_word == vowel_words[i] and con.idx < vowels[i].idx:
                if i > 0:
                    if con.idx > vowels[i-1].idx:  # make sure we don't get repeats for the same word
                        congrps_bv[i].add_consonant(con)
                else:
                    congrps_bv[i].add_consonant(con)

    chunks = [Chunk(vowels[i], congrps[i], i) for i in range(len(vowels))]  # define the chunks,
    #  i.e. the vowel and end consonant group pairs
    
    return congrps, congrps_bv, chunks

def generate_goodness_pairs(congrps, congrps_bv, chunks, t1, t2, t3, t4):
    # thresholds for rhyming strictness, see config
    """
    Generate rhyming and alliterating pairs by comparing every possible permutation of chunks and before vowel congrps
    and taking the ones that score highly enough in similarity as specified by the thresholds.
    """
    # generate every pair (permutation) of chunks and compare them
    pairs = list(generate_pairs(chunks))
    
    # Compare the chunks in each pair, and store the result with the index of each
    chunk_compar = sorted([(pairs[i][0].compare_to_chunk(pairs[i][1]), pairs[i][0].idx,
                            pairs[i][1].idx) for i in range(len(pairs))])
    
    pairs_bv = list(generate_pairs(congrps_bv))
    
    # Compare the before vowel consonant groups in each pair, and store the comparison score with the index of each
    congrp_bv_compar = sorted([(pairs_bv[i][0].compare_to_congrp(pairs_bv[i][1]),
                                pairs_bv[i][0].idx, pairs_bv[i][1].idx) for i in range(len(pairs_bv))])
     
    # get the ids of the chunks associated with each ith comparison pair
    ids = [(i, chunk_compar[i][1], chunk_compar[i][2]) for i in range(len(chunk_compar))]
    scores = [chunk_compar[i][0] for i in range(len(chunk_compar))]  # just the scores returned from the class method
    
    rhymes = []
    for i in range(len(ids)): 
        if scores[i][2][1] == 0:  # if both stresses are zero in the pair
            if scores[i][0] < t3 and scores[i][1] > t4:  # rhyme threshold, more lenient for 0 stress
                rhymes.append((ids[i][1], ids[i][2], i))
        else:
            if scores[i][0] < t1 and scores[i][1] > t2:  # stricter rhyme threshold, higher stress
                rhymes.append((ids[i][1], ids[i][2], i))
                
    alliterations = []
    for i in range(len(congrp_bv_compar)):
        if congrp_bv_compar[i][0] > T5:  # alliteration threshold, i.e.e require consonants to be in the same group
            alliterations.append((congrp_bv_compar[i][1], congrp_bv_compar[i][2], congrp_bv_compar[i][0]))
    
    rhyme_pairs = [Rhyme_pair(i, chunks[rhymes[i][0]], chunks[rhymes[i][1]],
                              chunk_compar[rhymes[i][2]][0]) for i in range(len(rhymes))]
    # arranged as (COLOR, (DIST,ALLIT,STRESS), IDX OF THIS, IDX OF MATCH)
    
    alliteration_pairs = [Alliteration_pair(congrps_bv[alliterations[i][0]],
                                            congrps_bv[alliterations[i][1]], alliterations[i][2])
                          for i in range(len(alliterations))]
    
    return rhyme_pairs, alliteration_pairs

def reconstruct_lyrics(vowels, congrps, congrps_bv, chunks, rhyme_pairs, alliteration_pairs):
    """
    Prints the lyrics in arpabet form, with rhyme and alliteration pairing information printed next to each component.
    Printed in the form: (COLOR), SCORE, INDEX OF COMPONENTS INVOLVED IN PAIR
    e.g. the IH1 in pink matching with the IH1 in shift looks like (color of IH1, 
    (distance from IH1 to IH1=0,alliteration score which=1 since K and T share a group, and stress diff=0), 
    idx of pink's IH1 in the vowel list, idx of shift's IH1 in the vowel list)
    """
    # word reconstruction
    for j in range(len(vowels)):
        print(vowels[j].root_word)
        print([congrps_bv[j].consonant_list[i].name for i in range(len(congrps_bv[j].consonant_list))], 'bv',
              [(altr.score, altr.idx1, altr.idx2) for altr in alliteration_pairs if altr.idx1 == j or altr.idx2 == j])
        print([chunks[j].vowel.name], 'v',
              [(rhyme.rhyme_nums, rhyme.idx1, rhyme.idx2)
               for rhyme in rhyme_pairs if rhyme.idx1 == j or rhyme.idx2 == j])
        print([chunks[j].congrp.consonant_list[i].name for i in range(len(chunks[j].congrp.consonant_list))], 'av')
    return

def color_rhymes(vowels, rhyme_pairs, chunks):
    """
    Get the color for each vowel that is a member of a rhyme pair.
    """         
    colorids = []
    
    for j in range(len(vowels)):
        l = [rhyme.color for rhyme in rhyme_pairs if rhyme.idx1 == j or rhyme.idx2 == j]
        if len(l) > 0:
            colorids.append(l[0])
        else:
            colorids.append((255, 255, 255))
            
    return colorids 

def scheme(vowels, congrps_bv, chunks, colorids, original_text):
    """
    Captures the terminal output and converts it to HTML
    """
    # Create StringIO object to capture print output
    old_stdout = sys.stdout
    mystdout = StringIO()
    sys.stdout = mystdout
    
    original_lines = [line.strip() for line in original_text.strip().split('\n')]
    
    # Create a dictionary to store phonetic components for each word
    word_phonetics = {}
    current_word = None
    current_phonetics = []
    
    for j in range(len(vowels)):
        # Get consonants before vowel
        cons_before = [congrps_bv[j].consonant_list[i].name for i in range(len(congrps_bv[j].consonant_list))]
        if cons_before:
            phonetic_part = str(cons_before)
        
        # Get vowel and following consonants with color
        vowel_part = (bg(colorids[j][0], colorids[j][1], colorids[j][2]) + 
                     str([chunks[j].vowel.name]) +
                     str([chunks[j].congrp.consonant_list[i].name 
                          for i in range(len(chunks[j].congrp.consonant_list))]) + 
                     bg.rs)
        
        # Group phonetics by word
        if current_word != vowels[j].root_word:
            if current_word:
                word_phonetics[current_word] = current_phonetics
            current_word = vowels[j].root_word
            current_phonetics = []
        
        if cons_before:
            current_phonetics.append(phonetic_part)
        current_phonetics.append(vowel_part)
    
    # Add the last word
    if current_word:
        word_phonetics[current_word] = current_phonetics
    
    # Print original text and its phonetic transcription line by line
    for line in original_lines:
        print(line)
        phonetic_line = []
        for word in line.split():
            if word in word_phonetics:
                phonetic_line.extend(word_phonetics[word])
        print(' '.join(phonetic_line))
        print()  # Empty line for readability
    
    # Get the printed output
    output = mystdout.getvalue()
    sys.stdout = old_stdout
    
    # Convert ANSI colors to HTML
    conv = Ansi2HTMLConverter()
    html = conv.convert(output)
    
    return html

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        text = request.json.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Process the entire text at once
        w = []
        lines = text.strip().split('\n')
        for line in lines:
            w.extend(line.strip().split())
            w.append('\n')
        w = w[:-1]
        
        line_arpas, arpa_words = split_lyrics_pronouncing(w)
        
        if line_arpas and arpa_words:
            vowels, consonants, vowel_words = get_components(line_arpas, arpa_words)
            if vowels and consonants:
                congrps, congrps_bv, chunks = group_components(vowels, consonants, vowel_words)
                rhyme_pairs, alliteration_pairs = generate_goodness_pairs(congrps, congrps_bv, chunks, T1, T2, T3, T4)
                colorids = color_rhymes(vowels, rhyme_pairs, chunks)
                
                # Get the HTML-converted terminal output
                html_output = scheme(vowels, congrps_bv, chunks, colorids, text)
                return jsonify({'result': html_output})
            
        return jsonify({'error': 'Could not process text'}), 400
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)


