import pickle
import argparse
import re 
import math



def main(TableDir, LexcFile):
    table = pickle.load(open(TableDir, "rb" ))

    flat_counts = table['flat']
    global_count = table['count']

    # add the TAM counts to the flat table (its a bug that the original transition count script doesnt already do this)
    pstperf = table['matrix']['ROOT']['[PstPerf]']
    pstimperf = table['matrix']['ROOT']['[PstImperf]']
    nonpst = table['matrix']['ROOT']['[NonPst]']
    imp = table['matrix']['ROOT']['[Imp]']
    irr = table['matrix']['ROOT']['[Irr]']
    flat_counts['[PstImperf]'] = pstimperf
    flat_counts['[PstPerf]'] = pstperf
    flat_counts['[NonPst]'] = nonpst
    flat_counts['[Imp]'] = imp
    flat_counts['[Irr]'] = irr

    #write_dict(flat_counts)
    lexc = read_lexc(LexcFile)

    #iteratethrough the sections
    for sec in lexc['sections']:
        #total_sec_count = 0
        # gather counts per line
        counts_per_line = {}
        if sec != "":
            for i, line in enumerate(lexc['sections'][sec]):
                if ":" in line:
                    tag = line.split(":")[0]
                    tag = clean_tag(tag)
                    if tag != '0': # then it is emitting a tag we have a count for
                        # look up the tag in the count dictionary
                        count = 1
                        if tag in flat_counts:
                            count = flat_counts[tag]
                        sec_idx = i
                        counts_per_line[sec_idx] = count
                        #total_sec_count += count
            # from gathered section and line counts, calculate a likelihood distribution over the section
            for idx, counts in counts_per_line.items():
                neglogprob = -math.log(counts/float(global_count))
                lexc['sections'][sec][idx]= re.sub(";", " \"weight: " + str(neglogprob) + "\" ;", lexc['sections'][sec][idx])
    
    write_lexc(lexc)

def write_lexc(lexc):
    header = lexc['header']
    sections = lexc['sections']

    with open('kunwok.weighted.lexc', "w") as f:
        for row in header:
            f.write(row)
        for lexicon, transitions in sections.items():
            f.write(lexicon)
            for transition in transitions:
                f.write(transition)

def read_lexc(pathToLexc):
    """Read a lexc file, segment by LEXICON sections, 
    and annotate transitions with the -log(P(x)) normalized by section
    
    Arguments:
        pathToLexc {str} -- The path to the Lexc file we want to annotate
    """
    with open(pathToLexc, "r") as f:
        lexclines = f.readlines()
    
    # first, find the beginning of the LEXICON sections
    start_idx = 0
    for i, l in enumerate(lexclines):
        if "LEXICON" in l:
            start_idx = i
            break
    
    # from the start, segment doc by lexicon collections
    state_transitions = {}
    current_bucket_name = ""
    current_bucket = []
    for line in lexclines[start_idx:]:
        if "LEXICON" in line: # start processing a lexicon section
            state_transitions[current_bucket_name] = current_bucket
            current_bucket = []
            current_bucket_name = line
        else:
            current_bucket.append(line)
    return {'sections': state_transitions, 'header': lexclines[:start_idx]}

def clean_tag(tag):
    tag = re.sub('\@.*?\@', "", tag)
    tag = re.sub('\[V\]', '', tag)
    return tag

def write_dict(d):
    with open('flat_counts.txt', "w") as f:
        for k,v in d.items():
            f.write("\"" + k + " : " + str(v) + '\",\n')

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Process')
    parser.add_argument('-t', action='store', dest='TransitionsTable',
                    help='Path to transitions table')
    parser.add_argument('-l', action='store', dest='LexcFile',
                    help='Path to lexc file')
    
    args = parser.parse_args()
    main(args.TransitionsTable, args.LexcFile)