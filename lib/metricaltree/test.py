from metricaltree import *

parser = DependencyTreeParser(model_path='Stanford Library/stanford-parser-full-%s/edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz' % DATE)
parser = MetricalTreeParser(parser)

sents = ['hello beautiful world!', 'how are you?']

t = list(parser.lex_raw_parse_sents(sents))[0]
