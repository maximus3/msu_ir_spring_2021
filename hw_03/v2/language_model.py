import json
from collections import defaultdict

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda x, *args, **kwargs: x
   
from utils import check_dir_or_create, word_clean, get_clean_words

class LanguageModel:

    def __init__(self):
        self._init_by_saved_data()

    def _make_data_to_save(self):
        data = {
            'words': list(self.words),
            'unigram_words_count': self.unigram_words_count,
            'unigram_model': dict(self.unigram_model),
            'bigram_words_count': self.bigram_words_count,
            'bigram_model': dict(self.bigram_model),
        }
        return data
    
    def _init_by_saved_data(self, data=None):
        if data is None:
            self.words = set()
            self.unigram_words_count = 0
            self.unigram_model = defaultdict(int)
            # {'word': P(word)}

            self.bigram_words_count = 0
            self.bigram_model = defaultdict(lambda: defaultdict(int))
            # {'word_1': {'word_2': P(word_1|word_2)}}
            return
        
        self.words = set(data['words'])
        self.unigram_words_count = data['unigram_words_count']
        self.unigram_model = defaultdict(int, data['unigram_model'])
        self.bigram_words_count = data['bigram_words_count']
        self.bigram_model = defaultdict(lambda: defaultdict(int), data['bigram_model'])
    
    def normalize_stat(self):
        for word in self.unigram_model:
            self.unigram_model[word] /= self.unigram_words_count
        
        for word_1 in self.bigram_model:
            for word_2 in self.bigram_model[word_1]:
                self.bigram_model[word_1][word_2] /= self.bigram_words_count
    
    def make_model(self, filename="queries_all.txt"):
        self._init_by_saved_data()
        with open(filename, 'r') as f:
            if filename == 'queries_all.txt':
                tqdm_cur = lambda x: tqdm(x, total=2000000)
            else:
                tqdm_cur = tqdm
            for line in tqdm_cur(f):
                if '\t' not in line:
                    continue
                line = line.split('\t')[1].lower()

                words = get_clean_words(line)
                len_words = len(words)
                self.words.update(set(words))

                for i, word in enumerate(words):
                    self.unigram_words_count += 1
                    self.unigram_model[word] += 1

                    if i != len_words - 1:
                        self.bigram_words_count += 1
                        word_2 = words[i + 1]
                        self.bigram_model[word][word_2] += 1
        
        self.normalize_stat()
    
    def unigram_prob(self, word):
        if word in self.unigram_model:
            return self.unigram_model[word]
        return 1 / self.unigram_words_count
    
    def bigram_prob(self, word_1, word_2):
        if word_1 in self.bigram_model and word_2 in self.bigram_model[word_1]:
            return self.bigram_model[word_1][word_2]
        return 1 / self.bigram_words_count
    
    def query_prob(self, query):
        words = get_clean_words(query.lower())
        len_words = len(words)
        prob = 1
        for i, word in enumerate(words):
            if i != len_words - 1:
                word_2 = words[i + 1]
                prob *= 1 / self.bigram_prob(word, word_2)
            else:
                prob *= 1 / self.unigram_prob(word)
        return prob
    
    def predict_next_word(self, word, n=None):
        word = word.lower()
        if word not in self.bigram_model:
            return []
        all_words = list(self.bigram_model[word].items())
        all_words.sort(key=lambda x: x[1], reverse=True)
        result = [elem[0] for elem in all_words]
        if n:
            result = result[:n]
        return result
    
    def save_model(self, filename='language_model.json', directory='prepared_data'):
        check_dir_or_create(directory)
        data_to_save = self._make_data_to_save()
        with open(directory + '/' + filename, 'w') as f:
            f.write(json.dumps(data_to_save))
    
    def load_model(self, filename='language_model.json', directory='prepared_data'):
        check_dir_or_create(directory)
        with open(directory + '/' + filename, 'r') as f:
            data = json.loads(f.read())
        self._init_by_saved_data(data)
