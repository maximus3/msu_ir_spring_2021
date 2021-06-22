from collections import defaultdict
import json
import numpy as np
try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, *args, **kwargs: x
    
from utils import check_dir_or_create, word_clean, get_clean_words

class ErrorModel:

    def __init__(self):      
        self.stat = defaultdict(lambda: defaultdict(int))
        # {'orig' : {'fix' : P(orig|fix)}}
        self._stat_size = 0
    
    @staticmethod
    def make_bigrams(word):
        word = '^' + word + '_'
        bigrams = []
        for i in range(len(word) - 1):
            bigrams.append(word[i:i + 2])
        return bigrams
    
    @staticmethod
    def _levenshtein_matrix(a, b):
        n, m = len(a), len(b)
        need_transpose = False
        if n > m:
            a, b = b, a
            n, m = m, n
            need_transpose = True

        current = list(range(n + 1))
        previous = current
        lv_matrix = np.array([current])
        for i in range(1, m + 1):
            prev_previous, previous, current = previous, current, [i] + [0] * n
            for j in range(1, n + 1):
                a_ne_b = int(a[j - 1] != b[i - 1])
                add    = previous[j] + 1
                delete = current[j - 1] + 1
                change = previous[j - 1] + a_ne_b
                
                # transpose = change
                # if j > 1 and i > 1 and a[j - 2] == b[i - 1] and a[j - 1] == b[j - 2]:
                #     transpose = prev_previous[j - 2] + a_ne_b

                current[j] = min(add, delete, change)#, transpose)
            lv_matrix = np.vstack((lv_matrix, [current]))
        return lv_matrix.T if need_transpose else lv_matrix
    
    def _add_stats(self, orig, fix):
        self.stat[orig][fix] += 1
        self._stat_size += 1

    def _get_stats(self, orig, fix):
        if orig in self.stat and fit in self.stat[orig]:
            return self.stat[orig][fit]
        return 1.0 / self._stat_size
    
    def _fill_stats(self, a, b, lv_matrix):
        i, j = len(a), len(b)
        cur_distance = lv_matrix[len(b), len(a)]

        while cur_distance != 0:
            add = lv_matrix[j - 1, i] if j > 0 else np.inf
            delete = lv_matrix[j, i - 1] if i > 0 else np.inf
            change = lv_matrix[j - 1, i - 1] if j > 0 and i > 0 else np.inf

            operation = np.argmin([change, add, delete]).item()

            if operation == 0:
                i -= 1
                j -= 1
                if cur_distance != change:
                    cur_distance = change
                    self._add_stats(a[i], b[j])
                
            elif operation == 1:
                j -= 1
                if cur_distance != add:
                    cur_distance = add
                    self._add_stats(a[i - 1][1] + '~', b[j])
            else:
                i -= 1
                if cur_distance != delete:
                    cur_distance = delete
                    self._add_stats(a[i], b[j - 1][1] + '~')
    
    def normalize_stat(self):
        for orig in self.stat:
            for fix in self.stat[orig]:
                self.stat[orig][fix] /= self._stat_size
    
    def make_model(self, filename="queries_all.txt"):
        self.stat = defaultdict(lambda: defaultdict(int))
        self._stat_size = 0
        with open(filename, 'r') as f:
            if filename == 'queries_all.txt':
                tqdm_cur = lambda x: tqdm(x, total=2000000)
            else:
                tqdm_cur = tqdm
            for line in tqdm_cur(f):
                if '\t' not in line:
                    continue
                wrong, right = line.lower().split('\t')
                wrong = get_clean_words(wrong)
                right = get_clean_words(right)
                
                if len(wrong) != len(right):  # join or split
                    continue

                for wrong_word, right_word in zip(wrong, right):
                    wrong_bigrams = self.make_bigrams(wrong_word)
                    right_bigrams = self.make_bigrams(right_word)
                    lv_matrix = self._levenshtein_matrix(wrong_bigrams, right_bigrams)
                    self._fill_stats(wrong_bigrams, right_bigrams, lv_matrix)

        self.normalize_stat()
    
    def save_model(self, filename='stats.json', directory='prepared_data'):
        check_dir_or_create(directory)
        with open(directory + '/' + filename, 'w') as f:
            f.write(json.dumps((self._stat_size, self.stat)))
    
    def load_model(self, filename='stats.json', directory='prepared_data'):
        check_dir_or_create(directory)
        with open(directory + '/' + filename, 'r') as f:
            self._stat_size, self.stat = json.loads(f.read())
