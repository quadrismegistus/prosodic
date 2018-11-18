#!/usr/bin/env python

program_name = "lexconvert v0.1453 - convert between lexicons of different speech synthesizers\n(c) 2007-2012 Silas S. Brown.  License: GPL"
# with contributions from Jan Weiss (x-sampa, acapela-uk, cmu)

# Run without arguments for usage information

#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

# Phoneme Conversion Table:
# Column 'festival': phoneme in Festival's British English notation
# Column 'espeak': approximation in eSpeak, but note that eSpeak's phoneme representation is not that simple (hence some of the code below)
# Column 'sapi': approximation in American English in MS SAPI notation
# Column 'cepstral': phoneme in Cepstral's British English SSML phoneset
# Column 'mac': approximation in American English in Apple's speech notation ([[inpt PHON]]...[[inpt TEXT]] with no spaces between the phonemes)
# Column 'x-sampa': X-SAMPA
# Column 'acapela-uk': acapela optimized X-SAMPA for UK English voices (e.g. "Peter")
# Column 'cmu': format of the US English "Carnegie Mellon University Pronouncing Dictionary" (http://www.speech.cs.cmu.edu/cgi-bin/cmudict)
# Column 'bbcmicro': BBC Micro Speech program by David J. Hoskins / Superior
# Column 'unicode-ipa': Unicode IPA, as used on an increasing number of websites
# Column 'pinyin-approx' (convert TO only): Rough approximation using roughly the spelling rules of Chinese Pinyin (for getting Chinese-only voices to speak some English words - works with some words better than others)
table = [
   ('festival', 'espeak', 'sapi', 'cepstral', 'mac', 'x-sampa', 'acapela-uk', 'cmu', 'bbcmicro', 'unicode-ipa','pinyin-approx'),
   # The first entry MUST be the syllable separator:
   ('0', '%', '-', '0', '=', '.', '', '0', '', '.',''),
   ('1', "'", '1', '1', '1', '"', 0, '1', '1', u'\u02c8','4'), # primary stress - ignoring this for acapela-uk
   ('2', ',', '2', '0', '2', '%', 0, '2', '2', u'\u02cc','2'), # secondary stress - ignoring this for acapela-uk
   ('', '', '', '', '', '', 0, '', '', '-',''),
   (0, 0, 0, 0, 0, 0, 0, 0, '', '#',0),
   (0, 0, 0, 0, 0, 0, 0, 0, '', ' ',0),
   (0, 0, 0, 0, 0, 0, 0, 0, '', '_',0),
   (0, 0, 0, 0, 0, 0, 0, 0, '', '?',0),
   (0, 0, 0, 0, 0, 0, 0, 0, '', '!',0),
   (0, 0, 0, 0, 0, 0, 0, 0, '', ',',0),
   ('aa', ['A:', 'A@', 'aa'], 'aa', 'a', 'AA', 'A', 'A:', 'AA', 'AA', u'\u0251','a5'),
   (0, 'A', 0, 0, 0, 0, 0, '2', 0, u'\u2051',0),
   (0, 'A:', 0, 0, 0, ':', 0, '1', 0, u'\u02d0',0),
   (0, 0, 0, 0, 0, 'A:', 0, 'AA', 0, u'\u0251\u02d0',0),
   (0, 0, 0, 0, 0, 'Ar\\', 0, 0, 0, u'\u0251\u0279',0),
   (0, 0, 0, 0, 'aa', 'a:', 0, 0, 0, 'a\\u02d0',0),
   ('a', ['a', '&'], 'ae', 'ae', 'AE', '{', '{', 'AE', 'AE', [u'\xe6','a'],'ya5'),
   ('uh', 'V', 'ah', 'ah', 'UX', 'V', 'V', 'AH', 'OH', u'\u028c','e5'),
   ('o', '0', 'ao', 'oa', 'AA', 'Q', 'Q', 'AA', 'O', u'\u0252','yo5'),
   (0, 0, 0, 0, 0, 'A', 'A', 0, 0, u'\u0251',0),
   (0, 0, 0, 0, 0, 'O', 'O', 0, 0, u'\u0254',0),
   ('au', 'aU', 'aw', 'aw', 'AW', 'aU', 'aU', 'AW', 'AW', u'a\u028a','ao5'),
   (0, 0, 0, 0, 0, '{O', '{O', 0, 0, u'\xe6\u0254',0),
   ('@', '@', 'ax', 'ah', 'AX', '@', '@', 'AH', 'AH', u'\u0259','e5'),
   ('@@', '3:', 'er', 'er', 0, '3:', '3:', 'ER', 'ER', u'\u0259\u02d0','e5'),
   ('@', '3', 'ax', 'ah', 0, '@', '@', 'AH', 'AH', u'\u025a','e5'),
   ('@1', 'a2', 0, 0, 0, 0, 0, 0, 0, u'\u0259', 0),
   ('@2', '@', 0, 0, 0, 0, 0, 0, 0, 0, 0),
   ('ai', 'aI', 'ay', 'ay', 'AY', 'aI', 'aI', 'AY', 'IY', u'a\u026a','ai5'),
   (0, 0, 0, 0, 0, 'Ae', 'A e', 0, 0, u'\u0251e',0),
   ('b', 'b', 'b', 'b', 'b', 'b', 'b', 'B ', 'B', 'b','bu0'),
   ('ch', 'tS', 'ch', 'ch', 'C', 'tS', 't S', 'CH', 'CH', [u't\u0283', u'\u02a7'],'che0'),
   ('d', 'd', 'd', 'd', 'd', 'd', 'd', 'D ', 'D', 'd','de0'),
   ('dh', 'D', 'dh', 'dh', 'D', 'D', 'D', 'DH', 'DH', u'\xf0','ze0'),
   ('e', 'E', 'eh', 'eh', 'EH', 'E', 'e', 'EH', 'EH', u'\u025b','ye5'),
   (0, 0, 'ey', 0, 0, 'e', 0, 0, 0, 'e',0),
   ('@@', '3:', 'er', 'er', 'AX', '3:', '3:', 'ER', 'ER', [u'\u025d', u'\u025c\u02d0'],'e5'),
   ('e@', 'e@', 'eh r', 'e@', 'EH r', 'E@', 'e @', 0, 'AI', u'\u025b\u0259','ye5'),
   (0, 0, 0, 0, 0, 'Er\\', 'e r', 0, 0, u'\u025b\u0279',0),
   (0, 0, 0, 0, 0, 'e:', 'e :', 0, 0, u'e\u02d0',0),
   (0, 0, 0, 0, 0, 'E:', 0, 0, 0, u'\u025b\u02d0',0),
   (0, 0, 0, 0, 0, 'e@', 'e @', 0, 0, u'e\u0259',0),
   ('ei', 'eI', 'ey', 'ey', 'EY', 'eI', 'eI', 'EY', 'AY', u'e\u026a','ei5'),
   (0, 0, 0, 0, 0, '{I', '{I', 0, 0, u'\xe6\u026a',0),
   ('f', 'f', 'f', 'f', 'f', 'f', 'f', 'F ', 'F', 'f','fu0'),
   ('g', 'g', 'g', 'g', 'g', 'g', 'g', 'G ', 'G', [u'\u0261', 'g'],'ge0'),
   ('h', 'h', 'h', 'h', 'h', 'h', 'h', 'HH', '/H', 'h','he0'), # Jan suggested "hh" for SAPI, but it doesn't work on XP
   ('i', 'I', 'ih', 'ih', 'IH', 'I', 'I', 'IH', 'IH', u'\u026a','yi5'),
   (0, 0, 0, 0, 0, '1', '1', 0, 0, u'\u0268',0),
   (0, ['I', 'I2'], 0, 0, 'IX', 'I', 'I', 0, 'IX', u'\u026a',0),
   ('i@', 'i@', 'iy ah', 'i ah', 'IY UX', 'I@', 'I@', 'EY AH', 'IXAH', u'\u026a\u0259','yi3re5'),
   (0, 0, 0, 0, 0, 'Ir\\', 'I r', 0, 0, u'\u026a\u0279',0),
   ('ii', ['i:','i'], 'iy', 'i', 'IY', 'i', 'i', 'IY', 'EE', 'i','yi5'),
   (0, 0, 0, 0, 0, 'i:', 'i:', 0, 0, u'i\u02d0',0),
   ('jh', 'dZ', 'jh', 'jh', 'J', 'dZ', 'dZ', 'JH', 'J', [u'd\u0292', u'\u02a4'],'zhe0'),
   ('k', 'k', 'k', 'k', 'k', 'k', 'k', 'K ', 'K', 'k','ke0'),
   (0, 'x', 0, 0, 0, 'x', 'x', 0, 0, 'x',0), # actually 'x' is like Scottish 'loch', but if the synth can't do that then try k 
   ('l', ['l', 'L'], 'l', 'l', 'l', 'l', 'l', 'L ', 'L', ['l', u'd\u026b'],'le0'),
   ('m', 'm', 'm', 'm', 'm', 'm', 'm', 'M ', 'M', 'm','me0'),
   ('n', 'n', 'n', 'n', 'n', 'n', 'n', 'N ', 'N', 'n','ne0'),
   ('ng', 'N', 'ng', 'ng', 'N', 'N', 'N', 'NG', 'NX', u'\u014b','eng0'),
   ('ou', 'oU', 'ow', 'ow', 'OW', '@U', '@U', 'OW', 'OW', [u'\u0259\u028a', 'o'],'ou5'),
   (0, 0, 0, 0, 0, 'oU', 'o U', 0, 0, u'o\u028a',0),
   (0, 0, 0, 0, 0, '@}', '@ }', 0, 0, u'\u0259\u0289',0),
   ('oi', 'OI', 'oy', 'oy', 'OY', 'OI', 'OI', 'OY', 'OY', u'\u0254\u026a','ruo2yi5'),
   (0, 0, 0, 0, 0, 'oI', 'o I', 0, 0, u'o\u026a',0),
   ('p', 'p', 'p', 'p', 'p', 'p', 'p', 'P ', 'P', 'p','pu0'),
   ('r', 'r', 'r', 'r', 'r', 'r\\', 'r', 'R ', 'R', u'\u0279','re0'),
   (0, 0, 0, 0, 0, 'r', 0, 0, 0, 'r',0),
   ('s', 's', 's', 's', 's', 's', 's', 'S ', 'S', 's','se0'),
   ('sh', 'S', 'sh', 'sh', 'S', 'S', 'S', 'SH', 'SH', u'\u0283','she0'),
   ('t', 't', 't', 't', 't', 't', 't', 'T ', 'T', ['t', u'\u027e'],'te0'),
   ('th', 'T', 'th', 'th', 'T', 'T', 'T', 'TH', 'TH', u'\u03b8','zhe0'),
   ('u@', 'U@', 'uh', 'uh', 'UH', 'U@', 'U@', 'UH', 'UH', u'\u028a\u0259','wu5'),
   (0, 0, 0, 0, 0, 'Ur\\', 'U r', 0, 0, u'\u028a\u0279',0),
   ('u', 'U', 0, 0, 0, 'U', 'U', 0, '/U', u'\u028a',0),
   ('uu', 'u:', 'uw', 'uw', 'UW', '}:', 'u:', 'UW', ['UW','UX'], u'\u0289\u02d0','yu5'),
   (0, 0, 0, 0, 0, 'u:', 0, 0, 0, [u'u\u02d0', 'u'],0),
   ('oo', 'O:', 'AO', 'ao', 'AO', 'O:', 'O:', 'AO', 'AO', u'\u0254\u02d0','huo5'),
   (0, 0, 0, 0, 0, 'O', 'O', 0, 0, u'\u0254',0),
   (0, 0, 0, 0, 0, 'o:', 'O:', 0, 0, u'o\u02d0',0),
   (0, ['O@', 'o@', 'O'], 0, 0, 0, 'O:', 0, 0, 0, u'\u0254\u02d0',0),
   ('v', 'v', 'v', 'v', 'v', 'v', 'v', 'V ', 'V', 'v','fu0'),
   ('w', 'w', 'w', 'w', 'w', 'w', 'w', 'W ', 'W', 'w','wu0'),
   (0, 0, 0, 0, 0, 'W', 0, 0, 0, u'\u028d',0), # Jan suggested "x" for SAPI here, but that doesn't work on XP
   ('y', 'j', 'y', 'j', 'y', 'j', 'j', 'Y ', 'Y', 'j','yu0'),
   ('z', 'z', 'z', 'z', 'z', 'z', 'z', 'Z ', 'Z', 'z','ze0'),
   ('zh', 'Z', 'zh', 'zh', 'Z', 'Z', 'Z', 'ZH', 'ZH', u'\u0292','zhe0'),
   # TODO \u0294 (glottal stop) to eSpeak? (for local dialects)
   # TODO bbcmicro also has CT as in fact, DR as in dragon, DUX as in duke, TR as in track
   # Hack (must be at end) - make sure all dictionaries have an entry for '@', for the @l rule:
   ('@', '@', '@', 'ah', 'AX', '@', '@', '@', 'AH', u'\u0259','wu5'),
   (0, 0, 'ax', '@', 0, 0, 0, 0, 0, 0,0),
   (0, 0, 0, 'ah', '@', 0, 0, 0, 0, 0,0),
   (0, 0, 0, 0, 'AX', 0, 0, 0, '@', '@',0),
]

