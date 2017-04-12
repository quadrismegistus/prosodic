from entity import entity,being


class WordToken(entity):
    def __init__(self,words,token,is_punct=False):
        self.children=words
        self.token=token
        self.is_punct=is_punct

    def __getitem__(self,key):
        return self.children[key]
