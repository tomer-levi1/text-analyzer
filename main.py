import json
import argparse
import pandas as pd
import re
from typing import *

"""Task1"""

class Preprocessor:
    def __init__(self):
        pass

    def convert_to_lowercase(self, text: str) -> str:
        """Converts text to lowercase"""
        return text.lower()
    
    def remove_punctuation(self, text: str) -> str:
        """Removes punctuation from text"""
        return re.sub(r"[^\w\s]", " ", text) #^ is for negation, \w is for word characters, \s is for whitespace characters

    def remove_unwanted_words(self, text: str, unwanted_words_file: Optional[str]) -> str:
        """Removes unwanted words from text"""
        if unwanted_words_file is None:
            return text
        try:
            unwanted_words = pd.read_csv(unwanted_words_file)
            unwanted_words = unwanted_words["words"].values
            return " ".join([word for word in text.split() if word not in unwanted_words])
        except FileNotFoundError:
            print("Invalid input")
            return text
    
    def remove_consecutive_spaces(self, text: str) -> str:
        """Removes consecutive spaces from text"""
        return re.sub(r"\s+", " ", text) #'s' is for whitespace characters, + is for one or more

    def remove_whitespace_suffix_and_prefix(self, text: str) -> str:
        """Removes whitespace suffix and prefix from text"""
        return text.strip()
    
    def process_text(self, text: str, unwanted_words_file: str) -> Optional[str]:
        """Processes text"""
        text = self.convert_to_lowercase(text) 
        text = self.remove_punctuation(text) 
        text = self.remove_unwanted_words(text, unwanted_words_file) 
        text = self.remove_consecutive_spaces(text)
        text = self.remove_whitespace_suffix_and_prefix(text)
        return text if text else None
    
    def load_name_list(self, name_list_file: str) -> Set[str]:
        """Loads name list"""
        try:
            name_list = pd.read_csv(name_list_file)
            return set(name_list["names"].values) #This assumes that the name list file has a column named "names", and returns a set of names
        except:
            print("Invalid input")
        return #Return an empty set if the input is invalid
    
    def process_sentences(self, sentences: List[str], unwanted_words_file: str) -> List[List[str]]:
        """Preprocesses and splits sentences into words"""
        cleaned_sentences = []
        for sentence in sentences:
            cleaned_sentence = self.process_text(sentence, unwanted_words_file)
            if cleaned_sentence:  #Only keep non-empty sentences
                cleaned_sentences.append(self.split_sentences_into_words(cleaned_sentence))
        return cleaned_sentences
    
    def split_sentences_into_words(self, text: str) -> List[str]:
        """Splits sentences into words"""
        return text.split()
        
    def process_single_name(self, name: str, unwanted_words_file: str) -> List[str]:
        """Processes a single name"""
        if pd.isna(name): #Check if the name is missing
            name = ""
        name = name.strip().lower()
        name = re.sub(r"[^\w\s]", " ", name) #Remove punctuation
        name = self.remove_unwanted_words(name, unwanted_words_file)
        name = [word for word in name.split() if word] #Split the name into word list
        return name
    
    def process_names(self, name_input_path: str, unwanted_words_file: str) -> List[List[List[str]]]:
        """Processes names and their other names from the names file"""
        try:
            all_name_list = pd.read_csv(name_input_path)
        except Exception:
            print("Invalid input")
            exit()
        output_name_list = []
        for _, person in all_name_list.iterrows(): #Use iterrows to get the person's name and aliases
            regular_name = self.process_single_name(person.get("Name", ""), unwanted_words_file) #Process the regular name
            other_names_raw = person.get("Other Names", "") #Get the other names
            if pd.notna(other_names_raw) and other_names_raw: 
                other_names = [name for name in other_names_raw.split(',')] #Split the other names by comma
                other_names = [self.process_single_name(name, unwanted_words_file) for name in other_names] 
                other_names = [name for name in other_names if name]
            else:
                other_names = []
            output_name_list.append([regular_name] + [other_names])
        return output_name_list
    
"""Task2"""

