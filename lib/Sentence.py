from entity import entity,being


class Sentence(entity):
    def __init__(self,tree,wordtokens):
        self.children=wordtokens
        self.tree=tree

    def __getitem__(self,key):
        return self.children[key]
