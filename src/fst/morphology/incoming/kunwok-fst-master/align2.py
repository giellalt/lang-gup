import hfst
import re


multi_char_graphemes = [ "bb", "kk", "ng","dd","rdd", "rd", "rn", "rl", "rr", "djdj", "dj", "nj"]
phon2orth_rules = [
    "b -> [ b | bb ]",
    "ɲ -> [ nj ]",
    "ŋ -> [ ng ]",
    "n -> [ n ]",
    "t -> [ d ]",
    "k -> [ k | kk ]",
    "d -> [ t | d ]",
    "ʈ -> [ rd | rdd ]",
    "ɻ -> [ rd | rdd ]",
    "ɳ -> [ rn ]",
    "ɭ -> [ rl ]",
    "l -> [ l ]",
    "r -> [ rr ]",
    "ɹ -> [ r ]",
    "ɟ -> [ dj | ddj ]",
    "m -> [ m ]",
    "ɪ -> [ i ]",
    "ɛ -> [ e ]",
    "ʔ -> [ h ]",
    "a -> [ a ]",
    "ɔ -> [ a | o]",
    "ɐ -> [ a ]",
    "j -> [ y ]",
    "o -> [ o ]",
    "u -> [ u ]",
    "ʊ -> [ u ]",
    "i -> [ i ]"
]

