# Metrics

This repo contains code I've been working on with Arto Anttila for prosodic analysis of texts. The documentation is currently nonexistant, but cleaning it up to make it more publically accessible is on my to do list. Until that happens, here's a high-level description of what the files in this repo do:
* Pickle Jar: contains pickle versions of entries in the CMU pronunciation dictionary, used for gathering lexical information about words. Currently there's no way to get information about words not in the dictionary, but eventually I plan to include some machine learning models to make guesses about unknown words.
* Text Book: contains documents used for developing the model.
* deptree.py: a clone of the nltk module for building trees, but includes functionality for parsing with the Stanford Parser's RNN model and adding dependency annotations to the leaf nodes.
* metricaltree.py: takes in a syntactic tree with dependency annotations and gives it a metrical parse.
* get-deps.sh: automatically grabs some of the files that this program depends on from the internet (e.g. the Stanford Parser).
