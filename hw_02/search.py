from sys import stdin
from index import *

class NodeTree:

    def __init__(self, op_type, op, *nodes):
        """
        Parameters
        ----------
        op : string
            Operand or operation
        op_type : {'O', 'B', 'U'}
            O - Operand
            U - Unary operation
            B - Binary operation
        nodes : list
            List of nodes for operand
        """
        self.op = op
        self.op_type = op_type
        if self.op_type == 'O':
            self.cur = 0
            self.docs = reversed_index[op]
        else:
            self.nodes = nodes
    
    def run(self, docID):
        if self.op_type == 'O':
            while self.cur < len(self.docs) and docID > self.docs[self.cur]:
                self.cur += 1
            if self.cur == len(self.docs):
                return float("inf")
            return self.docs[self.cur]

        elif self.op_type == 'B':
            res1 = self.nodes[0].run(docID)
            res2 = self.nodes[1].run(docID)
            if self.op == '&':
                return max(res1, res2)
            elif self.op == '|':
                return min(res1, res2)
            else:
                raise "Unknown binary operand"

        elif self.op_type == 'U':
            res = self.nodes[0].run(docID)
            if res == docID:
                return res + 1
            else:
                return docID
        
        else:
            raise RuntimeError(f"Unknown operand: {self.op}, {self.op_type}")


class QueryTree:

    OP = {'&', '|', '!'}

    def __init__(self, query):
        self.max_docID = max(url_to_docID.values())
        self.query = self.get_pref_not(self, query)
        self.head = self.make_tree(self, self.query)

    @staticmethod
    def get_tokens(cls, query):
        tokens = []
        buffer = ""
        for ch in query.lower():
            if ch.isalpha():
                buffer += ch
                continue
            if buffer:
                tokens.append(buffer)
            buffer = ''
            if not ch.isspace():
                tokens.append(ch)
        if buffer:
            tokens.append(buffer)
        return tokens
    
    @staticmethod
    def get_pref_not(cls, query):
        tokens = cls.get_tokens(cls, query)
        notation = []
        stack = []
        priority = {'!' : 4, '&' : 3, '|' : 2, '(' : 1}

        for token in tokens:
            if token == '(':
                stack.append(token)
            elif token == ')':
                while stack[-1] != '(':
                    notation.append(stack.pop())
                stack.pop()
            elif token in cls.OP:
                while len(stack) > 0 and priority[stack[-1]] >= priority[token]:
                    notation.append(stack.pop()) 
                stack.append(token)
            else:
                notation.append(token)
        
        notation.extend(stack[::-1])

        return notation
    
    @staticmethod
    def make_tree(cls, query):
        stack = []
        for token in query:
            if token == '!':
                node = NodeTree('U', '!', stack.pop())
            elif token in cls.OP:
                node = NodeTree('B', token, stack.pop(), stack.pop())
            else:
                node = NodeTree('O', word_to_ID[token])
            stack.append(node)
        return stack[0]
        
    def search(self):
        docID = -1
        documents = []
        while docID <= self.max_docID:
            foundID = self.head.run(docID)
            if foundID == docID:
                if docID != -1:
                    documents.append(docID_to_url[docID])
                docID += 1
            else:
                docID = foundID
        return documents


def search_sh(query):
    tree = QueryTree(query)
    documents = tree.search()
    
    return documents


if __name__ == '__main__':
    reversed_index, docID_to_url, url_to_docID, word_to_ID = load_data()
    for query in stdin:
        query = query.strip()
        documents = search_sh(query)
        print(query)
        print(len(documents))
        if len(documents):
            print(*documents, sep='\n')
        print()