formats_where_space_separates_words = ["espeak","mac","unicode-ipa","x-sampa","bbcmicro","pinyin-approx"]

espeak_consonants = "bdDfghklmnNprsStTvwjzZ"

import commands,sys,re,os

for row in table: assert len(row)==len(table[0]),"problem with "+repr(row) # sanity-check the table

def compare_tables(table1,table2,colsToIgnore):
  # Debug function to compare 2 versions of the table
  def checkDuplicateRows(t,which):
    d = {}
    for i in t:
      if d.has_key(i): print "Warning: duplicate row in "+which+":",i
      d[i]=1
  checkDuplicateRows(table1,"first table") ; checkDuplicateRows(table2,"second table")
  for col in table1[0]:
    if col not in table2[0]: print "Deleted column:",col
  for col in table2[0]:
    if col not in table1[0]: print "Added column:",col
  maps = [{}, {}]
  commonCols = filter(lambda x:x in table2[0],table1[0])
  for dx in [0,1]:
    table = [table1,table2][dx]
    for col1 in commonCols:
      if col1 in colsToIgnore: continue
      i1 = list(table[0]).index(col1)
      for col2 in filter(lambda x: x>col1, commonCols):
        if col2 in colsToIgnore: continue
        i2 = list(table[0]).index(col2)
        for row in table[1:]:
          if not row[i1] or not row[i2]: continue # don't bother reporting mappings involving null strings - they don't matter
          maps[dx][(col1,row[i1],col2,row[i2])] = True
  deleted_mappings = filter(lambda k:not maps[1].has_key(k), maps[0].keys())
  added_mappings = filter(lambda k:not maps[0].has_key(k), maps[1].keys())
  def simplify_mappings(mappings,which):
    byRow = {} ; byCol = {}
    for k1,v1,k2,v2 in mappings:
      if not byRow.has_key((k1,v1)): byRow[(k1,v1)]=[]
      byRow[(k1,v1)].append((k2,v2))
      if not byCol.has_key((k2,v2)): byCol[(k2,v2)]=[]
      byCol[(k2,v2)].append((k1,v1))
    byColCopy = byCol.copy()
    for r in byRow.keys():
      rowLen = len(r)
      maxColLen = max(map(lambda c:len(byCol[c]),byRow[r]))
      if rowLen > maxColLen:
        if len(byRow[r])>1: word="mappings:"
        else: word="mapping"
        print which,word,r,"to",byRow[r]
        for k in byColCopy.keys():
          if r in byColCopy[k]: byColCopy[k].remove(r)
    for c in filter(lambda x:byColCopy[x],byColCopy.keys()):
      if len(byColCopy[c])>1: word="mappings:"
      else: word="mapping"
      print which,word,c,"to",byColCopy[c]
  simplify_mappings(deleted_mappings,"Deleted")
  simplify_mappings(added_mappings,"Added")

