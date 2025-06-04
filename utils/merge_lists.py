import argparse

def merge_first_results(file1: str, file2: str) -> list:
    """
    Merge, deduplicate, and sort results from assetfinder and subfinder output files.
    Save the merged list to a dedicated file and return the list.

    Args:
        assetfinder_file (str): Path to assetfinder output file.
        subfinder_file (str): Path to subfinder output file.
        host_dir (str): Directory to save the merged results.

    Returns:
        list: Sorted, deduplicated list of targets.
    """
    results = set()
    for file_path in [file1, file2]:
        try:
            with open(file_path, "r") as f:
                for line in f:
                    clean = line.strip()
                    if clean:
                        results.add(clean)
        except FileNotFoundError:
            continue  # If a file doesn't exist, skip it

    sorted_results = sorted(results)
    merged_file = f"{file1}.merged"
    with open(merged_file, "w") as f:
        for item in sorted_results:
            f.write(f"{item}\n")
    return sorted_results


def main():
    parser = argparse.ArgumentParser(
        description="Merge, deduplicate, and sort results from two files, saving the merged list."
    )
    parser.add_argument(
        "file1", type=str, help="Path to the first input file (e.g., assetfinder output)"
    )
    parser.add_argument(
        "file2", type=str, help="Path to the second input file (e.g., subfinder output)"
    )
    parser.add_argument(
        "-v", '--verbose', action='store_true'
    )
    args = parser.parse_args()

    merged = merge_first_results(args.file1, args.file2)
    if (args.verbose):
        print("Merged and sorted results:")
        for item in merged:
            print(item)

if __name__ == "__main__":
    main()