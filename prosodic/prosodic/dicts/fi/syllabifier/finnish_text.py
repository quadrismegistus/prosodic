# coding=utf-8
from finnish_annotator import mark

import string
import sys

def remove_punct(word):

    start = 0

    while start < len(word) and word[start] in string.punctuation:

        start += 1

    end = len(word)-1

    while end >= 0 and word[end] in string.punctuation:

        end -= 1

    return word[start:end+1]

if len(sys.argv) != 2:

    print "Please enter a single argument for the file to annotate"

else:

    filename = sys.argv[1]

    try:

        f = open(filename, 'r')
        entries = f.readlines()
        f.close()

        for i in range(len(entries)-1):
            entries[i] = entries[i][:-1]

        for entry in entries:

            words = entry.split(' ')

            for word in words:

                mark(remove_punct(word))

    except IOError:

        print "File (" + filename + ") could not be opened"
