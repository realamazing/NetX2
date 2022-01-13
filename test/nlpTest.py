from pathlib import Path
import spacy
from spacy import displacy
from spacy.matcher import Matcher
from spacy.util import filter_spans

nlp = spacy.load('en_core_web_sm')

def findSources(obj,nouns,verbs):
    s = []
    if obj.dep_ == 'ROOT':
        for child in obj.children:
            if child.dep_ == 'nsubj':
                s.append(child)
                for c in child.conjuncts:
                    s.append(c)
    if obj.dep_ == 'prep' and obj.pos_ in ['VERB','AUX','ADP']:
        if obj.head.dep_ in ['ROOT','dobj','pobj'] and obj.head.pos_ in ['VERB','AUX','ADP']:
            s.append(obj.head)
        else:
            s = s + findSources(obj.head,nouns,verbs)
    if obj.dep_ in ['attr','dobj','pobj'] and obj.pos_ in ['NOUN','PROPN']:
        if obj.head.dep_ in ['ROOT','dobj','pobj'] and obj.head.pos_ in ['VERB','AUX','ADP']:
            s.append(obj.head)
        else:
            s = s + findSources(obj.head,nouns,verbs)
    if obj.dep_ == 'acl' and obj.pos_ in ['VERB','AUX','ADP']:
        if obj.head.dep_ in ['ROOT','dobj','pobj'] and obj.head.pos_ in ['VERB','AUX','ADP']:
            s.append(obj.head)
        else:
            s = s + findSources(obj.head,nouns,verbs)
    return s

def findDestinations(obj,nouns,verbs):
    d = []
    if obj.dep_ == 'ROOT':
        for child in obj.children:
            if child.dep_ in ['dobj','attr','pobj']:
                d.append(child)
                for c in child.conjuncts:
                    d.append(c)
    if obj.dep_ == 'prep' and obj.pos_ in ['VERB','AUX','ADP']:
        for child in obj.children:
            if child.dep_ in ['dobj','attr','pobj']:
                d.append(child)
                for c in child.conjuncts:
                    d.append(c)
    return d

def nlpCreation(text):
    text = text.lower()
    texts = text.split(',')

    docs = [nlp(t) for t in texts]

    entitys = []
    relationships = []

    for doc in docs:
        verbs = []
        nouns = []
        nouns = [chunk for chunk in doc.noun_chunks]
        for token in doc:
            p = token.pos_
            d = token.dep_
            if p not in ['DET','PUNCT','SPACE','CCONJ']:
                if p in ['AUX','VERB','ADP'] and d in ['prep','ROOT']:
                    verbs.append(token)
                print(token,p,token.head,token.dep_,spacy.explain(token.dep_))
        print('----')
        print(verbs)
        print(nouns)
        print('--')
        for verb in verbs:
            sources = findSources(verb,nouns,verbs)
            destinations = findDestinations(verb,nouns,verbs)
            print(sources,verb,destinations)
        print('----')
        ###########################################################
        if display:
            options = {"collapse_phrases": False}
            output_path = Path(f"quick.svg")
            svg = displacy.render(docs[0],'dep',options=options)
            with output_path.open("w",encoding="utf-8") as fh:
                fh.write(svg)

display = True
text = 'Gaius Julius Caesar was a Roman general and statesman, Caesar lead the roman armies in the Gailiac wars, Caesar is a memeber of the first triumvirate and the second triumvirate,Pompey wanted laws passed for land pensions'
text = 'The fox jumped over the dog'
nlpCreation(text)
#displacy.serve(docs[0], style='dep')
