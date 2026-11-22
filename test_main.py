import shutil
import pandas as pd
import tempfile
from collections import namedtuple
import os
from main import *


def test_convert_to_lowercase():
    preprocessor = Preprocessor()
    assert preprocessor.convert_to_lowercase("BANANA") == "banana"

def test_remove_consecutive_spaces():
    preprocessor = Preprocessor()
    assert preprocessor.remove_consecutive_spaces("Banana   Tomer") == "Banana Tomer"

def test_remove_punctuation():
    preprocessor = Preprocessor()
    assert preprocessor.remove_punctuation("Banana, Tomer!") == "Banana  Tomer "

def test_remove_unwanted_words():
    preprocessor = Preprocessor()
    temp_dir = tempfile.mkdtemp()
    try:
        remove_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        pd.DataFrame({"words": ["the", "a", "or", "and"]}).to_csv(remove_words_file, index=False)
        text = "the banana and tomer"
        result = preprocessor.remove_unwanted_words(text, remove_words_file)
        assert result == "banana tomer"
    finally:
        shutil.rmtree(temp_dir)

def test_process_text():
    preprocessor = Preprocessor()
    temp_dir = tempfile.mkdtemp()
    try:
        unwanted_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        pd.DataFrame({"words": ["the", "a", "or", "and"]}).to_csv(unwanted_words_file, index=False)
        text = "And banana! And the Tomer!"
        result = preprocessor.process_text(text, unwanted_words_file)
        assert result == "banana tomer"
    finally:
        shutil.rmtree(temp_dir)


def test_process_names():
    preprocessor = Preprocessor()
    temp_dir = tempfile.mkdtemp()
    try:
        names_file = os.path.join(temp_dir, "people_path.csv")
        unwanted_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        pd.DataFrame({"Name": ["Tomer Levi", "Banana Joe"], "Other Names": ["Tomatillo", "Banana King"]}).to_csv(names_file, index=False)
        pd.DataFrame({"words": ["the", "a", "or", "and"]}).to_csv(unwanted_words_file, index=False)
        result = preprocessor.process_names(names_file, unwanted_words_file)
        assert len(result) > 0
        assert result[0] == [["tomer", "levi"], [["tomatillo"]]]
    finally:
        shutil.rmtree(temp_dir)

def test_sequence_count_dict():
    sentences = [["banana", "tomer"], ["tomer", "fell", "banana"]]
    result = sequence_count_dict(sentences, 2)
    assert result == {1: {('banana',): 2, ('tomer',): 2, ('fell',): 1}, 2: {('banana', 'tomer'): 1, ('tomer', 'fell'): 1, ('fell', 'banana'): 1}}

def test_sort_counts_by_sequence():
    seq_count = {1: {('banana',): 2, ('tomer',): 2, ('fell',): 1}, 2: {('banana', 'tomer'): 1, ('tomer', 'fell'): 1, ('fell', 'banana'): 1}}
    result = sort_counts_by_sequence(seq_count)
    assert result == [['1_seq', [['banana', 2], ['fell', 1], ['tomer', 2]]], ['2_seq', [['banana tomer', 1], ['fell banana', 1], ['tomer fell', 1]]]]

def test_count_name_mentions():
    sentences = [["banana", "tomer"], ["tomer", "fell", "banana"]]
    names = [[["tomer levi"], ["tomatillo"]]]
    result = count_name_mentions(sentences, names)
    assert result == {'tomer levi': 2}


def test_init_empty_k_seqs_dict():
    preprocessor = Preprocessor()
    search_engine = SearchEngine(preprocessor)
    temp_dir = tempfile.mkdtemp()
    try:
        kseq_query_path = os.path.join(temp_dir, "kseq_query_path.csv")
        pd.DataFrame({"keys":[["banana", "tomer"], ["tomer", "fell", "banana"]]}).to_json(kseq_query_path)
        search_engine.init_empty_k_seqs_dict(kseq_query_path)
        result = search_engine.k_seqs_dict
        assert result == {('banana', 'tomer'): [], ('tomer', 'fell', 'banana'): []}
    finally:
        shutil.rmtree(temp_dir)

