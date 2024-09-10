import os
import time
import prosodic
timenow=time.time()
t = prosodic.Text(fn='../corpora/corppoetry_en/en.shakespeare.txt')
print(f"Time taken to load text: {time.time()-timenow:.2f}s")


timenow=time.time()
pll = t.parse(num_proc=1, lim=100, combine_by=None)
print(f"Time taken to parse: {time.time()-timenow:.2f}s")
data = pll.to_dict()


import cProfile
pr = cProfile.Profile()
pr.enable()
prosodic.Entity.from_dict(data)
pr.disable()
pr.dump_stats('profile_output.prof')

os.system("snakeviz profile_output.prof")