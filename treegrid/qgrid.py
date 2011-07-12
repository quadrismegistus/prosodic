import sys,pyparse

try:
	fn=sys.argv[1]
except:
	exit("[usage]: qgrid.py [xml_filename_of_stanford_corenlp_parser_output]")

#ld=pyparse.parse2grid(fn,ldlim=10)
pyparse.parse2tree(fn)