import pytest
import tempfile
import os
import sys
from utils.permutation.digit.permute_digit import generate_variants, process_chunk, chunked_file_reader, main

def test_generate_all_digit_permutations():
    # "a1b2" has digits at positions 1 and 3, so 100 variants (10*10)
    word = "a1b2"
    variants = set(generate_variants(word))
    expected = set(f"a{d1}b{d2}" for d1 in "0123456789" for d2 in "0123456789")
    assert variants == expected
    assert len(variants) == 100

def test_generate_permutations_with_depth():
    # "x1y2z3" has digits at positions 1, 3, 5
    # depth=2 should only permute last two digits (positions 3,5)
    word = "x1y2z3"
    variants = set(generate_variants(word, depth=2))
    # Only digits at positions 3 and 5 are permuted, position 1 stays as '1'
    expected = set(f"x1y{d2}z{d3}" for d2 in "0123456789" for d3 in "0123456789")
    assert variants == expected
    assert all(v[1] == "1" for v in variants)
    assert len(variants) == 100

def test_multiprocessing_output_integrity(tmp_path):
    # Prepare input file with two lines, each with two digits
    input_lines = ["a1b2\n", "c3d4\n"]
    input_file = tmp_path / "input.txt"
    output_file = tmp_path / "output.txt"
    input_file.write_text("".join(input_lines), encoding="utf-8")
    # Run main with multiprocessing (workers=2)
    sys_argv = [
        "permute_digit.py",
        str(input_file),
        str(output_file),
        "--workers", "2",
        "--chunk-size", "1"
    ]
    old_argv = sys.argv
    sys.argv = sys_argv
    try:
        main()
    finally:
        sys.argv = old_argv
    # Check output: each line should have 100 variants, total 200 lines
    output_lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(output_lines) == 200
    # Spot check a few expected variants
    assert "a0b0" in output_lines
    assert "a9b9" in output_lines
    assert "c0d0" in output_lines
    assert "c9d9" in output_lines

def test_no_digits_in_word():
    # No digits, should yield nothing
    word = "abcdef"
    variants = list(generate_variants(word))
    assert variants == []

def test_empty_input_file(tmp_path):
    # Create empty input file
    input_file = tmp_path / "empty.txt"
    output_file = tmp_path / "out.txt"
    input_file.write_text("", encoding="utf-8")
    sys_argv = [
        "permute_digit.py",
        str(input_file),
        str(output_file)
    ]
    old_argv = sys.argv
    sys.argv = sys_argv
    try:
        main()
    finally:
        sys.argv = old_argv
    # Output file should be empty
    assert output_file.read_text(encoding="utf-8") == ""

def test_file_io_error_handling(tmp_path):
    # Input file does not exist
    input_file = tmp_path / "does_not_exist.txt"
    output_file = tmp_path / "out.txt"
    sys_argv = [
        "permute_digit.py",
        str(input_file),
        str(output_file)
    ]
    old_argv = sys.argv
    sys.argv = sys_argv
    # Capture stderr and SystemExit
    import io
    from contextlib import redirect_stderr
    stderr = io.StringIO()
    with pytest.raises(SystemExit):
        with redirect_stderr(stderr):
            main()
    err = stderr.getvalue()
    assert "File error" in err