# e.g. if someone sends in newlexconvert.py and you want to review all changes not involving sampa/acapela:
# import lexconvert,newlexconvert
# lexconvert.compare_tables(lexconvert.table,newlexconvert.table,['x-sampa', 'acapela-uk'])

def squash_table(colsToDelete):
  # For maintenance use.  Deletes colsToDelete, and introduces dittos/list-alternatives
  colsToDelete=map(lambda c:list(table[0]).index(c),colsToDelete)
  colsToDelete.sort() ; colsToDelete.reverse()
  ret = [] ; lastRow = None
  for row in table:
    row=list(row)
    for c in colsToDelete: del row[c]
    if ret:
      for i in range(len(row)):
        k=-1
        while ret[k][i]==0: k -= 1
        if row[i]==ret[k][i]: row[i]=0
      if len(filter(lambda x:not x==0,row))==1:
        # only 1 thing changed
        ret[-1]=list(ret[-1])
        for i in range(len(row)):
          if not row[i]==0:
            if not type(ret[-1][i])==type([]): ret[-1][i]=[ret[-1][i]]
            ret[-1][i].append(row[i])
        ret[-1]=tuple(ret[-1])
        continue
    ret.append(tuple(row))
  # return ret
  print "table = ["
  for r in ret: print "   "+repr(r)+","
  print "]"

# Deal with any rows that contain lists of alternatives
# or 0 (ditto) marks
# If multiple lists in a row e.g. ([ab],[cd]), give [(a,c), (b,c), (a,d)], as (b,d) would never be reached anyway.
# (Removing duplicates and redundant rows is not really necessary but may help debugging)
newTable=[] ; hadAlready = {}
prevLine = None
for line in table:
  line=list(line)
  for i in range(len(line)):
    if line[i]==0: line[i]=prevLine[i]
  line=tuple(line)
  colsWithLists = filter(lambda col: type(line[col])==type([]), range(len(line)))
  if not colsWithLists: newTable.append(line)
  for col in colsWithLists:
    def firstItemIfList(l):
      if type(l)==type([]): return l[0]
      else: return l
    for extraTuple in [tuple(map(lambda x:firstItemIfList(x),list(line[:col])+[i]+list(line[col+1:]))) for i in line[col]]:
      if hadAlready.has_key(extraTuple): continue
      hadAlready[extraTuple]=1
      newTable.append(extraTuple)
  prevLine = line
