from utilities.hfst_model import HFSTModel
import argparse
import re
import os
from os import listdir
from os.path import isfile, join

ALPHA_PATTERN = re.compile('[^a-zA-Z|\.]')
'''
define bilabilas ["b" | "bb"];
define bilabialNasals ["m"];
define bilabialSemivowel ["w"];
define velarStops ["k" | "kk" | "g"];
define velarNasal ["ng"];
define apicoStops ["d" | "dd" | "rd" | "rdd"];
define apicoNasals ["n" | "rn"];
define apicoLateral ["l" | "rl"];
define apicoRhotic ["rr" | "r"];
define palatalStops ["dj" | "djdj"];
define palatalNasals ["nj"];
define palatalSemivowels ["y"];
define glottalStop ["h"];
define flap ["d" | "rr"];
'''
ORTH_PATTERN = re.compile('bb|kk|ng|dd|rdd|rd|rn|rl|rr|djdj|dj|nj|rr|b|m|k|g|d|n|l|r|y|h|d|a|e|i|o|u|.') # Defines the graphems of Kunwinjku orthography
BX_PATTERN = re.compile("\^")

segmenter = HFSTModel('bin/segmenter-morph.hfst')


def main(in_dir):
    tokens = read_txtfiles_in_dir(in_dir)
    
    ############################
    # Get segmented sequence  ##
    ############################
    for fp, sentences in tokens.items():
        with open(os.path.join("outputs", fp.split(os.sep)[-1] + ".segmented.txt"), "w") as f:
            for toklist in sentences:
                segmented_tokens = []
                for tok in toklist:
                    seg_tok = segmenter.apply_down(tok.lower())
                    if len(seg_tok) > 0:
                        segmented_tokens.extend(replace_pattern(seg_tok[0], BX_PATTERN, " ").split()) # just take the first segmentation
                    else:
                        segmented_tokens.extend(character_segmenter(tok)) # otherwise, segment to syllables
                f.write(" ".join(segmented_tokens) + "\n")
                segmented_tokens = None

def character_segmenter(token):
    return re.findall(ORTH_PATTERN, token.lower())

def read_txtfiles_in_dir(in_dir):
    onlyfiles = [join(in_dir, f) for f in listdir(in_dir) if isfile(join(in_dir, f))]
    tokens = {}

    for filepath in onlyfiles:
        if filepath.endswith(".txt"):
            with open(filepath, 'r') as f:
                tokens[filepath] = []
                lines = f.readlines()
                for l in lines:
                    tokens[filepath].extend([replace_pattern(x, ALPHA_PATTERN, "") for x in l.split()])
    
                sentences = []
                sentence = []
                for tok in tokens[filepath]:
                    if tok.endswith("."): # this will be the last tok in the sentence
                        sentence.append(tok.rstrip("."))
                        sentences.append(sentence)
                        sentence = []
                    else:
                        sentence.append(tok)
                tokens[filepath] = sentences
    return tokens

def replace_pattern(text, pattern, replacement):
    return pattern.sub(replacement, text)


if __name__=="__main__":
    # parser = argparse.ArgumentParser(description="Segment a collection of texts in a given directory")
    # parser.add_argument('input_dir', metavar="InputDir", type=str)
    # args = parser.parse_args()
    #main(args.input_dir)
    main('/home/wlane/projects/kunwok_bible_corpus/')