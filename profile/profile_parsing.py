import os
import time
import prosodic
timenow=time.time()
t = prosodic.Text(fn='../corpora/corppoetry_en/en.shakespeare.txt')
print(f"Time taken to load text: {time.time()-timenow:.2f}s")


timenow=time.time()
pll = t.parse(num_proc=1, lim=1000, combine_by=None)
print(f"Time taken to parse: {time.time()-timenow:.2f}s")


import cProfile
pr = cProfile.Profile()
timenow=time.time()
pr.enable()
data = pll.to_dict()
prosodic.Entity.from_dict(data)
pr.disable()
print(f"Time taken: {time.time()-timenow:.2f}s")
pr.dump_stats('profile_output.prof')

os.system("snakeviz profile_output.prof")