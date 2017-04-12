from entity import entity,being


class WordToken(entity):
    def __init__(self,words):
        self.children=words

    def __getitem__(self,key):
        return self.children[key]
