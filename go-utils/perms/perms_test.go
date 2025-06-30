package main

import (
	"bytes"
	"errors"
	"strings"
	"os"
	"bufio"
	"testing"
)

// --- Helper functions ---
var lastOpenedFile string

// Helper to simulate file content for sources
type fakeSource struct {
	lines []string
}

func (f *fakeSource) Lines() []string {
	return f.lines
}

// Helper to create a temporary sourceArg and its content
func makeSourceArg(path string, depth int, lines []string) (sourceArg, []string) {
	return sourceArg{Path: path, Depth: depth}, lines
}

// --- Test Cases ---

func TestPermutatorGeneratesSequencesWithMultipleSources(t *testing.T) {
	// Simulate two files: ./tests/file1.txt ("a", "b"), ./tests/file2.txt ("x")
	src1, lines1 := makeSourceArg("./tests/file1.txt", 2, []string{"a", "b"})
	src2, lines2 := makeSourceArg("./tests/file2.txt", 1, []string{"x"})

	// Patch os.Open and bufio.NewScanner for this test
	origOpen := osOpen
	origScanner := bufioNewScanner
	defer func() {
		osOpen = origOpen
		bufioNewScanner = origScanner
	}()

	// Map file names to their lines
	fileContents := map[string][]string{
		"./tests/file1.txt": lines1,
		"./tests/file2.txt": lines2,
	}
	osOpen = func(name string) (*os.File, error) {
		if _, ok := fileContents[name]; ok {
			lastOpenedFile = name
			return &os.File{}, nil
		}
		return nil, errors.New("file not found")
	}
	bufioNewScanner = func(file *os.File) *bufio.Scanner {
		lines := fileContents[lastOpenedFile]
		return newMockScanner(lines)
	}

	var buf bytes.Buffer
	err := RunPermutator([]sourceArg{src1, src2}, []string{"-"}, "", "", false, func(s string) {
		buf.WriteString(s + "\n")
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	output := buf.String()
	if !strings.Contains(output, "a") || !strings.Contains(output, "b") || !strings.Contains(output, "x") {
		t.Errorf("Expected output to contain all items, got: %s", output)
	}
	if !strings.Contains(output, "a-b") {
		t.Errorf("Expected output to contain 'a-b', got: %s", output)
	}
}

func TestPermutatorAppliesPrefixAndSuffix(t *testing.T) {
	src, lines := makeSourceArg("./tests/file1.txt", 1, []string{"foo"})

	origOpen := osOpen
	origScanner := bufioNewScanner
	defer func() {
		osOpen = origOpen
		bufioNewScanner = origScanner
	}()
	osOpen = func(name string) (*os.File, error) {
		return &os.File{}, nil
	}
	bufioNewScanner = func(file *os.File) *bufio.Scanner {
		return newMockScanner(lines)
	}

	var buf bytes.Buffer
	err := RunPermutator([]sourceArg{src}, []string{""}, "PRE-", "-SUF", false, func(s string) {
		buf.WriteString(s + "\n")
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	output := buf.String()
	if !strings.Contains(output, "PRE-foo-SUF") {
		t.Errorf("Expected output to contain prefix and suffix, got: %s", output)
	}
}

func TestPermutatorNoRepeatsFlag(t *testing.T) {
	src, lines := makeSourceArg("./tests/file2.txt", 2, []string{"a", "b"})

	origOpen := osOpen
	origScanner := bufioNewScanner
	defer func() {
		osOpen = origOpen
		bufioNewScanner = origScanner
	}()
	osOpen = func(name string) (*os.File, error) {
		return &os.File{}, nil
	}
	bufioNewScanner = func(file *os.File) *bufio.Scanner {
		return newMockScanner(lines)
	}

	var buf bytes.Buffer
	err := RunPermutator([]sourceArg{src}, []string{" "}, "", "", true, func(s string) {
		buf.WriteString(s + "\n")
	})
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	output := buf.String()
	if strings.Contains(output, "a a") || strings.Contains(output, "b b") {
		t.Errorf("Expected no repeated words in output, got: %s", output)
	}
}

func TestSourceArgInvalidFormat(t *testing.T) {
	var s sourceArgs
	err := s.Set("./tests/file1.txt") // missing colon
	if err == nil || !strings.Contains(err.Error(), "format") {
		t.Errorf("Expected error for invalid format, got: %v", err)
	}
	err = s.Set("./tests/file1.txt:zero")
	if err == nil || !strings.Contains(err.Error(), "invalid depth") {
		t.Errorf("Expected error for invalid depth, got: %v", err)
	}
	err = s.Set("./tests/file1.txt:0")
	if err == nil || !strings.Contains(err.Error(), "invalid depth") {
		t.Errorf("Expected error for depth < 1, got: %v", err)
	}
}

func TestPermutatorFileOpenError(t *testing.T) {
	src := sourceArg{Path: "bad./tests/file1.txt", Depth: 1}

	origOpen := osOpen
	defer func() { osOpen = origOpen }()
	osOpen = func(name string) (*os.File, error) {
		return nil, errors.New("cannot open file")
	}

	var buf bytes.Buffer
	err := RunPermutator([]sourceArg{src}, []string{""}, "", "", false, func(s string) {
		buf.WriteString(s + "\n")
	})
	if err == nil || !strings.Contains(err.Error(), "cannot open file") {
		t.Errorf("Expected error for file open, got: %v", err)
	}
}

// --- Patch points for mocks and helpers ---

// newMockScanner returns a bufio.Scanner for a slice of lines.
func newMockScanner(lines []string) *bufio.Scanner {
	r := strings.NewReader(strings.Join(lines, "\n"))
	return bufio.NewScanner(r)
}