def sequence_count_dict(sentences: str, N: int) -> Dict[int, Dict[Tuple[str], int]]:
    """Creates a dictionary of sequences of length 1 to N and how many times they appear"""
    if N < 1:
        return {}
    N_sequence_count = {i: {} for i in range(1, N + 1)} #Create a dictionary for each number up to N
    for sentence in sentences:
        for i in range(len(sentence)):
            for j in range(1, N + 1):
                if i + j > len(sentence): #i + j is the end of the sequence, it can't be outside the sentence
                    continue
                curr_sequence = tuple(sentence[i:i + j]) #Create a tuple of the sequence
                if curr_sequence in N_sequence_count[j]: #N_sequence_count[j] is for sequences of length j
                    N_sequence_count[j][curr_sequence] += 1 
                else:
                    N_sequence_count[j][curr_sequence] = 1
    return N_sequence_count

def sort_counts_by_sequence(sequence_count: Dict[int, Dict[Tuple[str], int]]) -> List[List[str]]:
    """Formats the sequence count dictionary as a list of lists, sorted lexicographically"""
    ordered_sequences = []
    for n, counts_dict in sequence_count.items(): #Go over each sequence length
        sorted_counts = [] 
        for seq, count in counts_dict.items(): #Go over each sequence and count 
            seq_str = " ".join(seq)
            sorted_counts.append([seq_str, count]) #Add the sequence and count to the list
        sorted_counts = sorted(sorted_counts) 
        ordered_sequences.append([f"{n}_seq", sorted_counts]) 
    return ordered_sequences

"""Task3"""

def count_name_mentions(sentences: List[List[str]], names: List[List[List[str]]]) -> Dict[str, int]:
    """Counts the number of times a person's name is mentioned in the sentences"""
    name_counts = {}
    for name_nickname_list in names:
        original_name = " ".join(name_nickname_list[0]) #Keep the main name
        all_names = [str(nickname) for nickname in name_nickname_list[1:]] #Add all nicknames
        all_names.extend(original_name.split()) #Add the main name to the list of names and nicknames
        count = 0
        for sentence in sentences: 
            for word in sentence:
                if any(name in word for name in all_names): #Check if any of the names or nicknames are the current word
                    count += 1
        if count > 0:
            name_counts[original_name] = count #Add the count to the dictionary, at the key of the main name
    return name_counts

"""Task4"""

class SearchEngine:
    def __init__(self, preprocessor: Preprocessor):
        self.k_seqs_dict = {}
        self.preprocessor = preprocessor

    def init_empty_k_seqs_dict(self, kseq_query_path: str) -> None:
        """Load k-seqs from JSON file and store in dictionary, with empty list as value"""
        try:
            data = pd.read_json(kseq_query_path)["keys"]
        except Exception:
            print("Invalid input")
            exit()
        all_k_seqs = []
        for k_seq in data:
                all_k_seqs.append(tuple(k_seq))
        self.k_seqs_dict = {k_seq: [] for k_seq in all_k_seqs}

    def create_k_seqs_dict(self, sentences_file: str, remove_words: str) -> None:
        """
        Process sentences and store matches in k_seqs_dict, with k-seq as keys,
        and list of unique matching sentences as values.
        We get O(1) lookup time for k-seqs by storing them as keys in a dictionary.
        """
        try:
            sentences = pd.read_csv(sentences_file)["sentence"].values
        except Exception:
            print("Invalid input")
            exit()
        for sentence in sentences:
            processed_sentences = self.preprocessor.process_text(sentence, remove_words)
            if not processed_sentences:
                continue
            words = processed_sentences.split()
            processed_sentences_set = set()  #Use a set to keep track of k_seq matches for this sentence
            for k_seq in self.k_seqs_dict.keys():
                for i in range(1, len(k_seq) + 1):  #Try all lengths of k_seq
                    for j in range(len(words) - i + 1):
                        curr_k_seq = tuple(words[j:j + i])  #Create a tuple of the current k_seq
                        if curr_k_seq in self.k_seqs_dict:  #Check if this is one of the k-sequences we're tracking
                            if curr_k_seq not in processed_sentences_set:
                                self.k_seqs_dict[curr_k_seq].append(words)  #Add the sentence (list of words) to the matches
                                processed_sentences_set.add(curr_k_seq)  #Add the k_seq to the set so we don't add the same sentence again
                                
    def create_k_seqs_preprocessed(self, sentences: List[List[str]]) -> None:
        """This is the same as the previous function, but it takes a list of preprocessed sentences"""
        for sentence in sentences:
            processed_sentences_set = set() #Keep track of processed sentences for each k_seq
            for k_seq in self.k_seqs_dict.keys():
                for i in range(1, len(k_seq) + 1): #Try all lengths of k_seq
                    for j in range(len(sentence) - i + 1):
                        curr_k_seq = tuple(sentence[j:j + i]) #Create a tuple of the current k_seq, because we use it as dict keys
                        if curr_k_seq in self.k_seqs_dict: #Only add if we haven't added this sentence for this k_seq
                            if curr_k_seq not in processed_sentences_set:
                                self.k_seqs_dict[curr_k_seq].append(sentence) #Add the sentence to the list of matches
                                processed_sentences_set.add(curr_k_seq) #True so we don't add the same sentence again
    
    def sort_matches_for_results(self) -> List[List[str]]:
        """Return list of k-seqs with sorted matches"""
        results = []
        for k_seq, matches in self.k_seqs_dict.items():
            if matches:
                results.append([" ".join(k_seq), sorted(matches)])
        return results