table = newTable

cached_source,cached_dest,cached_dict = None,None,None
def make_dictionary(source,dest):
    global cached_source,cached_dest,cached_dict
    if (source,dest) == (cached_source,cached_dest): return cached_dict
    types = list(table[0])
    assert source in types,"Unknown synthesizer name to convert from"
    assert dest in types, "Unknown synthesizer name to convert to"
    source,dest = types.index(source), types.index(dest)
    d = {}
    global dest_consonants ; dest_consonants = []
    global dest_syllable_sep ; dest_syllable_sep = table[1][dest]
    for l in table[1:]:
        if not l[source] in d: d[l[source]]=l[dest]
        is_in_espeak_consonants=True
        for cTest in l[1]:
            if cTest not in espeak_consonants:
                is_in_espeak_consonants=False; break
        if is_in_espeak_consonants: dest_consonants.append(l[dest])
    cached_source,cached_dest,cached_dict=source,dest,d
    return d

def convert(pronunc,source,dest):
    if source=="unicode-ipa":
        # try to decode it
        if "\\u" in pronunc and not '"' in pronunc: # maybe \uNNNN copied from Gecko on X11, can just evaluate it to get the unicode
            # (NB make sure to quote the \'s if pasing in on the command line)
            try: pronunc=eval('u"'+pronunc+'"')
            except: pass
        else: # see if it makes sense as utf-8
            try: pronunc = pronunc.decode('utf-8')
            except: pass
    ret = [] ; toAddAfter = None
    dictionary = make_dictionary(source,dest)
    while pronunc:
        for lettersToTry in [2,1,0]:
            if not lettersToTry and source=="espeak" and not pronunc[0] in "_: ":
              #sys.stderr.write("Warning: ignoring unknown espeak phoneme "+repr(pronunc[0])+"\n")
              pass
            if not lettersToTry: pronunc=pronunc[1:] # ignore
            elif dictionary.has_key(pronunc[:lettersToTry]):
                toAdd=dictionary[pronunc[:lettersToTry]]
                if toAdd in ['0','1','2','4'] and not dest=="espeak": # it's a stress mark in a notation that places stress marks AFTER vowels (not dest=="espeak" added because espeak uses 0 for other purposes)
                    if dest=="bbcmicro": # not sure which pitch levels to map the stresses to; try these:
                      if toAdd=='1': toAdd='3'
                      elif toAdd=='2': toAdd='4'
                    if source in ["espeak","unicode-ipa"]: # stress should be moved from before the vowel to after it
                        toAdd, toAddAfter = "",toAdd
                    else:
                        # With Cepstral synth, stress mark should be placed EXACTLY after the vowel and not any later.  Might as well do this for others also.
                        # (not dest=="espeak" because that uses 0 as a phoneme; anyway it's dealt with separately below)
                        r=len(ret)-1
                        while ret[r] in dest_consonants or ret[r].endswith("*added"): r -= 1 # (if that raises IndexError then the input had a stress mark before any vowel) ("*added" condition is there so that implicit vowels don't get the stress)
                        ret.insert(r+1,toAdd) ; toAdd=""
                elif toAdd in u"',\u02c8\u02cc" and dest in ["espeak","unicode-ipa"] and not source in ["espeak","unicode-ipa"]: # it's a stress mark that should be moved from after the vowel to before it
                    i=len(ret)
                    while i and (ret[i-1] in dest_consonants or ret[i-1].endswith("*added")): i -= 1
                    if i: i-=1
                    ret.insert(i,toAdd)
                    toAdd = ""
                # attempt to sort out the festival dictionary's (and other's) implicit @ :
                if ret and ret[-1] and toAdd in ['n','l'] and ret[-1] in dest_consonants: ret.append(dictionary['@']+'*added')
                elif len(ret)>2 and ret[-2].endswith('*added') and toAdd and not toAdd in dest_consonants and not toAdd==dest_syllable_sep: del ret[-2]
                # OK, add it:
                if toAdd:
                    toAdd=toAdd.split()
                    ret.append(toAdd[0])
                    if toAddAfter and not toAdd[0] in dest_consonants:
                        ret.append(toAddAfter)
                        toAddAfter=None
                    ret += toAdd[1:]
                    # TODO: the above few lines make sure that toAddAfter goes after the FIRST phoneme if toAdd is multiple phonemes, but works only when converting from eSpeak to non-eSpeak; it ought to work when converting from non-eSpeak to non-eSpeak also (doesn't matter when converting TO eSpeak)
                if source=="espeak" and pronunc[:lettersToTry]=="e@" and len(pronunc)>lettersToTry and pronunc[lettersToTry]=="r" and (len(pronunc)==lettersToTry+1 or pronunc[lettersToTry+1] in espeak_consonants): lettersToTry += 1 # hack because the 'r' is implicit in other synths (but DO have it if there's another vowel to follow)
                pronunc=pronunc[lettersToTry:]
                break
    if toAddAfter: ret.append(toAddAfter)
    if len(ret) and ret[-1]==dest_syllable_sep: del ret[-1] # spurious syllable separator at end
    if dest in formats_where_space_separates_words: separator = ''
    else: separator = ' '
    ret=separator.join(ret).replace('*added','')
    if dest=="cepstral": return ret.replace(" 1","1").replace(" 0","0")
    if dest=="pinyin-approx":
        for s,r in [
        ("te0ye","tie"),
        ("e0e5","e5"),("([^aeiou][uo])0e(5)",r"\1\2"),
        ("yu0y","y"),
        ("wu0yo5","wo5"),
        ("([bdfghklmnpwz])[euo]0ei",r"\1ei"),
        ("([bdghklmnpstwz])[euo]0ai",r"\1ai"),
        ("([ghklmnpstyz])[euo]0ya",r"\1a"),("([ghklmnpstz])a([0-5]*)ne0",r"\1an\2"),
        ("([bdfghklmnpstwyz])[euo]0a([1-5])",r"\1a\2"),
        ("([bdjlmnpt])[euo]0yi",r"\1i"),("([bjlmnp])i([1-5]*)ne0",r"\1in\2"),
        ("([zs])he0ei",r"\1hei"),
        ("([dfghklmnprstyz])[euo]0ou",r"\1ou"),
        ("([dghklnrst])[euo]0huo",r"\1uo"),
        ("([bfpm])[euo]0huo",r"\1o"),
        ("([bdghklmnprstyz])[euo]0ao",r"\1ao"),
        ("([zcs])h[eu]0ao",r"\1hao"),
        ("re0r","r"),
        ("zhe0ne0","zhun5"),
        ("54","4"),
        ("52","2"),
        ("([bdjlmnpty])i([1-9])eng0",r"\1ing\2"),
        ("ya([1-9])eng0",r"yang\1"),
        ("ya([1-9])ne0",r"an\1"),
        ("ye([1-9])ne0",r"yan\1"),("([wr])[eu]0yan",r"\1en"),
        ("yi([1-9])ne0",r"yin\1"),

        ("yu0","yu5"),("eng0","eng5"), # they won't work unvoiced anyway
        ("0","5"), # comment out if the synth supports 'tone 0 for unvoiced'
        #("[euo]0","0"), # comment in if it expects consonants only when doing that
        
        ]: ret=re.sub(s,r,ret)
    if dest=="espeak": return cleanup_espeak_entry(ret)
    else: return ret

