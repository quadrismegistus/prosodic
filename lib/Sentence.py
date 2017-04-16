from entity import entity,being


class Sentence(entity):
    def __init__(self,wordtokens,tree):
        self.children=wordtokens
        self.tree=tree

        # link wordtokens to this sentence
        for wtok in self.children:
            wtok.sentence = self

    def __getitem__(self,key):
        return self.children[key]

    def __repr__(self):
		return "<"+self.classname()+":"+' '.join([self.u2s(wtok.token) for wtok in self.children])+">"
