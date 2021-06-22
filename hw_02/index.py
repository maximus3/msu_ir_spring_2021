import os
import gzip
from collections import defaultdict
import json
from sys import argv


class JustCoder:

    def encode(self, data):
        return json.dumps(data).encode('utf-8')
    
    def decode(self, data):
        return json.loads(data.decode('utf-8'))


class Simple9Coder():

    codes = [
        0x00000000,
        0x10000000,
        0x20000000,
        0x30000000,
        0x40000000,
        0x50000000,
        0x60000000,
        0x70000000,
        0x80000000,
    ]

    codes_info = {
        codes[8]: [28, 1, 2**1 - 1],
        codes[7]: [14, 2, 2**2 - 1],
        codes[6]: [9, 3, 2**3 - 1],
        codes[5]: [7, 4, 2**4 - 1],
        codes[4]: [5, 5, 2**5 - 1],
        codes[3]: [4, 7, 2**7 - 1],
        codes[2]: [3, 9, 2**9 - 1],
        codes[1]: [2, 14, 2**14 - 1],
        codes[0]: [1, 28, 2**28 - 1],
    }
        
    def encode(self, data):
        curret_pos = 0        
        result = []
        data_size = len(data)

        while curret_pos < data_size:        
            for code, code_info in self.codes_info.items():
                count = code_info[0]
                shift = code_info[1]
                max_value = code_info[2]

                current_max_value = max(data[curret_pos:curret_pos + count])

                if current_max_value < max_value and curret_pos + count <= data_size:
                    tmp = data[curret_pos] | code
                    for i in range(count - 1):
                        tmp |= (data[curret_pos + i + 1] << (shift * (i + 1)))
                    
                    result.append(str(tmp))
                    curret_pos += count
                    break

        return ('\n'.join(result)).encode('utf-8')

    def decode(self, data):
        data = data.decode('utf-8')

        result = []
        for num in data.split():
            num = int(num)

            code = num & 0xf0000000
            code_info = self.codes_info[code]
            num = num & 0x0fffffff

            count = code_info[0]
            shift = code_info[1]
            mask = code_info[2]

            for i in range(count):
                result.append(num & mask)            
                num >>= shift

        return result


def save_data(reversed_index, docID_to_url, url_to_docID, word_to_ID, StringCoder=JustCoder, IntCoder=Simple9Coder, dirname='load_data'):
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    string_coder = StringCoder()
    int_coder = IntCoder()

    with gzip.open(f"{dirname}/docID_to_url.dump.gz", "w") as f:
        f.write(string_coder.encode(docID_to_url))
    with gzip.open(f"{dirname}/url_to_docID.dump.gz", "w") as f:
        f.write(string_coder.encode(url_to_docID))
    with gzip.open(f"{dirname}/word_to_ID.dump.gz", "w") as f:
        f.write(string_coder.encode(word_to_ID))

    
    prepared_index = []
    for key, value in reversed_index.items():
        batch = [key] + [len(value)] + value
        prepared_index.extend(batch)

    with gzip.open(f"{dirname}/reversed_index.dump.gz", "w") as f:
        f.write(int_coder.encode(prepared_index))


def load_data(StringCoder=JustCoder, IntCoder=Simple9Coder, dirname='load_data'):
    string_coder = StringCoder()
    int_coder = IntCoder()

    with gzip.open(f"{dirname}/docID_to_url.dump.gz", "r") as f:
        data = string_coder.decode(f.read())
        docID_to_url = {int(key) : value for key, value in data.items()}
    with gzip.open(f"{dirname}/url_to_docID.dump.gz", "r") as f:
        data = string_coder.decode(f.read())
        url_to_docID = {key : int(value) for key, value in data.items()}
    with gzip.open(f"{dirname}/word_to_ID.dump.gz", "r") as f:
        data = string_coder.decode(f.read())
        word_to_ID = {key : int(value) for key, value in data.items()}

    with gzip.open(f"{dirname}/reversed_index.dump.gz", "r") as f:
        prepared_index = int_coder.decode(f.read())

    state  = 0
    reversed_index = defaultdict(list)

    for elem in prepared_index:
        if state == 0:
            key = elem
            state = 1
        elif state == 1:
            data_size = elem
            current_data = []
            state = 2
        elif state == 2:
            current_data.append(elem)
            if len(current_data) == data_size:
                state = 0 
                reversed_index[key] = current_data
                current_data = []
    
    return reversed_index, docID_to_url, url_to_docID, word_to_ID


def check_save_data(reversed_index, docID_to_url, url_to_docID, word_to_ID):
    save_data(reversed_index, docID_to_url, url_to_docID, word_to_ID)

    new_reversed_index, new_docID_to_url, new_url_to_docID, new_word_to_ID = load_data()

    assert new_reversed_index == reversed_index
    assert new_docID_to_url == docID_to_url
    assert new_url_to_docID == url_to_docID
    assert new_word_to_ID == word_to_ID

    print("Tests OK")


def index_sh(dirname, test=False):
    dumps = os.listdir(dirname)

    dirty_words = ""
    for filename in dumps:
        with gzip.open(dirname + filename) as f:
            dirty_words += f.read().decode("utf-8", errors="ignore").lower() + ' '
    
    clean_words = ""
    for i, c in enumerate(dirty_words):
        if ord(c) > 32:
            clean_words += c
        else:
            clean_words += ' '
    clean_words = clean_words.split()

    words_set = set(clean_words) # Set of all words
    one_site = []
    sites_index = {} # site - site's content
    for word in clean_words:
        if 'http://lenta.ru/' in word:
            if len(one_site) > 3:
                adr = one_site[0]
                while adr[:4] != 'http':
                    adr = adr[1:]
                sites_index[adr] = one_site[1:]
                words_set.remove(one_site[0])
            one_site = []
        one_site.append(word)

    word_to_ID = {word: i for i, word in enumerate(words_set)} # word - wordID
    url_to_docID = {url: i for i, url in enumerate(sites_index.keys())} # site's url - docID
    docID_to_url = {i: url for i, url in enumerate(sites_index.keys())} # docID - site's url
    reversed_index = defaultdict(list) # wordID - docID

    for i, (url, words) in enumerate(sites_index.items()):
        for word in words:
            reversed_index[word_to_ID[word]].append(url_to_docID[url])
    
    if test:
        check_save_data(reversed_index, docID_to_url, url_to_docID, word_to_ID)
    
    return reversed_index, docID_to_url, url_to_docID, word_to_ID


if __name__ == '__main__':
    dirname = argv[1] if len(argv) > 1 else 'dumps/'
    if dirname[-1] != '/':
        dirname += '/'
    print("Making index...")
    reversed_index, docID_to_url, url_to_docID, word_to_ID = index_sh(dirname)
    print("Index done, saving...")
    save_data(reversed_index, docID_to_url, url_to_docID, word_to_ID)
    print("Saved")
    