def cleanup_espeak_entry(r):
    r = r.replace("k'a2n","k'@n").replace("ka2n","k@n").replace("gg","g").replace("@U","oU") # (eSpeak uses oU to represent @U; difference is given by its accent parameters)
    if r.endswith("i@r"): return r[:-3]+"i@"
    if r.endswith("U@r"): return r[:-3]+"U@"
    elif r.endswith("@r") and not r.endswith("e@r"): return r[:-2]+"3"
    if r.endswith("A:r"): return r[:-3]+"A@"
    if r.endswith("O:r"): return r[:-3]+"O@"
    # if r.endswith("@l") and not r.endswith("i@l") and not r.endswith("U@l"): return r[:-2]+"@L" # only in older versions of espeak (not valid in more recent versions)
    if r.endswith("rr") or r.endswith("3:r"): return r[:-1]
    # TODO: 'declared' & 'declare' the 'r' after the 'E' sounds a bit 'regional' (but pretty).  but sounds incomplete w/out 'r', and there doesn't seem to be an E2 or E@
    # TODO: consider adding 'g' to words ending in 'N' (if want the 'g' pronounced in '-ng' words) (however, careful of words like 'yankee' where the 'g' would be followed by a 'k'; this may also be a problem going into the next word)
    return r

def espeak_probably_right_already(existing_pronunc,new_pronunc):
    # Compares our "new" pronunciation with eSpeak's existing pronunciation.  As our transcription into eSpeak notation is only approximate, it could be that our new pronunciation is not identical to the existing one but the existing one is actually correct.
    if existing_pronunc==new_pronunc: return True
    def simplify(pronunc): return \
        pronunc.replace(";","").replace("%","") \
        .replace("a2","@") \
        .replace("3","@") \
        .replace("L","l") \
        .replace("I2","i:") \
        .replace("I","i:").replace("i@","i:@") \
        .replace(",","") \
        .replace("s","z") \
        .replace("aa","A:") \
        .replace("A@","A:") \
        .replace("O@","O:") \
        .replace("o@","O:") \
        .replace("r-","r")
    # TODO: rewrite @ to 3 whenever not followed by a vowel?
    if simplify(existing_pronunc)==simplify(new_pronunc): return True # almost the same, and festival @/a2 etc seems to be a bit ambiguous so leave it alone

def parse_festival_dict(festival_location):
    ret = []
    for line in open(festival_location).xreadlines():
        line=line.strip()
        if "((pos" in line: line=line[:line.index("((pos")]
        if line.startswith('( "'): line=line[3:]
        line=line.replace('"','').replace('(','').replace(')','')
        try:
            word, pos, pronunc = line.split(None,2)
        except ValueError: continue # malformed line
        if pos not in ['n','v','a','cc','dt','in','j','k','nil','prp','uh']: continue # two or more words
        yield (word.lower(), pos, pronunc)

