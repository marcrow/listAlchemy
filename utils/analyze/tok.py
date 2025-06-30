#!/usr/bin/env python3
import sys
import argparse
import urllib.parse
from collections import Counter

class TokenExtractor:
    def __init__(self, minlength=1, maxlength=25, alpha_num_only=False, delim_exceptions=""):
        self.minlength = minlength
        self.maxlength = maxlength
        self.alpha_num_only = alpha_num_only
        self.delim_exceptions = set(delim_exceptions)

    @staticmethod
    def _is_letter(ch):
        return ch.isalpha()

    @staticmethod
    def _is_number(ch):
        return ch.isdigit()

    def extract_tokens(self, text):
        """
        Extract tokens from a single text string, yielding tokens.
        """
        buf = []
        includes_letters = False
        includes_numbers = False
        maybe_urlencoded = False

        for ch in text:
            if self._is_letter(ch):
                includes_letters = True
            if self._is_number(ch):
                includes_numbers = True

            is_delim = not (self._is_letter(ch) or self._is_number(ch)) and ch not in self.delim_exceptions

            if is_delim:
                if buf:
                    token = "".join(buf)
                    if maybe_urlencoded:
                        try:
                            token = urllib.parse.unquote(token)
                        except Exception:
                            pass

                    length = len(token)
                    if self.minlength <= length <= self.maxlength:
                        if not self.alpha_num_only or (includes_letters and includes_numbers):
                            yield token
                # reset for next token
                buf = []
                includes_letters = False
                includes_numbers = False
                maybe_urlencoded = False
            else:
                if ch == '%':
                    maybe_urlencoded = True
                buf.append(ch)

        # Flush last buffer
        if buf:
            token = "".join(buf)
            if maybe_urlencoded:
                try:
                    token = urllib.parse.unquote(token)
                except Exception:
                    pass
            length = len(token)
            if self.minlength <= length <= self.maxlength:
                if not self.alpha_num_only or (includes_letters and includes_numbers):
                    yield token


def main():
    parser = argparse.ArgumentParser(
        description="Extract tokens from domains and count occurrences plus separator counts."
    )
    parser.add_argument("--min", type=int, default=1, help="minimum token length")
    parser.add_argument("--max", type=int, default=25, help="maximum token length")
    parser.add_argument("--alpha-num-only", action="store_true",
                        help="only include tokens containing both letters and numbers")
    parser.add_argument("--delim-exceptions", type=str, default="",
                        help="characters to treat as part of tokens (not delimiters)")
    args = parser.parse_args()

    extractor = TokenExtractor(
        minlength=args.min,
        maxlength=args.max,
        alpha_num_only=args.alpha_num_only,
        delim_exceptions=args.delim_exceptions
    )

    token_counts = Counter()
    max_separators = {}

    # Process each domain (one per line)
    for line in sys.stdin:
        domain = line.strip()
        if not domain:
            continue
        # count separators in domain (excluding dots)
        sep_count = sum(
            1 for ch in domain
            if not (ch.isalnum() or ch in extractor.delim_exceptions or ch == '.')
        )
        # extract tokens
        for token in extractor.extract_tokens(domain):
            token_counts[token] += 1
            prev = max_separators.get(token, 0)
            if sep_count > prev:
                max_separators[token] = sep_count

    # sort by count descending, then token
    sorted_tokens = sorted(
        token_counts.items(),
        key=lambda x: (-x[1], x[0])
    )

    # output: token count max_separators
    for token, cnt in sorted_tokens:
        sep = max_separators.get(token, 0)
        print(f"{token} {cnt} {sep}")


if __name__ == "__main__":
    main()
