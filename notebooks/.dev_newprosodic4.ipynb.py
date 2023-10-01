#!/usr/bin/env python
# coding: utf-8

# In[4]:


# !rm -rf /Users/ryan/prosodic_data/data/english_wordforms.sqlitedict
# !pip install -qU pip wheel
# !pip install -qU -r ../requirements.txt
import sys; sys.path.insert(0,'..')
from prosodic.imports import *


# In[13]:


# !pip install line_profiler
# %load_ext line_profiler


# In[14]:


poemstr="""
Those hours, that with gentle work did frame
The lovely gaze where every eye doth dwell,
Will play the tyrants to the very same
And that unfair which fairly doth excel;
For never-resting time leads summer on
To hideous winter, and confounds him there;
Sap checked with frost, and lusty leaves quite gone,
Beauty o’er-snowed and bareness every where:
Then were not summer’s distillation left,
A liquid prisoner pent in walls of glass,
Beauty’s effect with beauty were bereft,
Nor it, nor no remembrance what it was:
But flowers distill’d, though they with winter meet,
Leese but their show; their substance still lives sweet.
"""
poem = Text(poemstr)


# In[15]:


# %lprun -f poem.parse()


# In[5]:


poem.parse(max_s=None, max_w=None)


# In[ ]:




