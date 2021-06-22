from itertools import product


class Fixer:

    def __init__(self, language_model, tree):
        self.language_model = language_model
        self.tree = tree
    
    def fix(self, query):
        query = query.lower()
        query_variants = []
        for word in query.split():
            query_variants.append(self.tree.search(word))
        
        query_variants = product(*query_variants)
        result_variants = []
        for var in query_variants:
            var = ' '.join(var)
            prob = self.language_model.query_prob(var)
            result_variants.append((prob, var))
        
        result_variants.sort()
        return result_variants[0][1]
