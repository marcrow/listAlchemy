#!/usr/bin/env python3
"""
Script to extract unique words from a website's content, filtered by word length,
and ordered by occurrence count (descending).
"""
import argparse
import logging
import re
import sys
from collections import Counter

import requests
from bs4 import BeautifulSoup

# Disable HTTPS warnings when verify=False
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WordExtractor:
    """
    A class to fetch a webpage, extract words, filter by length,
    count occurrences, and return sorted unique words.
    """

    WORD_REGEX = re.compile(r"\b[A-Za-z][A-Za-z0-9']*\b")

    def __init__(self, url: str, min_length: int = 1, max_length: int = None):
        """
        Initialize WordExtractor.

        :param url: URL of the website to extract words from.
        :param min_length: Minimum word length to include.
        :param max_length: Maximum word length to include. None for no upper bound.
        """
        self.url = url
        self.min_length = min_length
        self.max_length = max_length
        self._validate_lengths()
        logging.debug(f"Initialized WordExtractor(url={url}, min_length={min_length}, max_length={max_length})")

    def _validate_lengths(self):
        """
        Validate that min_length and max_length are positive and logical.
        """
        if self.min_length < 1:
            raise ValueError("min_length must be at least 1")
        if self.max_length is not None:
            if self.max_length < self.min_length:
                raise ValueError("max_length cannot be less than min_length")
        logging.debug("Word length parameters validated.")

    def fetch_content(self) -> str:
        """
        Fetch HTML content from the URL.

        :return: Raw HTML text.
        :raises: requests.exceptions.RequestException on network issues.
        """
        try:
            response = requests.get(self.url, verify=False, timeout=10)
            response.raise_for_status()
            logging.info(f"Fetched content from {self.url} (status={response.status_code})")
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching {self.url}: {e}")
            raise

    def parse_text(self, html: str) -> str:
        """
        Parse HTML to extract visible text.

        :param html: Raw HTML content.
        :return: Cleaned text.
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            # Remove scripts and styles
            for tag in soup(['script', 'style', 'noscript']):
                tag.decompose()
            text = soup.get_text(separator=' ')
            logging.debug("Parsed HTML and extracted text.")
            return text
        except Exception as e:
            logging.error(f"Error parsing HTML: {e}")
            raise

    def extract_words(self, text: str) -> list:
        """
        Extract words matching WORD_REGEX from text.

        :param text: Input text.
        :return: List of words.
        """
        words = self.WORD_REGEX.findall(text)
        logging.debug(f"Extracted {len(words)} raw word candidates.")
        return words

    def filter_words(self, words: list) -> list:
        """
        Filter words by length constraints and normalize to lowercase.

        :param words: List of raw words.
        :return: Filtered list of words.
        """
        filtered = []
        for w in words:
            lw = w.lower()
            length = len(lw)
            if length < self.min_length:
                continue
            if self.max_length is not None and length > self.max_length:
                continue
            filtered.append(lw)
        logging.debug(f"Filtered down to {len(filtered)} words by length.")
        return filtered

    def count_words(self, words: list) -> Counter:
        """
        Count occurrences of each word.

        :param words: List of filtered words.
        :return: Counter mapping word->count.
        """
        counter = Counter(words)
        logging.debug(f"Counted {len(counter)} unique words.")
        return counter

    def get_sorted_words(self, counter: Counter) -> list:
        """
        Sort words by occurrence (descending), then alphabetically.

        :param counter: Counter of word counts.
        :return: List of (word, count) tuples.
        """
        sorted_words = sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0])
        )
        logging.debug("Sorted words by count and name.")
        return sorted_words

    def extract(self) -> list:
        """
        Full pipeline: fetch, parse, extract, filter, count, sort.

        :return: Sorted list of (word, count).
        """
        html = self.fetch_content()
        text = self.parse_text(html)
        raw_words = self.extract_words(text)
        words = self.filter_words(raw_words)
        counts = self.count_words(words)
        sorted_list = self.get_sorted_words(counts)
        return sorted_list


def main():
    """
    CLI entry point. Parses arguments and runs extraction.
    """
    parser = argparse.ArgumentParser(
        description="Extract and count unique words from a website, filtered by length."
    )
    parser.add_argument('url', help='URL of the website to analyze')
    parser.add_argument('--min', type=int, default=1,
                        help='Minimum word length to include (default: 1)')
    parser.add_argument('--max', type=int, default=None,
                        help='Maximum word length to include (default: no limit)')
    parser.add_argument('-w', '--words-only', action='store_true',
                        help='Do not display the number of occurence')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose logging')
    args = parser.parse_args()

    # Configure logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    try:
        extractor = WordExtractor(args.url, min_length=args.min, max_length=args.max)
        result = extractor.extract()
        for word, count in result:
            if args.words_only :
                print(f"{word}")
            else :
                print(f"{word}\t{count}")
    except Exception as e:
        logging.critical(f"Extraction failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