def convert_system_festival_dictionary_to_espeak(festival_location,check_existing_pronunciation,add_user_dictionary_also):
    os.system("mv en_extra en_extra~") # start with blank 'extra' dictionary
    if check_existing_pronunciation: os.system("espeak --compile=en") # so that the pronunciation we're checking against is not influenced by a previous version of en_extra
    outFile=open("en_extra","w")
    print "Reading dictionary lists"
    wordDic = {} ; ambiguous = {}
    for line in filter(lambda x:x.split() and not re.match(r'^[a-z]* *\$',x),open("en_list").read().split('\n')): ambiguous[line.split()[0]]=ambiguous[line.split()[0]+'s']=True # this stops the code below from overriding anything already in espeak's en_list.  If taking out then you need to think carefully about words like "a", "the" etc.
    for word,pos,pronunc in parse_festival_dict(festival_location):
        pronunc=pronunc.replace("i@ 0 @ 0","ii ou 2 ").replace("i@ 0 u 0","ii ou ") # (hack for OALD's "radio"/"video"/"stereo"/"embryo" etc)
        pronunc=pronunc.replace("0","") # 0's not necessary, and OALD sometimes puts them in wrong places, confusing the converter
        if wordDic.has_key(word):
            ambiguous[word] = True
            del wordDic[word] # better not go there
        if not ambiguous.has_key(word):
            wordDic[word] = (pronunc, pos)
    toDel = []
    if check_existing_pronunciation:
        print "Checking existing pronunciation"
        proc=os.popen("espeak -q -x -v en-rp > /tmp/.pronunc 2>&1","w")
        wList = []
    progressCount=0 ; oldPercent=-1
    for word,(pronunc,pos) in wordDic.items():
        if check_existing_pronunciation:
            percent = int(progressCount*100/len(wordDic))
            if not percent==oldPercent: sys.stdout.write(str(percent)+"%\r") ; sys.stdout.flush()
            oldPercent=percent
            progressCount += 1
        if not re.match("^[A-Za-z]*$",word): # (some versions of eSpeak also OK with "-", but not all)
            # contains special characters - better not go there
            toDel.append(word)
        elif word.startswith("plaque") or word in "friday saturday sunday tuesday thursday yesterday".split():
            # hack to accept eSpeak's pl'ak instead of pl'A:k - order was reversed in the March 2009 draft
            toDel.append(word)
        elif word[-1]=="s" and wordDic.has_key(word[:-1]):
            # unnecessary plural (espeak will pick up on them anyway)
            toDel.append(word)
        elif word.startswith("year") or "quarter" in word: toDel.append(word) # don't like festival's pronunciation of those (TODO: also 'memorial' why start with [m'I])
        elif check_existing_pronunciation:
            proc.write(word+"\n")
            proc.flush() # so the progress indicator works
            wList.append(word)
    if check_existing_pronunciation:
        proc.close() ; print
        oldPronDic = {}
        for k,v in zip(wList,open("/tmp/.pronunc").read().split("\n")): oldPronDic[k]=v.strip().replace(" ","")
    for w in toDel: del wordDic[w]
    print "Doing the conversion"
    lines_output = 0
    total_lines = 0
    not_output_because_ok = []
    items = wordDic.items() ; items.sort() # necessary because of the hacks below which check for the presence of truncated versions of the word (want to have decided whether or not to output those truncated versions before reaching the hacks)
    for word,(pronunc,pos) in items:
        total_lines += 1
        new_e_pronunc = convert(pronunc,"festival","espeak")
        if new_e_pronunc.count("'")==2 and not '-' in word: new_e_pronunc=new_e_pronunc.replace("'",",",1) # if 2 primary accents then make the first one a secondary (except on hyphenated words)
        # TODO if not en-rp? - if (word.endswith("y") or word.endswith("ie")) and new_e_pronunc.endswith("i:"): new_e_pronunc=new_e_pronunc[:-2]+"I"
        unrelated_word = None
        if check_existing_pronunciation: espeakPronunc = oldPronDic.get(word,"")
        else: espeakPronunc = ""
        if word[-1]=='e' and wordDic.has_key(word[:-1]): unrelated_word, espeakPronunc = word[:-1],"" # hack: if word ends with 'e' and dropping the 'e' leaves a valid word that's also in the dictionary, we DON'T want to drop this word on the grounds that espeak already gets it right, because if we do then adding 's' to this word may cause espeak to add 's' to the OTHER word ('-es' rule).
        if espeak_probably_right_already(espeakPronunc,new_e_pronunc):
            not_output_because_ok.append(word)
            continue
        if not unrelated_word: lines_output += 1
        outFile.write(word+" "+new_e_pronunc+" // from Festival's ("+pronunc+")")
        if espeakPronunc: outFile.write(", not [["+espeakPronunc+"]]")
        elif unrelated_word: outFile.write(" (here to stop espeak's affix rules getting confused by Festival's \""+unrelated_word+"\")")
        outFile.write("\n")
    print "Corrected(?) %d entries out of %d" % (lines_output,total_lines)
    if add_user_dictionary_also: convert_user_lexicon("festival","espeak",outFile)
    outFile.close()
    os.system("espeak --compile=en")
    if not_output_because_ok:
      print "Checking for unwanted side-effects of those corrections" # e.g. terrible as Terr + ible, inducing as in+Duce+ing
      proc=os.popen("espeak -q -x -v en-rp > /tmp/.pronunc 2>&1","w")
      progressCount = 0
      for w in not_output_because_ok:
          proc.write(w+"\n") ; proc.flush()
          percent = int(progressCount*100/len(not_output_because_ok))
          if not percent==oldPercent: sys.stdout.write(str(percent)+"%\r") ; sys.stdout.flush()
          oldPercent = percent
          progressCount += 1
      proc.close()
      outFile=open("en_extra","a") # append to it
      for word,pronunc in zip(not_output_because_ok,open("/tmp/.pronunc").read().split("\n")):
        pronunc = pronunc.strip().replace(" ","")
        if not pronunc==oldPronDic[word] and not espeak_probably_right_already(oldPronDic[word],pronunc):
          outFile.write(word+" "+oldPronDic[word]+" // (undo affix-side-effect from previous words that gave \""+pronunc+"\")\n")
      outFile.close()
      os.system("espeak --compile=en")
    return not_output_because_ok

def convert_user_lexicon(fromFormat,toFormat,outFile):
    if fromFormat=="festival": lex = eval('['+commands.getoutput("grep '^(lex.add.entry' ~/.festivalrc | sed -e 's/;.*//' -e 's/[^\"]*\"/[\"/' -e 's/\" . /\",(\"/' -e 's/$/\"],/' -e 's/[()]/ /g' -e 's/  */ /g'")+']')
    elif fromFormat=="espeak": lex = filter(lambda x:len(x)==2,[l.split()[:2] for l in open("en_extra").readlines()])
    elif fromFormat in ["acapela-uk","x-sampa"]:
        lex = []
        for l in open("acapela.txt").readlines():
            word, pronunc, ignore = l.split(None,2)
            if pronunc.startswith("#"): pronunc=pronunc[1:]
            lex.append((word,pronunc))
    elif fromFormat=="cepstral":
        lex = []
        for l in open("lexicon.txt").readlines():
            word, ignore, pronunc = l.split(None,2)
            lex.append((word,pronunc))
    else: assert 0, "Reading from '%s' lexicon file not yet implemented" % (fromFormat,)
    if toFormat=="mac": outFile.write("# I don't yet know how to add to the Mac OS X lexicon,\n# so here is a 'sed' command you can run on your text\n# to put the pronunciation inline:\n\nsed")
    elif "sapi" in toFormat: outFile.write("rem  You have to run this file\nrem  with ptts.exe in the same directory\nrem  to add these words to the SAPI lexicon\n\n")
    elif toFormat=="unicode-ipa": outFile.write("<HTML><HEAD>\n<META HTTP-EQUIV=\"Content-Type\" CONTENT=\"text/html; charset=utf-8\">\n</HEAD><BODY><TABLE>\n")
    for word, pronunc in lex:
        pronunc = convert(pronunc,fromFormat,toFormat)
        if toFormat=="espeak": outFile.write(word+" "+pronunc+"\n")
        elif "sapi" in toFormat: outFile.write("ptts -la "+word+" \""+pronunc+"\"\n")
        elif toFormat=="cepstral": outFile.write(word.lower()+" 0 "+pronunc+"\n")
        elif toFormat=="mac": outFile.write(" -e \"s/"+word+"/[[inpt PHON]]"+pronunc+"[[inpt TEXT]]/g\"")
        elif toFormat=="bbcmicro": outFile.write("> "+word.upper()+"_"+chr(128)+pronunc) # (specifying 'whole word'; remove the space before or the _ after if you want)
        elif toFormat=="unicode-ipa": outFile.write("<TR><TD>"+word+"</TD><TD>"+pronunc.encode("UTF-8")+"</TD></TR>\n")
        elif toFormat in ["acapela-uk","x-sampa"]: outFile.write(word+chr(9)+"#"+pronunc+chr(9)+"UNKNOWN\n") # TODO may be able to convert part-of-speech (NOUN etc) to/from some other formats e.g. Festival
        else: assert 0, "Writing to lexicon in %s format not yet implemented" % (format,)
    if toFormat=="mac": outFile.write("\n")
    elif toFormat=="bbcmicro": outFile.write(">**")
    elif toFormat=="unicode-ipa": outFile.write("</TABLE></BODY></HTML>\n")

