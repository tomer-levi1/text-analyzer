# Text Analyzer

A command-line tool, written in Python, that analyzes a collection of sentences and finds how the people mentioned in them are connected.

It cleans and tokenizes text, counts word sequences (n-grams), searches for given sequences, finds the context around each person's name, and builds a graph of people who appear close together in the text. The graph can then be searched to check whether two people are connected.

Built as the final project of my Introduction to Computer Science course (Python).

**Demo video:** https://www.youtube.com/watch?v=QRQr4RTTm98

## Features

| Task | What it does |
|------|--------------|
| 1 | **Preprocessing:** lowercases text, removes punctuation, removes unwanted words and extra spaces, and splits sentences into words. Names and nicknames are processed the same way. |
| 2 | **Sequence counts:** counts every word sequence of length 1 up to `k` across all sentences and sorts the results. |
| 3 | **Name mentions:** counts the words in the text that contain a person's first or last name. |
| 4 | **Sequence search:** given a list of word sequences, returns the sentences that contain each one. |
| 5 | **Person context:** for each person, collects the word sequences that appear in sentences where they are mentioned. |
| 6 | **Connections graph:** slides a window of sentences over the text, links people who are mentioned together in at least `threshold` windows, and returns the edges. |
| 7 | **Connection check:** checks whether two people are connected in the graph within a maximal distance. |
| 8 | **Fixed-length connection check:** checks whether two people are connected by a path of an exact length. |

## Requirements

- Python 3.8+
- [pandas](https://pandas.pydata.org/)
- [pytest](https://docs.pytest.org/) (only for running the tests)

```bash
pip install pandas pytest
```

## Usage

```bash
python main.py -t <task> [options] > result.json
```

| Option | Meaning |
|--------|---------|
| `-t`, `--task` | Task number (1-8) |
| `-s`, `--sentences` | Path to the sentences CSV |
| `-n`, `--names` | Path to the names CSV |
| `-r`, `--removewords` | Path to the CSV of words to remove |
| `-p`, `--preprocessed` | JSON output of task 1 (or 6), to skip re-processing |
| `--maxk` | Maximum sequence length (tasks 2, 5) |
| `--qsek_query_path` | JSON file with the sequences to search for (task 4) |
| `--windowsize` | Window size, in sentences (tasks 6-8) |
| `--threshold` | Minimum number of windows in which two people must appear together to be connected (tasks 6-8) |
| `--pairs` | JSON file with pairs of people to check (tasks 7, 8) |
| `--maximal_distance` | Maximal path length allowed (task 7) |
| `--fixed_length` | Exact path length required (task 8) |

Output is printed as JSON. Invalid input prints `Invalid input`.

### Input formats

- **Sentences CSV:** a column named `sentence`.
- **Names CSV:** columns named `Name` and `Other Names` (nicknames).
- **Remove words CSV:** a column named `words`.
- **Pairs / sequence query JSON:** an object with a `keys` list.

### Examples

A small made-up data set is included in `sample_data/` (a bakery story with five people), so you can try the tool right away:

```bash
# Task 3: count mentions of each person
python main.py -t 3 -s sample_data/sentences.csv -n sample_data/people.csv -r sample_data/REMOVEWORDS.csv

# Task 4: find sentences containing given word sequences
python main.py -t 4 -s sample_data/sentences.csv --qsek_query_path sample_data/kseq_query_keys.json -r sample_data/REMOVEWORDS.csv

# Task 6: build the connections graph
python main.py -t 6 -s sample_data/sentences.csv -n sample_data/people.csv -r sample_data/REMOVEWORDS.csv --windowsize 1 --threshold 2

# Task 7: check whether pairs of people are connected within 2 steps
python main.py -t 7 -s sample_data/sentences.csv -n sample_data/people.csv --pairs sample_data/people_connections.json -r sample_data/REMOVEWORDS.csv --windowsize 1 --threshold 2 --maximal_distance 2

# Task 8: check whether pairs are connected by a path of exactly 3 steps
python main.py -t 8 -s sample_data/sentences.csv -n sample_data/people.csv --pairs sample_data/people_connections.json -r sample_data/REMOVEWORDS.csv --windowsize 1 --threshold 2 --fixed_length 3
```

Add `> result.json` at the end of any command to save the output to a file.

## Tests

Each function has its own test, in `test_main.py`:

```bash
pytest
```

The `handle_*` functions are not tested directly, since each one only combines smaller functions that are tested separately.

## Design decisions

- **pandas for file reading.** `read_csv` and `read_json` handle file-format problems well, and made loading the input files simple.
- **Dictionaries for building data.** It is easier to set values by key while constructing data (for example sequence counts and the k-sequence search), then convert to lists for the final output. In task 4, a dictionary gives an O(1) membership check and also remembers which sentences contain each sequence, which a set cannot do.
- **The graph is a dictionary of sets.** Each person maps to the set of people they are connected to. This makes the graph searches in tasks 7 and 8 direct, instead of rebuilding a structure from a plain list of edges.
- **Small functions plus "handler" functions.** Each task has a `handle_q*` function that calls the smaller functions, so `main` stays short and each piece can be debugged and tested on its own.

## Project structure

```
.
├── main.py        # all the code: preprocessing, analysis, graph, CLI
├── test_main.py   # pytest tests
├── sample_data/   # small made-up input files for trying the tool
└── README.md
```
