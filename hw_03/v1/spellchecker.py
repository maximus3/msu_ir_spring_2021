import Levenshtein
from sys import stdin

def search_by_func(req, real_words, n=5, dist_func=Levenshtein.ratio, reverse=True):
    req = req.lower()
    best_dists = []
    for word in real_words:
        dist = dist_func(req, word)
        best_dists.append((dist, word))
        best_dists.sort(reverse=reverse)
        if len(best_dists) > n:
            best_dists.pop()
    return best_dists
    
def get_dict():
    words = set()

    with open('queries_all.txt', 'rt') as f:    
        file = f.read().split('\n')
        for line in file:
            if '\t' in line:
                pair = line.split('\t')
                words.update(pair[1].lower().split())

    return words


if __name__ == '__main__':
    real_words = get_dict()
    for req in stdin:
        req = req.split()
        ans = ''
        for word in req:
            word = search_by_func(word, real_words, n=1)[0][1]
            ans += word + ' '
        print(ans[:-1])
