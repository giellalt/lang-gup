import hfst
# hfst.set_default_fst_type(hfst.ImplementationType.) # we use foma implementation as there are no weights involved
import re, sys
import hfst
import grapheme
verbosity = 100


phones = 'kabiriwɔrwoɲlabalme' 
lexemes = 'kabirri barl'

multi_char_graphemes = [ "bb", "kk", "ng","dd","rdd", "rd", "rn", "rl", "rr", "djdj", "dj", "nj", "rr"]
fuzzy_spelling_rules = ["\"bb\" (->) [ \"b\" | \"m\" ]" ,
                    "\"ng\" -> [ \"ɲ\" | \"ŋ\" | \"n\" ]" ,
                    "\"dd\" -> [ \"t\" | \"n\" | \"d\" | \"ʈ\" | \"b\" ]",
                    "\"rdd\" -> [ \"ʈ\"| \"t\" | \"ɻ\" | \"d\"]" ,
                    "\"rd\" -> [ \"ʈ\" | \"t\" | \"ɻ\" | \"d\"]" ,
                    "\"rn\" -> [ \"ɳ\" | \"n\" | \"ɲ\"]" ,
                    "\"rl\" -> [ \"ɭ\" | \"l\" | \"r\" ]" ,
                    "\"rr\" -> [ \"r\" | \"ɹ\" ]" ,
                    "\"djdj\" -> [\"ɟ\" | \"k\" | \"ɲ\"]" ,
                    "\"dj\" -> [\"ɟ\" | \"k\" | \"ɲ\"]" ,
                    "\"nj\" -> [ \"ɲ\" | \"n\" | \"ŋ\" | \"ɟ\" | \"ɳ\" ]" ,
                    "\"b\" -> [ \"b\" | \"m\"]" ,
                    "\"m\" -> [ \"m\" | \"n\" | \"b\" ]" ,
                    "\"kk\" -> [ \"k\" | \"ɟ\" ]" ,
                    "\"k\" -> [ \"kk\" | \"ɟ\" ]" ,
                    "\"d\" -> [ \"t\" | \"n\" | \"d\" | \"ʈ\" | \"b\" ]" ,
                    "\"n\" -> [ \"n\" | \"m\" | \"ɳ\" | \"ɲ\" | \"ŋ\"]" ,
                    "\"l\" -> [ \"l\" | \"r\" | \"ɭ\" | \"t\"]" ,
                    "\"r\" -> [ \"l\" | \"ɭ\" ]" ,
                    "\"y\" -> [ \"j\" | \"ɪ\" | \"ɛ\" ]" ,
                    "\"h\" -> [ \"ʔ\" ]" ,
                    "\"a\" -> [ \"a\" | \"ɪ\" | \"ɔ\" | \"ɛ\" | \"ɐ\" ]" ,
                    "\"e\" -> [ \"ɛ\" | \"ɔ\" | \"ɪ\" | \"j\" ]" ,
                    "\"i\" -> [ \"i\" | \"ɪ\" | \"ɛ\" | \"j\" ]" ,
                    "\"o\" -> [ \"o\" | \"ɔ\" | \"u\"]" ,
                    "\"w\" -> [ \"w\" | \"u\" ]" ,
                    "\"u\" -> [ \"u\" | \"ɔ\" | \"ʊ\" ]"]

def main():
    # Create a simple lexicon transducer which respects graphemes as multichar symbols.
    tok = hfst.HfstTokenizer()
    for l in multi_char_graphemes:
         tok.add_multichar_symbol(l)
    t = hfst.tokenized_fst(tok.tokenize(" " + lexemes + " "))

    # Create a simple FSA which recognizes the phone string
    words = hfst.tokenized_fst(tok.tokenize(phones))

    # Create a rule transducer that replaces whitespace with 0 or more offset symbols Ø.
    rule = hfst.regex('[" " -> "Ø"*]') 
    rule2 = hfst.regex('[?]^' + str(len(phones))) # Limit the total offset size by the length of the phone string

    # Compose transducers to produce an FSA of all possible alignments of the lexemes to the phone stream
    t.compose(rule)
    t.compose(rule2)
    t.minimize()
    t.output_project() # takes output side language as FSA


    # Apply the rule transducer to the lexicon.
    noise = hfst.regex(fuzzy_spelling_rules[0])
    for r in fuzzy_spelling_rules[1:]:
        noise.compose(hfst.regex(r))

    # noise.invert()
    # noise = hfst.regex('"ɲ" -> [ "n" | "m" | "ng" | "nj" ]')
    noise.invert()
    words.compose(noise)
    words.output_project()

    t.cross_product(words)
    t.invert()


    #################################
    ###### Print FSM ################
    #################################
    # Extract all string pairs from the result and print them to standard output.
    # try:
        # Extract paths and remove tokenization
    results = t.extract_paths(output='dict')
    # except hfst.exceptions.TransducerIsCyclicException as e:
        # This should not happen because transducer is not cyclic.
        # print("TEST FAILED")
        # exit(1)
    
    for input,outputs in results.items():
        input_subbed= re.sub("@_EPSILON_SYMBOL_@", "", input)

        print('%s:' % input_subbed)
        for output in outputs:
            output_subbed= re.sub("@_EPSILON_SYMBOL_@", "", output[0])
            print('  %s\t%f' % (output_subbed, output[1]))

def shuffle_with_zeros(string, target_length):
    """Return a fsa where zeros are inserted in all possible ways in places where whitespace exists in the string
    
    string -- the string to which zero symbols are inserted at whitespace and boundaries, eg "kabirri om" -> ["0kabirri00000om00", etc]

    target_length -- how long the strings after insertions must be

    Returns a fsa which accepts all the strings with the inserted zeros.
    All strings have exactly target_length symbols.
    """    
    ### result_fsa = hfst.fst(string) # not correct for composed graphemes !!!
    result_fsa = string_to_fsa(string)

    l = grapheme.length(string)
    if l < target_length:
        n = target_length - l
        n_zeros_fsa = hfst.regex(" ".join(n * "Ø"))
        result_fsa.shuffle(n_zeros_fsa)
    
    result_fsa.minimize()
    result_fsa.set_name(string)
    if verbosity >= 30:
        print("shuffle_with_zeros:")
        print(result_fsa)
    return result_fsa

def string_to_fsa(string):
    """Return a FSA which accepts the sequence of graphemes in the string"""
    bfsa = hfst.HfstBasicTransducer()
    grapheme_list = list(grapheme.graphemes(string))
    string_pair_path = tuple(zip(grapheme_list, grapheme_list))
    if verbosity >= 10:
        print(grapheme_list)
        print(string_pair_path)
    bfsa.disjunct(string_pair_path, 0)
    fsa = hfst.HfstTransducer(bfsa)
    return(fsa)

if __name__== "__main__":
    main()