first_word=True # hack for bbcmicro
def markup_inline_word(format,pronunc):
    global first_word
    if format=="espeak": return "[["+pronunc+"]]"
    elif format=="mac": return "[[inpt PHON]]"+pronunc+"[[inpt TEXT]]"
    elif "sapi" in format: return "<pron sym=\""+pronunc+"\"/>"
    elif format=="cepstral": return "<phoneme ph='"+pronunc+"'>p</phoneme>"
    elif format=="acapela-uk": return "\\Prn="+pronunc+"\\"
    elif format=="bbcmicro" and first_word:
       first_word = False
       return "*SPEAK "+pronunc
    elif format=="unicode-ipa": return pronunc.encode("utf-8") # UTF-8 output - ok for pasting into Firefox etc *IF* the terminal/X11 understands utf-8 (otherwise redirect to a file, point the browser at it, and set encoding to utf-8, or try --convert'ing which will o/p HTML)
    else: return pronunc # fallback - assume the user knows what to do with it

def sylcount(festival):
  # we treat @ as counting the same as the previous syllable (e.g. "fire",
  # "power") but this can vary in different songs
  count = inVowel = maybeCount = hadAt = 0
  festival = festival.split()
  for phone,i in zip(festival,range(len(festival))):
    if phone[0] in "aeiou": inVowel=0 # unconditionally start new syllable
    if phone[0] in "aeiou@12":
      if not inVowel: count += 1
      elif phone[0]=="@" and not hadAt: maybeCount = 1 # (e.g. "loyal", but NOT '1', e.g. "world")
      if "@" in phone: hadAt = 1 # for words like "cheerful" ("i@ 1 @" counts as one)
      inVowel = 1
      if phone[0]=="@" and i>=3 and festival[i-2:i]==["ai","1"] and festival[i-3] in ["s","h"]: # special rule for higher, Messiah, etc - like "fire" but usually 2 syllables
        maybeCount = 0 ; count += 1
    else:
      if not phone[0] in "drz": count += maybeCount # not 'r/z' e.g. "ours", "fired" usually 1 syllable in songs, "desirable" usually 4 not 5
      # TODO steward?  y u@ 1 d but usally 2 syllables
      inVowel = maybeCount = hadAt = 0
  return count
def hyphenate(word,numSyls):
  orig = word
  try: word,isu8 = word.decode('utf-8'),True
  except: isu8 = False
  pre=[] ; post=[]
  while word and not 'a'<=word[0].lower()<='z':
    pre.append(word[0]) ; word=word[1:]
  while word and not 'a'<=word[-1].lower()<='z':
    post.insert(0,word[-1]) ; word=word[:-1]
  if numSyls>len(word): return orig # probably numbers or something
  l = int((len(word)+numSyls/2)/numSyls) ; syls = []
  for i in range(numSyls):
    if i==numSyls-1: syls.append(word[i*l:])
    else: syls.append(word[i*l:(i+1)*l])
    if len(syls)>1:
      if len(syls[-1])>2 and syls[-1][0]==syls[-1][1] and not syls[-1][0].lower() in "aeiou":
        # repeated consonant at start - put one on previous
        syls[-2] += syls[-1][0]
        syls[-1] = syls[-1][1:]
      elif ((len(syls[-2])>2 and syls[-2][-1]==syls[-2][-2] and not syls[-2][-1].lower() in "aeiou") \
            or (syls[-1][0].lower() in "aeiouy" and len(syls[-2])>2)) \
            and filter(lambda x:x.lower() in "aeiou",list(syls[-2][:-1])):
        # repeated consonant at end - put one on next
        # or vowel on right: move a letter over (sometimes the right thing to do...)
        # (unless doing so leaves no vowels)
        syls[-1] = syls[-2][-1]+syls[-1]
        syls[-2] = syls[-2][:-1]
  word = ''.join(pre)+"- ".join(syls)+''.join(post)
  if isu8: word=word.encode('utf-8')
  return word