"""Task5"""

class PeopleContextAnalyzer:
    def __init__(self, preprocessor: Preprocessor):
        self.preprocessor = preprocessor
        self.names_and_nicknames = []
        self.processed_sentences = []
        self.k_seqs_by_sentence = []
        self.names_and_k_seqs = []

    def process_name_to_string(self, name_parts: List[str]) -> str:
        """Helper method to convert name parts to a single string"""
        return " ".join(name_parts)

    def create_names_nicknames(self, names_file: str, unwanted_words_file: str) -> None:
        """Process names into main name and nicknames, and store in names_and_nicknames"""
        try:
            processed_names = self.preprocessor.process_names(names_file, unwanted_words_file)
        except Exception:
            print("Invalid input")
            exit()
        self.names_and_nicknames = []
        for name in processed_names:
            main_name = name[0]
            nicknames = name[1]
            self.names_and_nicknames.append([main_name] + nicknames)
        
    def create_names_nicknames_preprocessed(self, names: List[List[List[str]]]) -> None:
        """This is the same as the previous function, but it takes a list of preprocessed names"""
        self.names_and_nicknames = []
        for name in names:
            main_name = name[0]
            nicknames = name[1]
            self.names_and_nicknames.append([main_name] + nicknames)

    def create_processed_sentences(self, sentences_file: str, unwanted_words_file: str):
        """Process sentences and store them in processed_sentences"""
        try:
            sentences = pd.read_csv(sentences_file)["sentence"].values
        except Exception:
            print("Invalid input")
            exit()
        self.processed_sentences = []
        for sentence in sentences:
            cleaned_sentence = self.preprocessor.process_text(sentence, unwanted_words_file)
            if cleaned_sentence:
                words = self.preprocessor.split_sentences_into_words(cleaned_sentence)
                self.processed_sentences.append(words) 
    
    def create_processed_sentences_preprocessed(self, sentences: List[List[str]]) -> None:
        """This is the same as the previous function, but it takes a list of preprocessed sentences"""
        self.processed_sentences = sentences

    def generate_k_sequences(self, maxk: int) -> None:
        """Generate k-sequences for each sentence and store them in k_seqs_by_sentence"""
        self.k_seqs_by_sentence = []
        for sentence in self.processed_sentences:
            if maxk < 1:
                print("Invalid input")
                exit()
            k_seqs = [
                sentence[i:i + k]
                for k in range(1, maxk + 1)
                for i in range(len(sentence) - k + 1)
            ]
            self.k_seqs_by_sentence.append(k_seqs)

    def find_mentions(self) -> List[List[str]]:
        """Find mentions of people in sentences, and store the k-seq in names_and_k_seqs
        First, we iterate over each person and their nicknames, and check if they are mentioned in the sentence
        then, if the person was mentioned in the sentence, we add to the main name all unique k-seqs from that sentence"""
        self.names_and_k_seqs = [] #List to store all names AND the sequences they are mentioned in
        for person in self.names_and_nicknames:
            main_name = self.process_name_to_string(person[0])
            nicknames = [self.process_name_to_string(nickname) for nickname in person[1:]]
            all_names = [main_name] + nicknames #Add the main name and nicknames to the list of all names
            person_k_seqs = []
            mentioned = False
            for sent_idx, sentence in enumerate(self.processed_sentences): #Use enumerate to keep the index of the sentence and use the k-seqs of it
                for name in all_names:
                    if name == main_name: #If the name is the main name, check any part of it
                        name_parts = name.split()
                        if any(part in sentence for part in name_parts):
                            mentioned = True
                            person_k_seqs.extend(self.k_seqs_by_sentence[sent_idx])
                    else: #If the name is a nickname, check the whole thing
                        if name in " ".join(sentence):
                            mentioned = True
                            person_k_seqs.extend(self.k_seqs_by_sentence[sent_idx])  
            #NOW, only if the person was mentioned, we know for which sentence, and we get all the k-seqs          
            if mentioned:
                unique_sequences = set() #Use a set so seqs don't repeat
                unique_seqs = [] #Use a list for the output and for sorting
                for seq in person_k_seqs:
                    seq_str = " ".join(seq)
                    if seq_str not in unique_sequences:
                        unique_sequences.add(seq_str)
                        unique_seqs.append(seq)
                unique_seqs = sorted(unique_seqs)
                self.names_and_k_seqs.append([main_name, unique_seqs])
        self.names_and_k_seqs = sorted(self.names_and_k_seqs)
        return self.names_and_k_seqs

