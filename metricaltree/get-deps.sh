#!/bin/bash

# This is probably subject to change--fill it in with info from
# http://nlp.stanford.edu/software/lex-parser.shtml
DATE=2015-04-20
VERSION=3.5.2

wget "http://nlp.stanford.edu/software/stanford-parser-full-$DATE.zip"
unzip "stanford-parser-full-$DATE.zip"
mkdir "Stanford Library"
mv stanford-parser-full-$DATE "Stanford Library/"
cd "Stanford Library/stanford-parser-full-$DATE"
jar xf stanford-parser-$VERSION-models.jar

su
add-apt-repository ppa:webupd8team/java
apt-get update
apt-get install oracle-java8-installer
exit

su # May need to be su for this, may not
pip install numpy
pip install nltk
pip install matplotlib
pip install pandas
exit

python -c "import nltk; nltk.download('punkt')"