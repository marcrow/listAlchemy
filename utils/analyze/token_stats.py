import argparse
import os
from collections import Counter


class WordListProcessor:
    """Process and manage a list of single words and their statistics."""
    def __init__(self, output_file, count_file=None):
        self.output_file = output_file
        self.count_file = count_file
        self.words = Counter()

    def parse_word_list(self, file_path):
        """Read a file with one word per line and count occurrences."""
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    word = line.strip()
                    if word:
                        self.words[word] += 1
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
        except Exception as e:
            print(f"Error processing file '{file_path}': {e}")

    def save_word_list(self):
        """Save unique words, sorted, to the output file."""
        try:
            existing = set()
            if os.path.exists(self.output_file):
                with open(self.output_file, 'r') as f:
                    existing = set(f.read().splitlines())

            all_words = existing.union(self.words.keys())
            with open(self.output_file, 'w') as f:
                for word in sorted(all_words):
                    f.write(f"{word}\n")
        except Exception as e:
            print(f"Error saving word list to '{self.output_file}': {e}")

    def save_counts(self):
        """Update the count file with cumulative word counts."""
        if not self.count_file:
            print("Error: No count file specified; skipping saving counts.")
            return
        try:
            existing_counts = Counter()
            if os.path.exists(self.count_file):
                with open(self.count_file, 'r') as f:
                    for line in f:
                        w, c = line.rsplit(' ', 1)
                        existing_counts[w] = int(c)

            existing_counts.update(self.words)
            with open(self.count_file, 'w') as f:
                for w, c in existing_counts.items():
                    f.write(f"{w} {c}\n")
        except Exception as e:
            print(f"Error saving counts to '{self.count_file}': {e}")

    def display_top_stats(self, top_n=0):
        """Display the top N words by count; if top_n is 0, display all."""
        if not self.count_file:
            print("Error: No count file specified; cannot display stats.")
            return
        try:
            # Ensure the stats file exists, create if missing
            if not os.path.exists(self.count_file):
                open(self.count_file, 'w').close()
                print(f"Created new statistics file at '{self.count_file}'.")

            counts = Counter()
            with open(self.count_file, 'r') as f:
                for line in f:
                    if line.strip():
                        w, c = line.rsplit(' ', 1)
                        counts[w] = int(c)

            items = counts.items() if top_n == 0 else counts.most_common(top_n)

            for w, c in items:
                print(f"{w}: {c}")
        except Exception as e:
            print(f"Error displaying stats from '{self.count_file}': {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Process a list of single words to create a wordlist and stats."
    )
    parser.add_argument('-i', '--input', help="Path to the input file with one word per line.")
    parser.add_argument('-o', '--output', help="Path to save the word list.")
    parser.add_argument('-n', '--no-count', action='store_true', help="Disable counting occurrences of words.")
    parser.add_argument('-s', '--stats', type=int, default=None,
                        help="Display the top N words from the statistics file. 0 for all.")
    parser.add_argument('-c', '--count-file', help="Path to the statistics file.")

    args = parser.parse_args()

    # Display stats if requested
    if args.stats is not None:
        if not args.count_file:
            print("Error: --count-file/-c option is required to display stats.")
            return
        processor = WordListProcessor(output_file=None, count_file=args.count_file)
        processor.display_top_stats(args.stats)
        return

    # Validate required arguments for processing
    if not args.input or not args.output:
        print("Error: --input/-i and --output/-o options are required to generate the word list.")
        print("Or use --stats/-s with --count-file/-c to display stats.")
        return

    processor = WordListProcessor(output_file=args.output,
                                  count_file=args.count_file)

    # Parse the word list
    processor.parse_word_list(args.input)

    # Save unique words
    processor.save_word_list()

    # Update counts unless disabled and count_file provided
    if not args.no_count and args.count_file:
        processor.save_counts()

    print(f"Processed words have been saved to '{args.output}'.")
    if not args.no_count and args.count_file:
        print(f"Word counts have been saved to '{args.count_file}'.")


if __name__ == "__main__":
    main()