"""Task6"""

class ConnectionsGraph:
    """Class to build a graph of connections between people based on mentions in sentences"""
    def __init__(self, threshold: int, window_size: int, preprocessor: Preprocessor):
        """Initialize the graph with a threshold and window size,
        and store the preprocessor, main names, nicknames map, sentences, and graph
        because we want to use the its properties in different functions"""
        self.preprocessor = preprocessor
        if threshold < 1:
            print("Invalid input")
            exit()
        self.threshold = threshold
        self.window_size = window_size
        self.main_names = [] #List to store the main names
        self.nicknames_map = {} #Mapping from each nickname to the main name
        self.sentences = [] #List to store the sentences
        self.graph = {} #Dictionary to store the graph connections

    def create_name_map(self, names_file: str, unwanted_words_file: str) -> None:
        """Process names and build nickname mapping so every person's main name is mapped to their nicknames"""
        try:
            processed_names = self.preprocessor.process_names(names_file, unwanted_words_file)
        except Exception:
            print("Invalid input")
            exit()
        for person in processed_names:
            main_name = person[0]
            other_names = person[1]
            self.main_names.append(main_name)
            all_names = set(main_name)
            for nickname in other_names:
                nickname = " ".join(nickname)
                nickname = (nickname,)
                all_names.update(nickname)
            for name in all_names:
                self.nicknames_map[name] = main_name
    
    def create_name_map_preprocessed(self, names: List[List[List[str]]]) -> None:
        """This is the same as the previous function, but it takes a list of preprocessed names"""
        for person in names:
            main_name = person[0]
            other_names = person[1]
            self.main_names.append(main_name)
            all_names = set(main_name)
            for nickname in other_names:
                nickname = " ".join(nickname)
                nickname = (nickname,)
                all_names.update(nickname)
            for name in all_names:
                self.nicknames_map[name] = main_name

    def make_sentence_list(self, sentences_file: str, unwanted_words_file: str) -> None:
        """Eventually, we want to process the sentences and store them in the self.sentences list"""
        try:
            sentences = pd.read_csv(sentences_file)["sentence"].values
        except Exception:
            print("Invalid input")
            exit()
        processed_sentences = self.preprocessor.process_sentences(sentences, unwanted_words_file)
        self.sentences = [" ".join(sentence) for sentence in processed_sentences]

    def make_sentence_list_preprocessed(self, sentences: List[List[str]]) -> None:
        """This is the same as the previous function, but it takes a list of preprocessed sentences"""
        self.sentences = [" ".join(sentence) for sentence in sentences]

    def find_mentions_in_window(self, window_words: List[str]) -> Set[Tuple[str, ...]]:
        """Find mentions of people in a given window of words"""
        mentioned = set()
        for main_name in self.main_names:
            for name_part in main_name:
                if name_part in window_words:
                    mentioned.add(tuple(main_name))
                    break
        for nickname in self.nicknames_map:
            if nickname in window_words:
                main_name = self.nicknames_map[nickname]
                mentioned.add(tuple(main_name))
        return mentioned

    def count_pair_mentions(self) -> Dict[Tuple[Tuple[str, ...], Tuple[str, ...]], int]:
        """Count how many mentions of two people within windows"""
        pair_counts = {}
        if len(self.sentences) < self.window_size:
            print("Invalid input")
            exit()
        for i in range(len(self.sentences) - self.window_size + 1):
            window = self.sentences[i: i + self.window_size]
            window_text = " ".join(window) #Join the window into a single string
            window_words = window_text.split() #Split the window into words to use list functions
            mentioned = self.find_mentions_in_window(window_words)
            mentioned = sorted(mentioned)
            for i in range(len(mentioned)): 
                for j in range(i + 1, len(mentioned)):
                    person1, person2 = mentioned[i], mentioned[j] 
                    key = (person1, person2) 
                    pair_counts[key] = pair_counts.get(key, 0) + 1
        return pair_counts

    def build_graph(self) -> List[List[List[str]]]:
        """Build graph of connections between people that meet the threshold.
        We update the self.graph as a dictionary where each person is a key and the value is a set of people they are connected to
        but we return the edges as a list of lists for the output"""
        try:
            pair_counts = self.count_pair_mentions()
            edges = []
            self.graph = {}
            for (person1, person2), count in pair_counts.items():
                if count >= self.threshold:
                    edges.append([list(person1), list(person2)])
                    person1_name = " ".join(person1)
                    person2_name = " ".join(person2)
                    if person1_name not in self.graph:
                        self.graph[person1_name] = set()
                    if person2_name not in self.graph:
                        self.graph[person2_name] = set()
                    self.graph[person1_name].add(person2_name)
                    self.graph[person2_name].add(person1_name)
            return sorted(edges)
        except Exception:
            print("Invalid input")
            exit()

    """Task7"""

    def search_for_neighbors(self, person1: str, person2: str, max_depth: int) -> bool:
        """Search if a path exists between two people given a maximum depth"""
        if max_depth < 0:
            print("Invalid input")
            exit()
        if person1 not in self.graph or person2 not in self.graph:
            return False
        people_to_check = [(person1, 0)] #List of people to check, with the depth so we don't pass the max
        visited = set()
        while people_to_check:
            curr_person, curr_depth = people_to_check.pop(0) 
            if curr_depth > max_depth:
                return False
            if curr_person == person2:
                return True
            if curr_person not in visited:
                visited.add(curr_person)
                for neighbor in self.graph[curr_person]:
                    if neighbor not in visited:
                        people_to_check.append((neighbor, curr_depth + 1))
        return False

    def check_connections(self, pair_matches: List[List[str]], max_depth: int) -> List[List]:
        """Check if pairs are connected by a path, add them to a list"""
        results = []
        for pair in pair_matches:
            name1, name2 = pair
            results.append(sorted([name1, name2]) + [self.search_for_neighbors(name1, name2, max_depth)]) #Add the pair and if they are connected to the results
        return sorted(results) 
    
    """Task8"""

    def search_for_neighbors_exact(self, person1: str, person2: str, exact_depth: int) -> bool:
        """Search for a path between two people with an exact depth, use the same logic from task 7
        but now check if the depth is the same as the given"""
        if exact_depth < 0:
            print("Invalid input")
            exit()
        if person1 not in self.graph or person2 not in self.graph:
            return False
        people_to_check = [(person1, 0)]
        visited = set()
        while people_to_check:
            person, depth = people_to_check.pop(0)
            if depth > exact_depth:
                return False
            if person == person2 and depth == exact_depth - 1:
                return True
            if person not in visited:
                visited.add(person)
                for neighbor in self.graph[person]:
                    if neighbor not in visited:
                        people_to_check.append((neighbor, depth + 1))
        return False

    def check_connections_exact(self, pair_matches: List[List[str]], exact_depth: int) -> List[List]:
        """Check if pairs are connected at exactly the given depth"""
        results = []
        for pair in pair_matches:
            name1, name2 = pair
            results.append(sorted([name1, name2]) + [self.search_for_neighbors_exact(name1, name2, exact_depth)])
        return sorted(results)

