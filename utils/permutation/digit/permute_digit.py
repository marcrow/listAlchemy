class DigitPermuter:
    """
    A class to generate digit permutations for words containing digits.
    """

    def __init__(self, depth=None, workers=1, chunk_size=1000, digit_list='0123456789'):
        """
        Initialize the DigitPermuter.

        Args:
            depth (int, optional): Limit permutations to the last N digits. Default is None (all digits).
            workers (int, optional): Number of worker processes to use. Default is 1 (no multiprocessing).
            chunk_size (int, optional): Number of lines to process per chunk. Default is 1000.
        """
        self.depth = depth
        self.workers = workers
        self.chunk_size = chunk_size
        self.digit_list = digit_list

    def generate_variants(self, word):
        """
        For a given word, yield all variants where digit positions
        (limited to the last 'depth' if provided) are replaced by 0–9.
        """
        import re
        import itertools

        word = word.rstrip('\n')
        positions = [m.start() for m in re.finditer(r'\d', word)]
        if not positions:
            return word
        if self.depth and self.depth > 0:
            positions = positions[-self.depth:]
        segments = []
        last_index = 0
        for pos in positions:
            segments.append(word[last_index:pos])
            segments.append(None)  # placeholder for a digit
            last_index = pos + 1
        segments.append(word[last_index:])
        for combo in itertools.product(self.digit_list, repeat=len(positions)):
            output = []
            idx = 0
            for seg in segments:
                if seg is None:
                    output.append(combo[idx])
                    idx += 1
                else:
                    output.append(seg)
            yield ''.join(output)

    def process_chunk(self, lines):
        """
        Process a chunk of lines, returning a list of generated variants.
        """
        output = []
        for line in lines:
            for variant in self.generate_variants(line):
                output.append(variant)
        return output

    def chunked_file_reader(self, file_handle):
        """
        Read a file in chunks of up to self.chunk_size lines.
        """
        chunk = []
        for line in file_handle:
            chunk.append(line)
            if len(chunk) >= self.chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

    def permute_file(self, input_path, output_path):
        """
        Read an input file, permute digit positions, and write results to output file.
        """
        import sys
        from functools import partial
        from multiprocessing import Pool

        try:
            fin = open(input_path, 'r', encoding='utf-8', errors='ignore')
            fout = open(output_path, 'w', encoding='utf-8')
        except IOError as e:
            sys.stderr.write(f"File error: {e}\n")
            raise

        if self.workers > 1:
            with Pool(self.workers) as pool:
                worker_func = partial(DigitPermuter._static_process_chunk, depth=self.depth)
                for chunk in self.chunked_file_reader(fin):
                    for result in pool.imap(worker_func, [chunk]):
                        for word in result:
                            fout.write(word + "\n")
        else:
            for chunk in self.chunked_file_reader(fin):
                for word in self.process_chunk(chunk):
                    fout.write(word + "\n")

        fin.close()
        fout.close()

    @staticmethod
    def _static_generate_variants(word, depth):
        """
        Static version of generate_variants for multiprocessing.
        """
        import re
        import itertools

        word = word.rstrip('\n')
        positions = [m.start() for m in re.finditer(r'\d', word)]
        if not positions:
            return [word]
        if depth and depth > 0:
            positions = positions[-depth:]
        segments = []
        last_index = 0
        for pos in positions:
            segments.append(word[last_index:pos])
            segments.append(None)
            last_index = pos + 1
        segments.append(word[last_index:])
        results = []
        for combo in itertools.product('0123456789', repeat=len(positions)):
            output = []
            idx = 0
            for seg in segments:
                if seg is None:
                    output.append(combo[idx])
                    idx += 1
                else:
                    output.append(seg)
            results.append(''.join(output))
        return results

    @staticmethod
    def _static_process_chunk(lines, depth):
        """
        Static version of process_chunk for multiprocessing.
        """
        output = []
        for line in lines:
            output.extend(DigitPermuter._static_generate_variants(line, depth))
        return output


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
    description="Permute digits in a wordlist (one word per line) from 0 to 9."
    )
    parser.add_argument("input", help="Input file path")
    parser.add_argument("output", help="Output file path")
    parser.add_argument(
        "--depth", "-d", type=int, default=1,
        help="Limit permutations to the last N digits (default: all digits)"
    )
    parser.add_argument(
        "--workers", "-w", type=int, default=2,
        help="Number of worker processes to use (default: 1)"
    )
    parser.add_argument(
        "--chunk-size", "-c", type=int, default=1000,
        help="Number of lines to process per chunk (default: 1000)"
    )
    parser.add_argument(
        "--digit", '-i', default='0123456789', help="List of digit used for permutationn"
    )
    args = parser.parse_args()
    permuter = DigitPermuter(depth=args.depth, workers=args.depth, chunk_size=args.chunk_size, digit_list=args.digit)
    permuter.permute_file(args.input, args.output)

    # Or for direct variant generation:
    # for variant in permuter.generate_variants("coucou"):
    #     print(variant)