#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import math
import logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Tuple


class WordEntropyCalculator:
    """
    Calculates Shannon entropy for words and provides filtering and sorting.
    """

    def __init__(self,
                 words: List[str],
                 min_entropy: float = 0.0,
                 max_entropy: Optional[float] = None):
        if not isinstance(words, list):
            raise TypeError(f"words must be a list of strings, got {type(words)}")
        if not words:
            raise ValueError("words list cannot be empty")
        self.words = words
        self.min_entropy = min_entropy
        self.max_entropy = max_entropy
        self._validate_entropy_bounds()

    def _validate_entropy_bounds(self):
        if self.min_entropy < 0:
            raise ValueError("min_entropy must be non-negative")
        if self.max_entropy is not None:
            if self.max_entropy < 0:
                raise ValueError("max_entropy must be non-negative")
            if self.max_entropy < self.min_entropy:
                raise ValueError("max_entropy must be >= min_entropy")

    @staticmethod
    def calculate_entropy(word: str) -> float:
        """
        Compute the Shannon entropy of a single word.
        Returns 0.0 for an empty string.
        """
        if not isinstance(word, str):
            raise TypeError(f"Word must be a string, got {type(word)}")
        length = len(word)
        if length == 0:
            return 0.0
        counts = Counter(word)
        entropy = 0.0
        for count in counts.values():
            p = count / length
            entropy -= p * math.log2(p)
        return entropy

    def calculate_entropies(self) -> Dict[str, float]:
        """
        Calculate entropies for each unique word using multiple threads.
        Returns a mapping from word to its entropy.
        """
        unique_words = list(set(self.words))
        entropies: Dict[str, float] = {}
        with ThreadPoolExecutor() as executor:
            future_to_word = {
                executor.submit(self.calculate_entropy, word): word
                for word in unique_words
            }
            for future in as_completed(future_to_word):
                word = future_to_word[future]
                try:
                    entropies[word] = future.result()
                except Exception as e:
                    logging.error(f"Failed to calculate entropy for '{word}': {e}")
        return entropies

    def filter_and_sort(self,
                        order: str = 'decreasing') -> List[Tuple[str, float]]:
        """
        Filters words by the configured min/max entropy bounds, then sorts.
        `order` may be 'increasing' or 'decreasing'.
        Returns a list of (word, entropy) tuples sorted by entropy.
        """
        if order not in ('increasing', 'decreasing'):
            raise ValueError("order must be 'increasing' or 'decreasing'")
        entropies = self.calculate_entropies()
        filtered = {
            word: ent
            for word, ent in entropies.items()
            if ent >= self.min_entropy and
               (self.max_entropy is None or ent <= self.max_entropy)
        }
        reverse = (order == 'decreasing')
        sorted_items = sorted(filtered.items(), key=lambda item: item[1], reverse=reverse)
        return sorted_items


def main():
    logging.basicConfig(level=logging.ERROR)
    parser = argparse.ArgumentParser(
        description="Compute word entropies, filter by range, and sort."
    )
    parser.add_argument(
        '--order',
        choices=['increasing', 'decreasing'],
        default='decreasing',
        help="Sort order for entropy scores (default: decreasing)"
    )
    parser.add_argument(
        '--min-entropy',
        type=float,
        default=0.0,
        help="Minimum entropy threshold (inclusive)"
    )
    parser.add_argument(
        '--max-entropy',
        type=float,
        default=None,
        help="Maximum entropy threshold (inclusive); default is no upper bound"
    )
    parser.add_argument(
        'words',
        nargs='*',  # allow zero or more words
        help="List of words to process; if empty, read from stdin"
    )
    args = parser.parse_args()

    if not args.words:
        try:
            data = sys.stdin.read()
            if not data.strip():
                raise ValueError("No input provided via stdin or arguments")
            args.words = data.split()
        except Exception as e:
            print(f"Error reading words from stdin: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        calculator = WordEntropyCalculator(
            words=args.words,
            min_entropy=args.min_entropy,
            max_entropy=args.max_entropy
        )
        result = calculator.filter_and_sort(order=args.order)
        for word, ent in result:
            print(f"{word}\t{ent}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