def read_args(args=None):
    parser = argparse.ArgumentParser(prog='Text Analyzer project')
    
    # General arguments
    parser.add_argument('-t', '--task', type=int,
                        help="Task number")
    parser.add_argument('-s', '--sentences',
                        help="Sentence file path")
    parser.add_argument('-n', '--names',
                        help="Names file path")
    parser.add_argument('-r', '--removewords',
                        help="Words to remove file path")
    parser.add_argument('-p', '--preprocessed',
                        help="JSON file with preprocessed data")
    
    # Task-specific arguments
    parser.add_argument('--maxk', type=int,
                        help="Max k for sequences")
    parser.add_argument('--fixed_length', type=int,
                        help="Fixed length to find")
    parser.add_argument('--windowsize', type=int,
                        help="Window size")
    parser.add_argument('--pairs',
                        help="JSON file with list of pairs")
    parser.add_argument('--threshold', type=int,
                        help="Graph connection threshold")
    parser.add_argument('--maximal_distance', type=int,
                        help="Maximal distance between nodes in graph")
    parser.add_argument('--qsek_query_path',
                        help="JSON file with query path")

    return parser.parse_args(args)

def handle_q1(args):
    preprocessor = Preprocessor()
    sentences = pd.read_csv(args.sentences)["sentence"].values
    cleaned_sentences = preprocessor.process_sentences(sentences, args.removewords)
    processed_names = preprocessor.process_names(args.names, args.removewords)
    
    return {"Processed Sentences": cleaned_sentences,
            "Processed Names": processed_names}