def test_create_k_seqs_dict():
    preprocessor = Preprocessor()
    search_engine = SearchEngine(preprocessor)
    temp_dir = tempfile.mkdtemp()
    try:
        sentence_file = os.path.join(temp_dir, "sentence_file.csv")
        remove_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        kseq_query_path = os.path.join(temp_dir, "kseq_query_path.csv")
        pd.DataFrame({"sentence":["banana tomer", "tomer fell banana"]}).to_csv(sentence_file, index=False)
        pd.DataFrame({"words": ["the", "a", "or", "and"]}).to_csv(remove_words_file, index=False)
        pd.DataFrame({"keys":[["banana"], ["tomer", "fell"]]}).to_json(kseq_query_path)
        search_engine.init_empty_k_seqs_dict(kseq_query_path)
        search_engine.create_k_seqs_dict(sentence_file, remove_words_file)
        result = search_engine.k_seqs_dict
        assert result == {('banana',): [['banana', 'tomer'], ['tomer', 'fell', 'banana']], ('tomer', 'fell'): [['tomer', 'fell', 'banana']]}
    finally:
        shutil.rmtree(temp_dir)

def test_create_names_nicknames():
    preprocessor = Preprocessor()
    people_context_analyzer = PeopleContextAnalyzer(preprocessor)
    temp_dir = tempfile.mkdtemp()
    try:
        names_file = os.path.join(temp_dir, "names.csv")
        remove_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        pd.DataFrame({"Name": ["Tomer Levi", "Banana Joe"], "Other Names": ["Tom", "Ban"]}).to_csv(names_file, index=False)
        pd.DataFrame({"words": ["the", "a", "or", "and"]}).to_csv(remove_words_file, index=False)
        people_context_analyzer.create_names_nicknames(names_file, remove_words_file)
        assert people_context_analyzer.names_and_nicknames == [[["tomer", "levi"], ["tom"]], [["banana", "joe"], ["ban"]]]
    finally:
        shutil.rmtree(temp_dir)

def test_create_processed_sentences():
    preprocessor = Preprocessor()
    people_context_analyzer = PeopleContextAnalyzer(preprocessor)
    temp_dir = tempfile.mkdtemp()
    try:
        sentence_file = os.path.join(temp_dir, "sentence_file.csv")
        remove_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        pd.DataFrame({"sentence": ["banana tomer", "tomer went to the tree"]}).to_csv(sentence_file, index=False)
        pd.DataFrame({"words": ["the", "a", "to", "and"]}).to_csv(remove_words_file, index=False)
        people_context_analyzer.create_processed_sentences(sentence_file, remove_words_file)
        assert people_context_analyzer.processed_sentences == [["banana", "tomer"], ["tomer", "went", "tree"]]
    finally:
        shutil.rmtree(temp_dir)

def test_generate_k_sequences():
    preprocessor = Preprocessor()
    people_context_analyzer = PeopleContextAnalyzer(preprocessor)
    temp_dir = tempfile.mkdtemp()
    try:
        sentence_file = os.path.join(temp_dir, "sentence_file.csv")
        remove_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        pd.DataFrame({"sentence": ["banana tomer", "tomer went to the tree"]}).to_csv(sentence_file, index=False)
        pd.DataFrame({"words": ["the", "a", "or", "and"]}).to_csv(remove_words_file, index=False)
        people_context_analyzer.create_processed_sentences(sentence_file, remove_words_file)
        people_context_analyzer.generate_k_sequences(2)
        result = people_context_analyzer.k_seqs_by_sentence
        assert result == [[['banana'], ['tomer'], ['banana', 'tomer']], [['tomer'], ['went'], ['to'], ['tree'], ['tomer', 'went'], ['went', 'to'], ['to', 'tree']]]
    finally:
        shutil.rmtree(temp_dir)

def test_find_mentions():
    preprocessor = Preprocessor()
    people_context_analyzer = PeopleContextAnalyzer(preprocessor)
    temp_dir = tempfile.mkdtemp()
    try:
        sentence_file = os.path.join(temp_dir, "sentence_file.csv")
        remove_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        names_file = os.path.join(temp_dir, "names.csv")
        pd.DataFrame({"sentence": ["banana tomer", "tomer went to the tree"]}).to_csv(sentence_file, index=False)
        pd.DataFrame({"words": ["the", "a", "or", "and"]}).to_csv(remove_words_file, index=False)
        pd.DataFrame({"Name": ["Tomer Levi", "Banana Joe"], "Other Names": ["Tom", "Ban"]}).to_csv(names_file, index=False)
        people_context_analyzer.create_names_nicknames(names_file, remove_words_file)
        people_context_analyzer.create_processed_sentences(sentence_file, remove_words_file)
        people_context_analyzer.generate_k_sequences(1)
        people_context_analyzer.find_mentions()
        result = people_context_analyzer.names_and_k_seqs
        assert result == [['banana joe', [['banana'], ['tomer']]], ['tomer levi', [['banana'], ['to'], ['tomer'], ['tree'], ['went']]]]
    finally:
        shutil.rmtree(temp_dir)

