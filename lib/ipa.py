# -*- coding: UTF-8 -*-

## NOTES
# changed ɐ to be a non-vowel [syll = False]

#ipakey = ['[+approx]','[+cons]','[+son]','[+syll]','[+constr]','[+spread]','[+voice]','vlength.[+long]','[+cont_acoust]','[+cont_artic]','[+del_rel]','[+lat]','[+nas]','[+strid]','[+tap]','[+trill]','[+coronal]','[+dorsal]','[+labial]','[+labiodental]','[+ant]','[+dist]','[+back]','[+front]','[+high]','[+low]','[+tense]','[+round]']
ipakey = ['approx','cons','son','syll','constr','spread','voice','long','cont_acoust','cont_artic','delrel','lat','nas','strid','tap','trill','coronal','dorsal','labial','labiodental','ant','dist','back','front','high','low','tense','round']
ipa = {}
ipa[u'p'] = [False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,False,False,True,False,True,False,False,None,False,False,None,False]
ipa[u'm']=[False,True,True,False,False,False,True,None,True,False,False,False,True,False,False,False,False,False,True,False,True,False,False,None,False,False,None,False]
ipa[u'pʰ']=[False,True,False,False,False,True,False,None,False,False,False,False,False,False,False,False,False,False,True,False,True,False,False,None,False,False,None,False]
ipa[u't']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'b']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,False,False,True,False,True,False,False,None,False,False,None,False]
ipa[u'd']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'k']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,False,True,False,False,False,False,True,None,True,False,None,False]
ipa[u'd̪']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u't̪']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'n']=[False,True,True,False,False,False,True,None,True,False,False,False,True,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ɳ']=[False,True,True,False,False,False,True,None,True,False,False,False,True,False,False,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'ɲ']=[False,True,True,False,False,False,True,None,True,False,False,False,True,False,False,False,True,True,False,False,False,True,False,None,True,False,None,False]
ipa[u'g']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,False,True,False,False,False,False,True,None,True,False,None,False]
ipa[u'f']=[False,True,False,False,False,False,False,None,True,True,False,False,False,False,False,False,False,False,True,True,True,False,False,None,False,False,None,False]
ipa[u'v']=[False,True,False,False,False,False,True,None,True,True,False,False,False,False,False,False,False,False,True,True,True,False,False,None,False,False,None,False]
ipa[u'ʃ']=[False,True,False,False,False,False,False,None,True,True,False,False,False,True,False,False,True,False,False,False,False,True,False,None,False,False,None,False]
ipa[u's']=[False,True,False,False,False,False,False,None,True,True,False,False,False,True,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'z']=[False,True,False,False,False,False,True,None,True,True,False,False,False,True,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ʒ']=[False,True,False,False,False,False,True,None,True,True,False,False,False,True,False,False,True,False,False,False,False,True,False,None,False,False,None,False]
ipa[u'j']=[True,False,True,False,False,False,True,None,True,True,False,False,False,False,False,False,True,True,False,False,False,False,False,None,True,False,None,False]
ipa[u'ɦ']=[False,True,False,False,False,True,True,None,True,True,False,False,False,False,False,False,False,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'h']=[False,True,False,False,False,True,False,None,True,True,False,False,False,False,False,False,False,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'q']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,False,True,False,False,False,False,True,None,False,False,None,False]
ipa[u'ɸ']=[False,True,False,False,False,False,False,None,True,True,False,False,False,False,False,False,False,False,True,False,True,False,False,None,False,False,None,False]
ipa[u'ʀ']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,True,False,True,False,False,False,False,True,None,False,False,None,False]
ipa[u'ʁ']=[False,True,False,False,False,False,True,None,True,True,False,False,False,False,False,False,False,True,False,False,False,False,True,None,False,False,None,False]
ipa[u'ɣ']=[False,True,False,False,False,False,True,None,True,True,False,False,False,False,False,False,False,True,False,False,False,False,True,None,True,False,None,False]
ipa[u'ɬ']=[False,True,False,False,False,False,False,None,True,True,False,True,False,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ɮ']=[False,True,False,False,False,False,True,None,True,True,False,True,False,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'x']=[False,True,False,False,False,False,False,None,True,True,False,False,False,False,False,False,False,True,False,False,False,False,True,None,True,False,None,False]
ipa[u'ʤ']=[False,True,False,False,False,False,True,None,False,False,True,False,False,True,False,False,True,False,False,False,False,True,False,None,False,False,None,False]
ipa[u'ʧ']=[False,True,False,False,False,False,False,None,False,False,True,False,False,True,False,False,True,False,False,False,False,True,False,None,False,False,None,False]
ipa[u'ð']=[False,True,False,False,False,False,True,None,True,True,False,False,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'θ']=[False,True,False,False,False,False,False,None,True,True,False,False,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'β']=[False,True,False,False,False,False,True,None,True,True,False,False,False,False,False,False,False,False,True,False,True,False,False,None,False,False,None,False]
ipa[u'ç']=[False,True,False,False,False,False,False,None,True,True,False,False,False,False,False,False,True,True,False,False,False,True,False,None,True,False,None,False]
ipa[u'ʂ']=[False,True,False,False,False,False,False,None,True,True,False,False,False,True,False,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'ʐ']=[False,True,False,False,False,False,True,None,True,True,False,False,False,True,False,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'l']=[True,True,True,False,False,False,True,None,True,True,False,True,False,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'r']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,True,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ɾ']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,True,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ɥ']=[True,False,True,False,False,False,True,None,True,True,False,False,False,False,False,False,True,True,True,False,False,False,False,None,True,False,None,True]
ipa[u'ʔ']=[False,True,False,False,True,False,False,None,False,False,False,False,False,False,False,False,False,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'ŋ']=[False,True,True,False,False,False,True,None,True,False,False,False,True,False,False,False,False,True,False,False,False,False,True,None,True,False,None,False]
ipa[u'ɻ']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ħ']=[False,True,False,False,False,False,False,None,True,True,False,False,False,False,False,False,False,True,False,False,False,False,True,None,False,True,None,False]
ipa[u'χ']=[False,True,False,False,False,False,False,None,True,True,False,False,False,False,False,False,False,True,False,False,False,False,True,None,False,False,None,False]
ipa[u'n̪']=[False,True,True,False,False,False,True,None,True,False,False,False,True,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'kʰ']=[False,True,False,False,False,True,False,None,False,False,False,False,False,False,False,False,False,True,False,False,False,False,True,None,True,False,None,False]
ipa[u'tʰ']=[False,True,False,False,False,True,False,None,False,False,False,False,False,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ʈ']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'ʈʰ']=[False,True,False,False,False,True,False,None,False,False,False,False,False,False,False,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'ɖ']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'ɖʰ']=[False,True,False,False,False,True,True,None,False,False,False,False,False,False,False,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'ʝ']=[False,True,False,False,False,False,True,None,True,True,False,False,False,False,False,False,False,True,False,False,False,True,False,None,True,False,None,False]
ipa[u'kʷ']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,False,True,True,False,False,False,True,None,True,False,None,True]
ipa[u'gʷ']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,False,True,True,False,False,False,True,None,True,False,None,True]
ipa[u'ɢ']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,False,True,False,False,False,False,True,None,False,False,None,False]
ipa[u'kʲ']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,True,True,False,False,False,False,False,None,True,False,None,False]
ipa[u'gʲ']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,True,True,False,False,False,False,False,None,True,False,None,False]
ipa[u'ɱ']=[False,True,True,False,False,False,True,None,True,False,False,False,True,False,False,False,False,False,True,True,True,False,False,None,False,False,None,False]
ipa[u'ʋ']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,False,False,False,True,True,True,False,False,None,False,False,None,False]
ipa[u'c']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,True,True,False,False,False,True,False,None,True,False,None,False]
ipa[u'ʝ']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,True,True,False,False,False,True,False,None,True,False,None,False]
ipa[u'n̥']=[False,True,True,False,False,False,False,None,True,False,False,False,True,False,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'm̥']=[False,True,True,False,False,False,False,None,True,False,False,False,True,False,False,False,True,False,True,False,False,False,False,None,False,False,None,False]
ipa[u'pʷ']=[False,True,False,False,False,False,False,None,False,False,False,False,False,False,False,False,False,False,True,False,True,False,False,None,False,False,None,True]
ipa[u'bʷ']=[False,True,False,False,False,False,True,None,False,False,False,False,False,False,False,False,False,False,True,False,True,False,False,None,False,False,None,True]
ipa[u'ɬ̪']=[False,True,False,False,False,False,False,None,True,True,False,True,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'ɮ̪']=[False,True,False,False,False,False,True,None,True,True,False,True,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'r̪']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,True,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'ɾ̪']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,True,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'ɹ̪']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'w̃']=[True,True,True,False,False,False,True,None,True,True,False,False,True,False,False,False,False,True,True,False,True,False,True,None,True,False,None,True]
ipa[u'cʰ']=[False,True,False,False,False,True,False,None,False,False,False,False,False,False,False,False,True,True,False,False,False,True,False,None,True,False,None,False]
ipa[u't̪ʰ']=[False,True,False,False,False,True,False,None,False,False,False,False,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u's̪']=[False,True,False,False,False,False,False,None,True,True,False,False,False,True,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'l̪']=[True,True,True,False,False,False,True,None,True,True,False,True,False,False,False,False,True,False,False,False,True,True,False,None,False,False,None,False]
ipa[u'ʟ']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,False,False,True,False,False,False,False,False,None,True,True,None,False]
ipa[u'ɭ']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'ʎ']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,False,False,True,True,False,False,False,True,False,None,True,False,None,False]
ipa[u'ʦ']=[False,True,False,False,False,False,False,None,False,False,True,False,False,True,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ʣ']=[False,True,False,False,False,False,True,None,False,False,True,False,False,True,False,False,True,False,False,False,True,False,False,None,False,False,None,False]
ipa[u'ɽ']=[True,True,True,False,False,False,True,None,True,True,False,False,False,False,True,False,True,False,False,False,False,False,False,None,False,False,None,False]
ipa[u'o']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,False,True,True]
ipa[u'ɔ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,False,False,True]
ipa[u'ɐ']=[None,False,True,False,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,False,True,True,False]
ipa[u'w']=[None,False,True,False,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,False,False,False,False]
ipa[u'ɤ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,False,True,False]
ipa[u'ɨ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,True,False,True,False]
ipa[u'ə']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,False,False,False,False]
ipa[u'i']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,True,False]
ipa[u'iː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,True,False]
ipa[u'y']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,True,True]
ipa[u'yː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,True,True]
ipa[u'ɪ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,False,False]
ipa[u'ɪː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,False,False]
ipa[u'ʏ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,False,True]
ipa[u'ʏː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,False,True]
ipa[u'e']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,True,False]
ipa[u'eː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,True,False]
ipa[u'ø']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,True,True]
ipa[u'øː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,True,True]
ipa[u'ɛ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,False,False]
ipa[u'ɛː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,False,False]
ipa[u'œ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,False,True]
ipa[u'œː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,False,True]
ipa[u'æ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,True,True,False]
ipa[u'æː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,True,True,False]
ipa[u'ɶ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,True,False,True]
ipa[u'ʉ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,True,False,True,True]
ipa[u'ʉː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,True,False,True,True]
ipa[u'a']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,False,True,False,False]
ipa[u'aː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,False,True,False,False]
ipa[u'ɯ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,True,False,True,False]
ipa[u'ɯː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,True,False,True,False]
ipa[u'u']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,True,False,True,True]
ipa[u'uː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,True,False,True,True]
ipa[u'ʊ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,True,False,False,True]
ipa[u'ʊː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,True,False,False,True]
ipa[u'oː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,False,True,True]
ipa[u'ʌ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,False,False,False]
ipa[u'ʌː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,False,False,False]
ipa[u'ɔː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,False,False,True]
ipa[u'ɑ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,True,False,False]
ipa[u'ɑː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,True,False,False]
ipa[u'ɒ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,True,False,True]
ipa[u'ɒː']=[None,False,True,True,None,None,None,True,None,None,None,None,False,None,None,None,None,None,None,None,None,None,True,False,False,True,False,True]
ipa[u'œ̃']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,False,False,False,True]
ipa[u'ɵ']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,False,False,False,False,True]
ipa[u'ʉ̞']=[None,False,True,True,None,None,None,False,None,None,None,None,False,None,None,None,None,None,None,None,None,None,False,True,True,False,True,True]
ipa[u'ẽ']=[None,False,True,True,None,None,None,True,None,None,None,None,True,None,None,None,None,None,None,None,None,None,False,True,False,False,True,False]
ipa[u'ɛ̃']=[None,False,True,True,None,None,None,False,None,None,None,None,True,None,None,None,None,None,None,None,None,None,False,True,False,False,False,False]
ipa[u'ɔ̃']=[None,False,True,True,None,None,None,False,None,None,None,None,True,None,None,None,None,None,None,None,None,None,True,False,False,False,False,True]
ipa[u'ɑ̃']=[None,False,True,True,None,None,None,False,None,None,None,None,True,None,None,None,None,None,None,None,None,None,True,False,False,True,False,False]
ipa[u'ɑ̃ː']=[None,False,True,True,None,None,None,False,None,None,None,None,True,None,None,None,None,None,None,None,None,None,True,False,False,True,False,False]
ipa[u'ã']=[None,False,True,True,None,None,None,False,None,None,None,None,True,None,None,None,None,None,None,None,None,None,False,False,False,True,False,None]

ipa2cmu={}
ipa2cmu['ɑ'] = 'AA' # father, hot
ipa2cmu['æ'] = 'AE' # had
ipa2cmu['ə'] = 'AH' # sofA
ipa2cmu['ʌ'] = 'AH' # but
ipa2cmu['ɔː'] = 'AO' # caught
ipa2cmu['aʊ'] = 'AW'
ipa2cmu['aɪ'] = 'AY' # hide
ipa2cmu['ʧ'] = 'CH' # cheese
ipa2cmu['ð'] = 'DH' # thee,this
ipa2cmu['ɛ'] = 'EH' # head
ipa2cmu['ɛː'] = 'ER' # ER[FIX]
ipa2cmu['eɪ'] = 'EY' # todAy
ipa2cmu['h'] = 'HH' # harm
ipa2cmu['ɪ'] = 'IH' # hid
ipa2cmu['iː'] = 'IY' # heed
ipa2cmu['ŋ'] = 'NG' # sing
ipa2cmu['oʊ'] = 'OW' # hoed
ipa2cmu['ɔɪ'] = 'OY' # joy
ipa2cmu['ʃ'] = 'SH' # shh
ipa2cmu['θ'] = 'TH' # the
ipa2cmu['ʊ'] = 'UH' # hood
ipa2cmu['uː'] = 'UW' # boot
ipa2cmu['ʒ'] = 'ZH'
ipa2cmu['b'] = 'B'
ipa2cmu['d'] = 'D'
ipa2cmu['f'] = 'F'
ipa2cmu['g'] = 'G'
ipa2cmu['ʤ'] = 'JH'
ipa2cmu['k'] = 'K'
ipa2cmu['l'] = 'L'
ipa2cmu['m'] = 'M'
ipa2cmu['n'] = 'N'
ipa2cmu['p'] = 'P'
ipa2cmu['r'] = 'R'
ipa2cmu['s'] = 'S'
ipa2cmu['t'] = 'T'
ipa2cmu['v'] = 'V'
ipa2cmu['w'] = 'W'
ipa2cmu['j'] = 'Y'
ipa2cmu['z'] = 'Z'


d_sampa2ipa={}
sampa_table=u"""i	i
I	I
e	e
E	ɛ
{	æ
y	y
2	ø
9	œ
1	ɨ
@	ə
6	ɐ
3	ɜ
a	a
}	ʉ
8	ɵ
&	ɶ
M	ɯ
7	ɤ
V	ʌ
A	ɑ
u	u
U	ʊ 
o	o
O	ɔ 
Q	ɒ
p	p
b	b
t	t
d	d
tS	ʧ
dZ	ʤ
c	c
J\	ɟ
k	k
g	g
q	q
p\	φ
B	β 
f	f
v	v
T	θ 
D	ð 
s	s
z	z
S	ʃ
Z	ʒ
C	ç
j\	ʝ
jj	ʝ
x	x
G	γ
M\	ɰ
h	h
h\	ɦ
m	m
F	ɱ
n	n
J	ɲ
N	ŋ
l	l
L	ʎ
5	ɫ
4	ɾ
r	ɽ
r\`	ɻ
R	ʀ
w	w
H	ɥ 
j	j
aI	aɪ
AI	aɪ
aU	aʊ
EI	ɛɪ
OY	ɔɪ
UI	ʊɪ 
ts	ʦ
Y	ʏ
pf	pʰ
r=	ɽ"""
for ln in sampa_table.split('\n'):
	sampa,ipa_str=ln.split('\t')
	d_sampa2ipa[sampa.strip()]=ipa_str.strip()

d_ipa2sampa={}
for sm,ip in d_sampa2ipa.items():
	d_ipa2sampa[ip]=sm


## FORMANTS
formantd={}
x=u"""i	240	2400
y	235	2100
e	390	2300
ø	370	1900
ɛ	610	1900
œ	585	1710
a	850	1610
ɶ	820	1530
ɑ	750	940
ɒ	700	760
ʌ	600	1170
ɔ	500	700
ɤ	460	1310
o	360	640
ɯ	300	1390
u	250	595"""
f1s=[]
f2s=[]
for ln in x.split('\n'):
	_ipa,f1,f2=ln.strip().split()
	f1s+=[int(f1)]
	f2s+=[int(f2)]
	formantd[_ipa]=[int(f1),int(f2)]
maxf1,minf1=max(f1s),min(f1s)
maxf2,minf2=max(f2s),min(f2s)
f1_range=maxf1-minf1
f2_range=maxf2-minf2
for _ipa in formantd:
	formantd[_ipa][0] = (formantd[_ipa][0] - minf1) / float(f1_range)
	formantd[_ipa][1] = (formantd[_ipa][1] - minf2) / float(f2_range)
	#print _ipa,formantd[_ipa]

ipa2featd={}
for ph,vals in ipa.items():
	ipa2featd[ph]=dict(zip(ipakey,vals))



def sampa2ipa(sampa):
	import lexconvert
	if sampa == 'r=':
		return u'ɛː'
	return lexconvert.convert(sampa,'x-sampa','unicode-ipa')
	sampa=sampa.replace(u'?',u'')
	if not sampa: return sampa
	if ':' in sampa:
		colon=u'ː'
		sampa=sampa.replace(u':',u'')
	else:
		colon=u''

	if not sampa in d_sampa2ipa and len(sampa)==2:
		#print "?!!",sampa
		return sampa2ipa(sampa[0]) + sampa2ipa(sampa[1])
	else:
		return d_sampa2ipa[sampa] + colon