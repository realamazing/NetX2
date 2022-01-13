import nltk
from nltk import *
from nltk.tag import stanford
from nltk.tag.stanford import StanfordPOSTagger
from nltk.tokenize import word_tokenize



class NLP():
    def __init__(self) -> None:

        java_path = r"C:\Program Files\Java\jre1.8.0_301\bin" 
        os.environ["JAVAHOME"] = java_path

        _path_to_model = 'stanford-tagger/models/english-bidirectional-distsim.tagger'
        _path_to_jar = 'stanford-tagger/stanford-postagger.jar'
        self.st = StanfordPOSTagger(_path_to_model,_path_to_jar,encoding = "utf-8")

        grammar = r"""
            NP: {<PRP\$>?<JJ.?>*<NN.*>+}   # chunk determiner/possessive, adjectives and nouns
                {<PRP>+} # chains of proper nouns
                {<JJ.*>+} # adjectives
                {<VBG>} # gerunds
            NP: {<NP>(<CC><NP>)+} # groups of nouns through and
            VP: {<VB.*|IN>+}# combinations of verbs and prepositions make up a verb phrase
            C: {<VP><NP>}
               {<C><C>}
        """
        self.parser = nltk.RegexpParser(grammar,"S",5)

    def findSource(self,tree,s=None):  
        s = s
        if tree.label() in ['NP','VP']:
            return tree
        else:
            if tree[0].label() == "C":
                s = self.findSource(tree[0])
            elif tree[0].label() in ['NP','VP']:
                return tree[0]
        return s

    def toList(self,chunk,f=[]):
        f = f
        if chunk.height() == 3:
            for i in chunk:
                if isinstance(i,ParentedTree):
                    f = self.toList(i,f)
        if chunk.height() == 2:
            s = ' '.join([i[0] for i in chunk])
            f.append(s)
        return f

    def getPairs(self,sentence):
        #------------------------- Preformating -----------------------------
        sentence = sentence.lower()
        sentence = word_tokenize(sentence)
        tokens = self.st.tag(sentence)
        for tok in tokens:
            if tok[1] == "DT":
                tokens.remove(tok)
        # ----------------------- Parsing and chunking ------------------------
        result = self.parser.parse(tokens)
        result = ParentedTree.convert(result)
        result.pretty_print()

        trees = [i for i in result.subtrees()]

        relats = []
        for i in trees:
            label = i.label()
            if label == "C" and (i[0].label() in ['NP','VP'] and i[1].label() in ['NP','VP']): # get all Cs with noun and verb phrase terminals
                relats.append(i)
        findLeft = lambda x: self.findSource(x.parent()) if self.findSource(x.parent()) != self.findSource(x) else findLeft(x.parent()) # find source of relat by checking up chain of parents until source is different
        pairs = []
        for i in relats:
            sources = self.toList(findLeft(i),[])
            relationship = self.toList(self.findSource(i,[])) # source is relationship
            destination = self.toList(i[1],[]) # destination is next
            pairs.append([sources,relationship,destination])
        return pairs

if __name__ == '__main__':
    #sentence = "The quick brown fox jumped over the lazy dog"
    #sentence = "The fox went between the shed and tree"
    #sentence = "Caesar led the roman armies in the Gailiac wars"
    #sentence = "Caesar caused the fall of the roman republic through greed"
    #sentence = "Pompey wanted laws passed for land pensions"
    #sentence = "Caesar was a member of the first trumvirate and the second triumvirate"
    #sentence = "Julius Gailius Caesar was a statesman and a roman dictator and a leader"
    sentence = "Caesar and Pompey formed the first triumvirate"
    #sentence = "The fox jumped over the dog"
    #sentence = "He was dying"
    #sentence = "He is dead"
    nlp = NLP()
    print(nlp.getPairs(sentence))