def test_create_name_map():
    preprocessor = Preprocessor()
    graph = ConnectionsGraph(threshold=1, window_size=2, preprocessor=preprocessor)
    temp_dir = tempfile.mkdtemp()
    try:
        names_file = os.path.join(temp_dir, "names.csv")
        unwanted_words_file = os.path.join(temp_dir, "REMOVEWORDS.csv")
        pd.DataFrame({"Name": ["Tomer Levi", "Banana Joe"], "Other Names": ["Tom", "Ban"]}).to_csv(names_file, index=False)
        pd.DataFrame({"words": ["the", "a", "or", "and"]}).to_csv(unwanted_words_file, index=False)
        graph.create_name_map(names_file, unwanted_words_file)
        assert ["tomer", "levi"] in graph.nicknames_map.values()
    finally:
        shutil.rmtree(temp_dir)

def test_find_mentions_in_window():
    preprocessor = Preprocessor()
    graph = ConnectionsGraph(threshold=1, window_size=2, preprocessor=preprocessor)
    try:
        sentences = ["banana", "peel", "tomer", "fell", "banana"]
        names = [["tomer", "levi"]]
        graph.main_names = names
        result = graph.find_mentions_in_window(sentences)
        assert result == {("tomer", "levi")}
    finally:
        pass

def test_count_pair_mentions():
    preprocessor = Preprocessor()
    graph = ConnectionsGraph(threshold=1, window_size=2, preprocessor=preprocessor)
    try:
        sentences = ["banana", "peel", "tomer", "fell", "banana"]
        names = [["tomer", "levi"], ["banana", "joe"]]
        graph.main_names = names
        graph.sentences = sentences
        graph.window_size = 3
        result = graph.count_pair_mentions()
        assert result == {(('banana', 'joe'), ('tomer', 'levi')): 2}
    finally:
        pass

def test_create_graph():
    preprocessor = Preprocessor()
    graph = ConnectionsGraph(threshold=1, window_size=2, preprocessor=preprocessor)
    try:
        sentences = ["banana", "peel", "tomer", "fell", "banana"]
        names = [["tomer", "levi"], ["banana", "joe"]]
        graph.main_names = names
        graph.sentences = sentences
        graph.window_size = 3
        edges = graph.build_graph()
        result = graph.graph
        assert edges ==[[['banana', 'joe'], ['tomer', 'levi']]]
        assert result == {'banana joe': {'tomer levi'}, 'tomer levi': {'banana joe'}}
    finally:
        pass
    
def test_search_for_neighbors():
    preprocessor = Preprocessor()
    graph = ConnectionsGraph(threshold=1, window_size=2, preprocessor=preprocessor)
    try:
        sentences = ["banana", "peel", "tomer", "fell", "banana"]
        names = [["tomer", "levi"], ["banana", "joe"]]
        graph.main_names = names
        graph.sentences = sentences
        graph.window_size = 3
        graph.build_graph()
        result = graph.search_for_neighbors("tomer levi", "tomer levi", 0)
        assert result == True
    finally:
        pass

def test_check_connections():
    preprocessor = Preprocessor()
    graph = ConnectionsGraph(threshold=1, window_size=2, preprocessor=preprocessor)
    try:
        sentences = ["banana", "peel", "tomer", "fell", "banana"]
        names = [["tomer", "levi"], ["banana", "joe"]]
        graph.main_names = names
        graph.sentences = sentences
        graph.window_size = 3
        graph.build_graph()
        pair_matches = [["tomer levi", "banana joe"]]
        result = graph.check_connections(pair_matches, 1)
        assert result == [['banana joe', 'tomer levi', True]]
    finally:
        pass

def test_search_for_neighbors_exact():
    preprocessor = Preprocessor()
    graph = ConnectionsGraph(threshold=1, window_size=2, preprocessor=preprocessor)
    try:
        sentences = ["banana", "peel", "tomer", "fell", "banana"]
        names = [["tomer", "levi"], ["banana", "joe"]]
        graph.main_names = names
        graph.sentences = sentences
        graph.window_size = 3
        graph.build_graph()
        result = graph.search_for_neighbors_exact("tomer levi", "banana joe", 10)
        assert result == False
    finally:
        pass

def test_check_connections_exact():
    preprocessor = Preprocessor()
    graph = ConnectionsGraph(threshold=1, window_size=2, preprocessor=preprocessor)
    try:
        sentences = ["banana", "peel", "tomer", "fell", "banana"]
        names = [["tomer", "levi"], ["banana", "joe"]]
        graph.main_names = names
        graph.sentences = sentences
        graph.window_size = 3
        graph.build_graph()
        pair_matches = [["tomer levi", "banana joe"]]
        result = graph.check_connections_exact(pair_matches, 10)
        assert result == [['banana joe', 'tomer levi', False]]
    finally:
        pass