def handle_q2(args):
    if args.preprocessed:
        preprocessed_data = json.load(open(args.preprocessed))
        processed_sentences = preprocessed_data["Question 1"]["Processed Sentences"]
        n_seq_counts = sequence_count_dict(processed_sentences, args.maxk)
        formatted_counts = sort_counts_by_sequence(n_seq_counts)
        return {f"{args.maxk}-Seq Counts": formatted_counts}
    preprocessor = Preprocessor()
    sentences = pd.read_csv(args.sentences)["sentence"].values
    cleaned_sentences = preprocessor.process_sentences(sentences, args.removewords)
    n_seq_counts = sequence_count_dict(cleaned_sentences, args.maxk)
    formatted_counts = sort_counts_by_sequence(n_seq_counts)
    
    return {f"{args.maxk}-Seq Counts": formatted_counts}

def handle_q3(args):
    if args.preprocessed:
        preprocessed_data = json.load(open(args.preprocessed))
        processed_sentences = preprocessed_data["Question 1"]["Processed Sentences"]
        processed_names = preprocessed_data["Question 1"]["Processed Names"]
        name_counts = count_name_mentions(processed_sentences, processed_names)
        formatted_counts = sorted([(name, count) for name, count in name_counts.items()])
        return {"Name Mentions": formatted_counts}
    preprocessor = Preprocessor()
    sentences = pd.read_csv(args.sentences)["sentence"].values
    cleaned_sentences = preprocessor.process_sentences(sentences, args.removewords)
    processed_names = preprocessor.process_names(args.names, args.removewords)
    name_counts = count_name_mentions(cleaned_sentences, processed_names)
    formatted_counts = sorted([(name, count) for name, count in name_counts.items()])
    
    return {"Name Mentions": formatted_counts}

def handle_q4(args):
    preprocessor = Preprocessor()
    search_engine = SearchEngine(preprocessor)
    if args.preprocessed:
        preprocessed_data = json.load(open(args.preprocessed))
        processed_sentences = preprocessed_data["Question 1"]["Processed Sentences"]
        search_engine.init_empty_k_seqs_dict(args.qsek_query_path)
        search_engine.create_k_seqs_preprocessed(processed_sentences)
        results = search_engine.sort_matches_for_results()
        sorted_results = sorted(results)
        return {"K-Seq Matches": sorted_results}
    search_engine.removewords = args.removewords
    search_engine.init_empty_k_seqs_dict(args.qsek_query_path)
    search_engine.create_k_seqs_dict(args.sentences, args.removewords)
    results = search_engine.sort_matches_for_results()
    sorted_results = sorted(results)
    
    return {"K-Seq Matches": sorted_results}

def handle_q5(args):
    preprocessor = Preprocessor()
    context_analyzer = PeopleContextAnalyzer(preprocessor)
    if args.preprocessed:
        preprocessed_data = json.load(open(args.preprocessed))
        processed_sentences = preprocessed_data["Question 1"]["Processed Sentences"]
        processed_names = preprocessed_data["Question 1"]["Processed Names"]
        context_analyzer.names_and_nicknames = processed_names
        context_analyzer.processed_sentences = processed_sentences
        context_analyzer.create_names_nicknames_preprocessed(processed_names)
        context_analyzer.create_processed_sentences_preprocessed(processed_sentences)
        context_analyzer.generate_k_sequences(args.maxk)
        context_analyzer.find_mentions()
        results = context_analyzer.names_and_k_seqs
        return {"Person Contexts and K-Seqs": results}
    context_analyzer.create_names_nicknames(args.names, args.removewords)
    context_analyzer.create_processed_sentences(args.sentences, args.removewords)
    context_analyzer.generate_k_sequences(args.maxk)
    context_analyzer.find_mentions()
    results = context_analyzer.names_and_k_seqs

    return {"Person Contexts and K-Seqs": results}

