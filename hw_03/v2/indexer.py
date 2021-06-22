from error_model import ErrorModel
from language_model import LanguageModel
from search_tree import SearchTree

if __name__ == '__main__':
    error_model = ErrorModel()
    error_model.make_model()
    error_model.save_model()
    print('Error model saved')
    
    language_model = LanguageModel()
    language_model.make_model()
    language_model.save_model()
    print('Language model saved')
    
    tree = SearchTree(error_model, language_model.words)
    tree.save_model()
    print('Search Tree saved')
