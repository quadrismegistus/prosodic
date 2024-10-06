from ..imports import *
from .trees import recurse_tree
NLP_PARSE_POSTAG=True
NLP_PARSE_TOKENIZE=True
NLP_PARSE_CONSTITUENCY=True
NLP_PARSE_DEPPARSE=True
NLPD={}
# badcols={'feats','id','text'}
badcols={'feats','start_char','end_char','id','text','misc','lemma'}

def get_nlp(
        lang=DEFAULT_LANG,
        
        pretokenized=True,
        postag=NLP_PARSE_POSTAG,
        tokenize=NLP_PARSE_TOKENIZE,
        constituency=NLP_PARSE_CONSTITUENCY,
        depparse=NLP_PARSE_DEPPARSE,

        processors=[],
        verbose=None,
        **kwargs
        ):
    global NLPD

    if verbose is None:
        resource_path = os.path.expanduser(f'~/stanza_resources/{lang}')
        resource_exists = os.path.exists(resource_path)
        verbose = not resource_exists

    if not processors:
        processors=get_processors(
            constituency=constituency,
            depparse=depparse,
            postag=postag
        )
    
    procstr=','.join(processors)
    
    kwargs=dict(
        lang=lang,
        tokenize_pretokenized=pretokenized,
        processors=procstr,
    )

    key=tuple(kwargs.items())

    if not key in NLPD:
        # eprint('Loading NLP model:',kwargs)
        import stanza
        kwargs2={**dict(verbose=verbose), **kwargs}
        try:
            NLPD[key] = stanza.Pipeline(**kwargs2)
        # except stanza.pipeline.core.ResourcesFileNotFoundError:
        except Exception as e:
            log.error(e)
            lang = kwargs.get('lang')
            eprint(f'[cadence] Downloading stanza NLP model for language = "{lang}"')
            stanza.download(lang)
            try:
                NLPD[key] = stanza.Pipeline(**kwargs2)
            # except stanza.pipeline.core.ResourcesFileNotFoundError:
            except Exception as e:
                log.error(e)
                raise Exception(f'[cadence] Cannot download stanza model for language = "{lang}"')
        
        NLPD[key].procstr=procstr
        # NLPD[key].processors=processors
    return NLPD[key]




def get_processors(
        tokenize=True,
        postag=True,
        constituency=True,
        depparse=True,
        **kwargs):
    #o=dict(DEFAULT_PROCESSORS)
    o={}
    if tokenize:
        o['tokenize']=''
    if postag:
        o['tokenize']=''
        o['pos']=''
        o['lemma']=''
    if constituency:
        o['tokenize']=''
        o['pos']=''
        o['constituency']=''
    if depparse:
        o['tokenize']=''
        o['pos']=''
        o['lemma']=''
        o['depparse']=''
    return sorted(list(o.keys()))




########
# Tokenize NLP
########


### NLP FUNCS
# @stash.stashed_result
def get_nlp_doc(doc_ll_or_txt,nlp=None,**kwargs):
    if nlp is None: nlp=get_nlp(**kwargs)
    try:
        doc=nlp(doc_ll_or_txt)
        # fix
        fix_nlp_doc_constituency_bug(doc)
        return doc
    except Exception as e:
        # eprint(f'!! NLP Parser error: {e}')
        pass

COLS_RENAMER_NLP=dict(
    deprel='dep_type',
    head='dep_head',
    upos='pos_upos',
    xpos='pos_xpos',
    lemma='word_lemma',
)


def get_nlp_doc_wordfeat_df(doc,**kwargs):
    if doc is None: return pd.DataFrame()
    ld=[]
    sents=doc.sentences
    sentd_orig=None
    for sent_i, sent in enumerate(sents):
        ## Get Word Info
        for word_i,word in enumerate(sent.tokens):
            feats=word.to_dict()[0]
            statd=dict(
                # (v,feats[k])
                # for k,v in COLS_RENAMER_NLP.items()
                # if k in feats
                (COLS_RENAMER_NLP.get(k,k), feats[k])
                for k in feats
                if k not in badcols
            )
            for feat in feats.get('feats','').split('|'):
                if not feat: continue
                fk,fv=feat.split('=',1)
                statd[f'pos_{fk.lower()}']=fv
            dx={
                'sent_i': sent_i+1,
                'word_i': word_i+1,
                'word_str':word.text,
                **statd
            }
            ld.append(dx)
    return pd.DataFrame(ld).fillna('')

def fix_nlp_doc_constituency_bug(doc,**kwargs):
    sentd_orig={}
    sents = doc.sentences
    for sent_i,sent in enumerate(sents):
        sent.i=sent_i+1
        sentd_orig[get_sent_id_tokens(sent)] = sent
    for sent_i,sent in enumerate(sents):
        if hasattr(sent,'constituency'):
            sent_id_constituency=get_sent_id_constituency(sent)
            if sent_id_constituency not in sentd_orig: continue
            sent_orig=sentd_orig[sent_id_constituency]
            if hasattr(sent_orig,'constituency'):
                sent.constituency,sent_orig.constituency = sent_orig.constituency,sent.constituency
    
    doc.sentences = sents


def get_nlp_doc_constituency_df(doc,**kwargs):
    if doc is None: return pd.DataFrame()
    ## Constituency?
    ld=[]
    sents=doc.sentences
    sentd_orig=None

    depthstrd=Counter()
    def getdepthstr(lvlstr):
        lvlstr=lvlstr.split('-',1)[-1]
        depthstrd[lvlstr]+=1
        return f'{lvlstr}-{depthstrd[lvlstr]}'

    pathseend={}

    for sent_i, sent in enumerate(sents):
        if hasattr(sent,'constituency'):
            senttree=recurse_tree(sent.constituency, node_i=0, path=[])
            for word_i,word_constituency_path in enumerate(senttree):
                word_constituency_path_str='('.join(word_constituency_path)
                word_constituency_path_nolvl=[xx.split('-',1)[-1] for xx in word_constituency_path]
                constituency_depth=len(word_constituency_path)
                dx={
                    'sent_i': sent.i,
                    'word_i': word_i+1,
                    'word_depth':constituency_depth,
                    # 'word_constituency':word_constituency_path_str,
                }
                
                # max_wc_len=10
                # for wci in range(2,len(word_constituency_path)+1):
                #     if wci>max_wc_len: break
                #     wcpath=word_constituency_path[:wci]
                #     pathseen=tuple(wcpath)
                #     if not pathseen in pathseend: pathseend[pathseen]=f'{word_i+1:03}'
                #     newlevel=pathseend[pathseen]
                #     wcpathstr=f'{newlevel}_{"(".join(wcpath)}'
                #     dx[f'sent_depth{wci-1}']=wcpathstr
                ld.append(dx)
    return pd.DataFrame(ld).fillna('')


def get_nlp_feats_df(doc,**kwargs):
    df_feats=get_nlp_doc_wordfeat_df(doc,**kwargs)
    # display(df_feats)

    df_const=get_nlp_doc_constituency_df(doc,**kwargs)
    # display(df_const)

    if len(df_feats) and len(df_const):
        return df_feats.merge(df_const,on=['sent_i','word_i'],how='inner')
    elif len(df_feats):
        return df_feats
    elif len(df_const):
        return dc_const
    return pd.DataFrame()



def get_sent_id_tokens(sent,hash=True):
    o=[tok.text for tok in sent.tokens]
    return tuple(o)
def get_sent_id_constituency(sent,hash=True):
    o=[tok.split()[-1] for tok in str(sent.constituency).split(')') if tok]
    o=[x.replace('(-RRB-',')') for x in o]
    return tuple(o)