def handle_q6(args):
    preprocessor = Preprocessor()
    graph_builder = ConnectionsGraph(args.threshold, args.windowsize, preprocessor)
    if args.preprocessed:
        preprocessed_data = json.load(open(args.preprocessed))
        processed_sentences = preprocessed_data["Question 1"]["Processed Sentences"]
        processed_names = preprocessed_data["Question 1"]["Processed Names"]
        graph_builder.create_name_map_preprocessed(processed_names)
        graph_builder.make_sentence_list_preprocessed(processed_sentences)
        graph = graph_builder.build_graph()
        return {"Pair Matches": graph}
    graph_builder.create_name_map(args.names, args.removewords)
    graph_builder.make_sentence_list(args.sentences, args.removewords)
    graph = graph_builder.build_graph()

    return {"Pair Matches": graph}

def handle_q7(args):
    preprocessor = Preprocessor()
    graph_builder = ConnectionsGraph(args.threshold, args.windowsize, preprocessor)
    if args.preprocessed:
        preprocessed_data = json.load(open(args.preprocessed))
        pair_matches = json.load(open(args.pairs))
        pair_matches = pair_matches["keys"]
        graph = preprocessed_data["Question 6"]["Pair Matches"]
        for edge in graph: #Now use the same logic from build_graph
            person1 = " ".join(edge[0])
            person2 = " ".join(edge[1])
            if person1 not in graph_builder.graph:
                graph_builder.graph[person1] = set()
            if person2 not in graph_builder.graph:
                graph_builder.graph[person2] = set()
            graph_builder.graph[person1].add(person2)
            graph_builder.graph[person2].add(person1)
        results = graph_builder.check_connections(pair_matches, args.maximal_distance)
        return {"Pair Matches": results}
    graph_builder.create_name_map(args.names, args.removewords)
    graph_builder.make_sentence_list(args.sentences, args.removewords)
    graph_builder.build_graph()
    pair_matches = json.load(open(args.pairs))
    pair_matches = pair_matches["keys"]
    results = graph_builder.check_connections(pair_matches, args.maximal_distance)

    return {"Pair Matches": results}

def handle_q8(args):
    preprocessor = Preprocessor()
    graph_builder = ConnectionsGraph(args.threshold, args.windowsize, preprocessor)
    if args.preprocessed:
        preprocessed_data = json.load(open(args.preprocessed))
        pair_matches = json.load(open(args.pairs))
        pair_matches = pair_matches["keys"]
        graph = preprocessed_data["Question 6"]["Pair Matches"]
        for edge in graph: #Now use the same logic from build_graph
            person1 = " ".join(edge[0])
            person2 = " ".join(edge[1])
            if person1 not in graph_builder.graph:
                graph_builder.graph[person1] = set()
            if person2 not in graph_builder.graph:
                graph_builder.graph[person2] = set()
            graph_builder.graph[person1].add(person2)
            graph_builder.graph[person2].add(person1)
        results = graph_builder.check_connections_exact(pair_matches, args.fixed_length)
        return {"Pair Matches": results}
    graph_builder.create_name_map(args.names, args.removewords)
    graph_builder.make_sentence_list(args.sentences, args.removewords)
    graph_builder.build_graph()
    pair_matches = json.load(open(args.pairs))
    pair_matches = pair_matches["keys"]
    results = graph_builder.check_connections_exact(pair_matches, args.fixed_length)

    return {"Pair Matches": results}

def main():

    args = read_args()
    
    try:
        if args.task == 1:
            result = handle_q1(args)
        elif args.task == 2:
            result = handle_q2(args)
        elif args.task == 3:
            result = handle_q3(args)
        elif args.task == 4:
            result = handle_q4(args)
        elif args.task == 5:
            result = handle_q5(args)
        elif args.task == 6:
            result = handle_q6(args)
        elif args.task == 7:
            result = handle_q7(args)
        elif args.task == 8:
            result = handle_q8(args)
        else:
            print("Invalid input")
            exit()
        output = {f"Question {args.task}": result}
        print(json.dumps(output, indent=4))
        
    except Exception:
        print("Invalid input")
        exit()

if __name__ == "__main__":

    main()
