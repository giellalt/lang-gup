# Kunwok-FST

The canonical repo for the Kunwinjku FST morphological analyzer. 

To update the autocomplete model:
1. Make a change to `kunwok.lexc`
2. `make generate-weighted-lexc` to generate the weighted version of the lexc file that was changed
3. `make autocomplete` to compile the new hfst model

The other FST models (analysis, spelling, etc) do not yet have make targets because they have not been converted to hfst models in the dictionary interface. 
Continue building Foma models for those FSTs. 