def main(phone_str, lexemes):

    tokd_lexemes = tokenize_lexemes(lexemes)

    stream = hfst.HfstInputStream('bin/kunwok.hfst')
    analyzer_fst = None
    if not stream.is_eof():
        analyzer_fst = stream.read()
    analyzer_fst.output_project()
    analyzer_fst.eliminate_flags()

    # turn phone_str and lexemes into FST strs
    phone_str_fst = hfst.regex('[ ' + ' '.join([x for x in phone_str]) + ' ]')
    lexemes_fst = hfst.regex('[ X ' + ' X'.join(tokd_lexemes.split('  ')) + ' X ]')
    print("LEXEMES_WORDS: " + '[ X ' + ' X'.join(tokd_lexemes.split('  ')) + ' X ]')

    # Build Lexeme transducer: Lexemes are represented as an FST which allows any char between lexemes in order
    # define LexemePattern [[LEXEMES .o. [X -> ?*]].i].u;
    lexemes_fst.compose(hfst.regex('[X -> ?*]'))
    lexemes_fst.invert()
    lexemes_fst.input_project()
    lexeme_pattern = lexemes_fst

    # Define useful edit distance FSTs
    # define Edit1 [?* [?:0|0:?] ?*]^<2;
    # define Edit2 [?* [?:0|0:?] ?*]^<3;
    edit1 = hfst.regex('[?* [?:0|0:?] ?*]^<2')
    edit2 = hfst.regex('[?* [?:0|0:?] ?*]^<3')

    ######################
    ##   GENERATION     ##
    ######################

    # Turn phone stream into FSA of all possible orthographic realizations
    # define OrthStrs  [phone_str_fst  .o. NoisyPhones];
    noisy_phones = hfst.regex(' .o. '.join(phon2orth_rules))
    phone_str_fst.compose(noisy_phones)
    orthstrs = phone_str_fst

    #####################################
    ##     ALIGNMENT CONSTRAINTS       ##
    ##################################### 
    # define Edit0Align [[?]* LexemePattern [?]*]; 
    # define Edit1Align [[?]* [ Edit1 .o. LexemePattern] [?]*][0:"^"];
    # define Edit2Align [[?]* [ Edit2 .o. LexemePattern] [?]*][0:"^"][0:"^"];
    # define AlignedOrth [OrthStrs .o. [ Edit0Align | Edit1Align | Edit2Align ]];
    edit0_align = hfst.regex('[?]*')
    edit0_align.concatenate(lexeme_pattern)
    edit0_align.concatenate(hfst.regex('[?]*'))

    edit1_align = hfst.regex('[?]*')
    edit1.compose(lexeme_pattern)
    edit1_align.concatenate(edit1)
    edit1_align.concatenate(hfst.regex('[?]*'))
    edit1_align.concatenate(hfst.regex('["^"]*'))
    edit1_align.concatenate(hfst.regex('[0:"^"]'))

    edit2_align = hfst.regex('[?]*')
    edit2.compose(lexeme_pattern)
    edit2_align.concatenate(edit2)
    edit2_align.concatenate(hfst.regex('[?]*'))
    edit2_align.concatenate(hfst.regex('["^"]*'))
    edit2_align.concatenate(hfst.regex('[0:"^"][0:"^"]'))

    aligned_edits = edit0_align
    aligned_edits.disjunct(edit1_align)
    aligned_edits.disjunct(edit2_align)
    aligned_orth = orthstrs
    aligned_orth.compose(aligned_edits)
    
    ###################################
    # WORD DISCOVERY CONSTRAINTS     ##
    ###################################
    # define Edit0Discover [[?:0]* LEXICON [?:0]*];
    # define Edit1Discover [[?:0]* [Edit1 .o. LEXICON] [?:0]*][0:"^"];
    # define Edit2Discover [[?:0]* [Edit2 .o. LEXICON] [?:0]*][0:"^"][0:"^"];
    # define DiscoverWords [AlignedOrth .o. [ Edit0Discover | Edit1Discover | Edit2Discover]];
    
    edit0discover = hfst.regex('[?:0]*')
    edit0discover.concatenate(analyzer_fst)
    edit0discover.concatenate(hfst.regex('[?:0]*'))
    edit0discover.concatenate(hfst.regex('["^"]*'))

    edit1discover = hfst.regex('[?:0]*')
    edit1.compose(analyzer_fst)
    edit1discover.concatenate(edit1)
    edit1discover.concatenate(hfst.regex('[?:0]*'))
    edit1discover.concatenate(hfst.regex('["^"]*'))
    edit1discover.concatenate(hfst.regex('[0:"^"]'))

    edit2discover = hfst.regex('[?:0]*')
    edit2.compose(analyzer_fst)
    edit2discover.concatenate(edit2)
    edit2discover.concatenate(hfst.regex('[?:0]*'))
    edit2discover.concatenate(hfst.regex('["^"]*'))
    edit2discover.concatenate(hfst.regex('[0:"^"][0:"^"]'))
 
    edit0discover.disjunct(edit1discover)
    edit0discover.disjunct(edit2discover)
    
    aligned_orth.compose(edit0discover)
    discover_words = aligned_orth
    
    ################################################
    # FILTER down to results anchored at a lexeme ##
    ################################################
    # define AnchoredWords DiscoverWords .o. [?* LEXEMESB ?*];
    discover_words.compose(hfst.regex('[?* [' + ' | '.join(list(set(tokd_lexemes.split('  ')))) + '] ?*]'))
    print("DISCOVER_WORDS: " + '[?* [' + ' | '.join(list(set(tokd_lexemes.split('  ')))) + '] ?*]')
    # discover_words.output_project()
    discover_words.minimize()
    discover_words.determinize()

    results = discover_words.extract_paths(max_cycles=1, output='dict')
    for inp, outlist in results.items():
        print(re.sub('@_EPSILON_SYMBOL_@', '', inp))
        for out in outlist:
            print('\t' + re.sub('@_EPSILON_SYMBOL_@', '', str(out)))

    #################################################################################
    ## PRIORITY UNION to get the results with the lowest edit distance penalties   ##
    #################################################################################
    # define filtered [[AnchoredWords .o. FilterA0D0] .P. [AnchoredWords .o. FilterA1D0] .P. 
    #                 [AnchoredWords .o. FilterA0D1] .P. 
    #                 [AnchoredWords .o. FilterA1D1] .P. 
    #                 [AnchoredWords .o. FilterA1D2] .P. 
    #                 [AnchoredWords .o. FilterA2D1] ];

    ## TODO: implement the filter
  
    
def tokenize_lexemes(lexemes):
    matches = re.findall('|'.join(multi_char_graphemes) + "|.", " ".join(lexemes))
    return ' '.join(matches)


if __name__== "__main__":

    # phone_str = "kɔŋadkarijmɛjɛkaribekanikabiribimbomŋarakarbɔɟakŋaraŋulumɛŋ"
    phone_str = "ŋawokdibriwambunngan"
    lexemes = ['wok', "wam"]
    main(phone_str, lexemes)