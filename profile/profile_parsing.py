import os
import time
import prosodic
timenow=time.time()
t = prosodic.Text(fn='../corpora/corppoetry_en/en.shakespeare.txt')
print(f"Time taken to load text: {time.time()-timenow:.2f}s")


timenow=time.time()


import cProfile
pr = cProfile.Profile()
timenow=time.time()
pr.enable()


pll = t.parse(num_proc=5, lim=None, parse_unit='line')
print(f"Time taken to parse: {time.time()-timenow:.2f}s")



pr.disable()
print(f"Time taken: {time.time()-timenow:.2f}s")
pr.dump_stats('profile_output.prof')

os.system("snakeviz profile_output.prof")