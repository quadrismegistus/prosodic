#!/bin/bash

# This is probably subject to change--fill it in with info from
# http://nlp.stanford.edu/software/lex-parser.shtml
DATE=2015-04-20
VERSION=3.5.2

wget "http://nlp.stanford.edu/software/stanford-parser-full-$DATE.zip"
unzip "stanford-parser-full-$DATE.zip"
mkdir "StanfordLibrary"
mv stanford-parser-full-$DATE "StanfordLibrary/"
cd "StanfordLibrary/stanford-parser-full-$DATE"
jar xf stanford-parser-$VERSION-models.jar
cd ../..
rm "stanford-parser-full-$DATE.zip"
echo ">> successfully installed Stanford NLP Parser ($DATE)'"