def main():
    if '--festival-dictionary-to-espeak' in sys.argv:
        try: festival_location=sys.argv[sys.argv.index('--festival-dictionary-to-espeak')+1]
        except IndexError:
            sys.stderr.write("Error: --festival-dictionary-to-espeak must be followed by the location of the festival OALD file (see help text)\n") ; sys.exit(1)
        try: open(festival_location)
        except:
            sys.stderr.write("Error: The specified OALD location '"+festival_location+"' could not be opened\n") ; sys.exit(1)
        try: open("en_list")
        except:
            sys.stderr.write("Error: en_list could not be opened (did you remember to cd to the eSpeak dictsource directory first?\n") ; sys.exit(1)
        convert_system_festival_dictionary_to_espeak(festival_location,not '--without-check' in sys.argv,not os.system("test -e ~/.festivalrc"))
    elif '--try' in sys.argv:
        i=sys.argv.index('--try')
        espeak = convert(' '.join(sys.argv[i+2:]),sys.argv[i+1],'espeak')
        os.popen("espeak -x","w").write(markup_inline_word("espeak",espeak))
    elif '--trymac' in sys.argv:
        i=sys.argv.index('--trymac')
        mac = convert(' '.join(sys.argv[i+2:]),sys.argv[i+1],'mac')
        os.popen("say -v Vicki","w").write(markup_inline_word("mac",mac))
        # Need to specify a voice because the default voice might not be able to take English phonemes (especially on 10.7+)
        # Vicki has been available since 10.3, as has the 'say' command (previous versions need osascript, see Gradint's code)
    elif '--phones' in sys.argv:
        i=sys.argv.index('--phones')
        format=sys.argv[i+1]
        w,r=os.popen4("espeak -q -x")
        w.write(' '.join(sys.argv[i+2:])) ; w.close()
        print ", ".join([" ".join([markup_inline_word(format,convert(word,"espeak",format)) for word in line.split()]) for line in filter(lambda x:x,r.read().split("\n"))])
    elif '--syllables' in sys.argv:
        i=sys.argv.index('--syllables')
        w,r=os.popen4("espeak -q -x")
        w.write('\n'.join(sys.argv[i+1:]).replace("!","").replace(":","")) ; w.close()
        rrr = r.read().split("\n")
        print " ".join([hyphenate(word,sylcount(convert(line,"espeak","festival"))) for word,line in zip(sys.argv[i+1:],filter(lambda x:x,rrr))])
    elif '--phones2phones' in sys.argv:
        i=sys.argv.index('--phones2phones')
        format1,format2 = sys.argv[i+1],sys.argv[i+2]
        text=' '.join(sys.argv[i+3:])
        if format1 in formats_where_space_separates_words:
          for w in text.split(): print markup_inline_word(format2, convert(w,format1,format2))
        else: print markup_inline_word(format2, convert(text,format1,format2))
    elif '--convert' in sys.argv:
        i=sys.argv.index('--convert')
        fromFormat = sys.argv[i+1]
        toFormat = sys.argv[i+2]
        assert not fromFormat==toFormat, "cannot convert a lexicon to its own format (that could result in it being truncated)"
        outFile = None
        if toFormat=="cepstral": fname="lexicon.txt"
        elif toFormat in ["acapela-uk","x-sampa"]: fname="acapela.txt"
        elif "sapi" in toFormat: fname="run-ptts.bat"
        elif toFormat=="mac": fname="substitute.sh"
        elif toFormat=="bbcmicro": fname="BBCLEX"
        elif toFormat=="espeak":
            try: open("en_list")
            except: assert 0, "You should cd to the espeak source directory before running this"
            os.system("mv en_extra en_extra~ ; grep \" // \" en_extra~ > en_extra") # keep the commented entries, so can incrementally update the user lexicon only
            fname="en_extra"
            outFile=open(fname,"a")
        elif toFormat=="unicode-ipa":
            fname="words-ipa.html" # just make a table of words and pronunciation
            try:
                open(fname)
                assert 0, fname+" already exists, I'd rather not overwrite it; delete it yourself if you want"
            except IOError: pass
            outFile=open(fname,"w")
        else: assert 0, "Don't know where to put lexicon of format '%s', try using --phones or --phones2phones options instead" % (toFormat,)
        if not outFile:
            l = 0
            try: l = open(fname).read()
            except: pass
            assert not l, "File "+fname+" already exists and is not empty; are you sure you want to overwrite it?  (Delete it first if so)"
            outFile=open(fname,"w")
        print "Writing lexicon entries to",fname
        convert_user_lexicon(fromFormat,toFormat,outFile)
        outFile.close()
        if toFormat=="espeak": os.system("espeak --compile=en")
    else:
        print program_name
        print "\nAvailable pronunciation formats:",', '.join(list(table[0]))
        print "\nUse --convert <from-format> <to-format> to convert a user lexicon file.  Expects Festival's .festivalrc to be in the home directory, or espeak's en_extra or Cepstral's lexicon.txt to be in the current directory.\nFor InfoVox/acapela, export the lexicon to acapela.txt in the current directory.\nE.g.: python lexconvert.py --convert festival cepstral"
        print "\nUse --try <format> <pronunciation> to try a pronunciation with eSpeak (requires 'espeak' command),\n e.g.: python lexconvert.py --try festival h @0 l ou1\n or: python lexconvert.py --try unicode-ipa '\\u02c8\\u0279\\u026adn\\u0329' (for Unicode put '\\uNNNN' or UTF-8)\n (it converts to espeak format and then uses espeak to play it)\nUse --trymac to do the same as --try but with Mac OS 'say' instead of 'espeak'"
        print "\nUse --phones2phones <format1> <format2> <phones in format1> to perform a one-off conversion of phones from format1 to format2."
        print "\nUse --phones <format> <words> to convert 'words' to phones in format 'format'.  espeak will be run to do the text-to-phoneme conversion, and the output will then be converted to 'format'.\nE.g.: python lexconvert.py --phones unicode-ipa This is a test sentence.\nNote that some commercial speech synthesizers do not work well when driven entirely from phones, because their internal format is different and is optimised for normal text."
        print "\nUse --syllables <words> to attempt to break 'words' into syllables for music lyrics (uses espeak to determine how many syllables are needed)"
        print "\nUse --festival-dictionary-to-espeak <location> to convert the Festival Oxford Advanced Learners Dictionary (OALD) pronunciation lexicon to ESpeak.\nYou need to specify the location of the OALD file in <location>,\ne.g. for Debian festlex-oald package: python lexconvert.py --festival-dictionary-to-espeak /usr/share/festival/dicts/oald/all.scm\nor if you can't install the Debian package, try downloading http://ftp.debian.org/debian/pool/non-free/f/festlex-oald/festlex-oald_1.4.0.orig.tar.gz, unpack it into /tmp, and do: python lexconvert.py --festival-dictionary-to-espeak /tmp/festival/lib/dicts/oald/oald-0.4.out\nIn all cases you need to cd to the espeak source directory before running this.  en_extra will be overwritten.  Converter will also read your ~/.festivalrc if it exists.  (You can later incrementally update from ~/.festivalrc using the --convert option; the entries from the system dictionary will not be overwritten in this case.)  Specify --without-check to bypass checking the existing espeak pronunciation for OALD entries (much faster, but makes a larger file and in some cases compromises the pronunciation quality)."

if __name__ == "__main__": main()
