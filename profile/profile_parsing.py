import os
import cProfile
import pstats
import io
from pstats import SortKey

# Import your main application code here
import prosodic

# Run the profiler
t = prosodic.Text(fn='../corpora/corppoetry_en/en.shakespeare.txt')

# Run the profiler
pr = cProfile.Profile()
pr.enable()

# Run your main application code
# t.stanza1.line1
t.parse(num_proc=1, lim=10, combine_by=None)

pr.disable()

# Save the results to a file
s = io.StringIO()
sortby = SortKey.CUMULATIVE
ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
ps.print_stats()

with open('profile_output.txt', 'w') as f:
    f.write(s.getvalue())

# Save results in a format that can be read by snakeviz
pr.dump_stats('profile_output.prof')

os.system("snakeviz profile_output.prof")