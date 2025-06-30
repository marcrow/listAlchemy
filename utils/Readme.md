# ListAlchemy python utils

Before using one of these script initiate the python env.

```bash
python3 -m venv venv
source venv/bin/activate
```

You can directly install every dependances.

```bash
pip install -r utils/requirements.txt
```

Here’s a suggested Markdown “rubric”/section you can drop into your project’s README.md to document the WordEntropyCalculator, its purpose (“job”), how to import it, and how to use it both as a library and from the CLI:




## Analyse tools 
### Word Entropy Calculator

A simple, thread-pooled utility for computing Shannon entropy on words, filtering by an entropy range, and sorting them.

---

### 📌 What It Does (Its “Job”)

- **Compute** the Shannon entropy of each unique word in a list  
- **Filter** out words whose entropy falls outside a given `[min_entropy, max_entropy]` range  
- **Sort** the remaining words by entropy (ascending or descending)  
- **Run** either as a Python class or via a command-line script  

---

#### 📥 How to Import

```python
from entropy import WordEntropyCalculator
```

---

#### 🛠️ API Usage

```python
from entropy import WordEntropyCalculator

# 1. Prepare your data
words = ["apple", "banana", "orange", "kiwi", "date", "apple"]

# 2. Instantiate the calculator
#    - min_entropy: minimum allowable entropy (inclusive)
#    - max_entropy: maximum allowable entropy (inclusive; None for no upper bound)
calc = WordEntropyCalculator(
    words=words,
    min_entropy=1.0,
    max_entropy=3.0
)

# 3. Filter & sort
#    - order="increasing" or "decreasing"
result = calc.filter_and_sort(order="decreasing")

print(result)
# e.g. ['banana', 'orange', 'apple']
```

##### Class: `WordEntropyCalculator`

| Method                               | Description                                                                                   |
|--------------------------------------|-----------------------------------------------------------------------------------------------|
| `__init__(words, min_entropy, max_entropy)` | Set up with your word list and entropy bounds (validates inputs).                             |
| `calculate_entropy(word: str) → float`      | (Static) Compute Shannon entropy for one word.                                               |
| `calculate_entropies() → Dict[str,float]`    | (Internal) Multi-threaded computation of entropy for each unique word.                        |
| `filter_and_sort(order='decreasing') → List[str]` | Filter by entropy range and return words sorted by entropy (order can be `"increasing"`). |

---

#### ▶️ CLI Usage

Once installed or placed in your `$PATH`:

```bash
# Basic:
python entropy.py word1 word2 word3

# With filters and custom sort:
python entropy.py --order increasing \
                  --min-entropy 1.5 \
                  --max-entropy 3.5 \
                  apple banana orange kiwi date
```

**Options**  
- `--order {increasing,decreasing}` (default: `decreasing`)  
- `--min-entropy FLOAT` (default: `0.0`)  
- `--max-entropy FLOAT` (default: no upper bound)  

---

#### ⚠️ Error Handling

- Invalid types or empty word lists raise a clear exception.  
- `max_entropy` must be ≥ `min_entropy`.  
- Unrecognized CLI options will display usage help.



---


## Token Extractor Script

Idea from : https://github.com/tomnomnom/hacks/blob/master/tok/main.go

### Features

* **Customizable Length Filters**: Set minimum/maximum token lengths (`--min`, `--max`).
* **Alpha‑Numeric Enforcement**: Optionally require tokens to contain both letters and numbers (`--alpha-num-only`).
* **Delimiter Exceptions**: Treat specified characters as part of tokens rather than delimiters (`--delim-exceptions`).
* **URL‑Decoding**: Automatically decodes URL‑encoded sequences (e.g. `%20`).
* **Occurrence Counting**: Counts total occurrences of each token across all domains.
* **Separator Tracking**: Records the maximum number of non‑alphanumeric (excluding `.`) separators found in any domain for each token. (Amazing for permutation depth)

### Integration

1. **Add to Project**: Copy `tok.py` into your repo.
2. **Make Executable**: Run `chmod +x tok.py`.
3. **Install Dependencies**: Requires only Python 3.x standard library.
4. **Import (optional)**: To reuse in code:

   ```python
   from tok import TokenExtractor
   extractor = TokenExtractor(minlength=2, maxlength=20)
   tokens = list(extractor.extract_tokens('example.com'))
   ```

### CLI Usage

```bash
# Basic usage: read domains from stdin, output "token count max_separators"
cat domains.txt | ./tok.py --min 3 --max 15 --alpha-num-only --delim-exceptions "-_"

# Flags:
#   --min N            Minimum token length (default: 1)
#   --max N            Maximum token length (default: 25)
#   --alpha-num-only   Only include tokens with both letters & numbers
#   --delim-exceptions CHARS  Characters to treat as non-delimiters
```



## Web

### WordExtractor

Target : subdomain enumeration.

#### What it does
`WordExtractor` fetches any webpage, strips out HTML/JS/CSS, extracts all words, filters them by length, counts how often each appears, and returns a sorted list of unique words by frequency.

#### Installation
Make sure your environment has:
```bash
pip install requests beautifulsoup4
```

#### How to import
If your package layout is:
```
your_project/
├── webExtractor.py
└── README.md
```
then in your code simply:
```python
from webExtractor import WordExtractor
```

#### How to use

##### As a library
```python
# instantiate with URL, minimum and maximum word lengths:
extractor = WordExtractor(
    url="https://example.com",
    min_length=3,
    max_length=12
)

# run the full pipeline:
word_counts = extractor.extract()

# `word_counts` is a list of (word, count) tuples, sorted by count desc:
for word, count in word_counts[:20]:
    print(f"{word}: {count}")
```

##### From the command line
```bash
cd utils/web
# basic usage:
python webExtractor.py https://example.com

# with length filters:
python webExtractor.py https://example.com --min 4 --max 10

# verbose logging:
python webExtractor.py https://example.com --min 4 --max 10 --verbose
```

#### Constructor arguments
| Argument    | Type    | Default | Description                                 |
|-------------|---------|---------|---------------------------------------------|
| `url`       | `str`   | —       | The webpage URL to fetch                    |
| `min_length`| `int`   | `1`     | Minimum word length to include              |
| `max_length`| `int\|None` | `None`   | Maximum word length (omit for no upper bound)|

### Output
The `.extract()` method returns a list of `(word, count)` pairs sorted first by descending count, then alphabetically.

---
