package main

import (
    "bufio"
    "errors"
    "flag"
    "fmt"
    "os"
    "strconv"
    "strings"
)

type sourceArg struct {
    Path  string
    Depth int
}

type sourceArgs []sourceArg

func (s *sourceArgs) Set(val string) error {
    parts := strings.SplitN(val, ":", 2)
    if len(parts) != 2 {
        return errors.New("source must be in format file:depth")
    }
    depth, err := strconv.Atoi(parts[1])
    if err != nil || depth < 1 {
        return errors.New("invalid depth in source")
    }
    *s = append(*s, sourceArg{Path: parts[0], Depth: depth})
    return nil
}

func (s *sourceArgs) String() string {
    parts := make([]string, len(*s))
    for i, src := range *s {
        parts[i] = fmt.Sprintf("%s:%d", src.Path, src.Depth)
    }
    return strings.Join(parts, ", ")
}

type sepArgs []string

func (s *sepArgs) Set(val string) error {
    *s = append(*s, val)
    return nil
}
func (s *sepArgs) String() string {
    return strings.Join(*s, ",")
}

type permutator struct {
    allItems    []string
    srcOfItem   []int
    srcDepths   []int
    seps        []string
    prefix, suffix string
    noRepeats   bool
    output      func(string) // for testability
}

// Patch points for testability (must be defined at package level)
var (
    osOpen          = func(name string) (*os.File, error) { return os.Open(name) }
    bufioNewScanner = func(file *os.File) *bufio.Scanner { return bufio.NewScanner(file) }
)

func NewPermutatorFromFiles(sources []sourceArg, seps []string, prefix, suffix string, noRepeats bool, output func(string)) error {
    p := &permutator{
        seps:      seps,
        prefix:    prefix,
        suffix:    suffix,
        noRepeats: noRepeats,
        output:    output,
    }
    for srcIdx, src := range sources {
        file, err := osOpen(src.Path) // Use patch point
        if err != nil {
            return fmt.Errorf("ERROR opening %s: %v", src.Path, err)
        }
        scanner := bufioNewScanner(file) // Use patch point
        for scanner.Scan() {
            line := scanner.Text()
            if line == "" {
                continue
            }
            p.allItems = append(p.allItems, line)
            p.srcOfItem = append(p.srcOfItem, srcIdx)
        }
        file.Close()
        p.srcDepths = append(p.srcDepths, src.Depth)
    }
    p.generate()
    return nil
}

// This is the new function for testability
func RunPermutator(sources []sourceArg, seps []string, prefix, suffix string, noRepeats bool, output func(string)) error {
    return NewPermutatorFromFiles(sources, seps, prefix, suffix, noRepeats, output)
}

func (p *permutator) generate() {
    n := len(p.allItems)
    used := make([]bool, n)
    for i := 0; i < n; i++ {
        src := p.srcOfItem[i]
        maxDepth := p.srcDepths[src]
        p.dfs([]int{i}, used, maxDepth)
    }
}

func (p *permutator) dfs(path []int, used []bool, maxDepth int) {
    depth := len(path)
    last := path[depth-1]
    if p.noRepeats {
        used[last] = true
        defer func() { used[last] = false }()
    }
    if depth >= 1 && depth <= maxDepth {
        for _, sep := range p.seps {
            var b strings.Builder
            b.WriteString(p.prefix)
            for j, idx := range path {
                if j > 0 {
                    b.WriteString(sep)
                }
                b.WriteString(p.allItems[idx])
            }
            b.WriteString(p.suffix)
            if p.output != nil {
                p.output(b.String())
            } else {
                fmt.Println(b.String())
            }
        }
    }
    if depth == maxDepth {
        return
    }
    for next := 0; next < len(p.allItems); next++ {
        if p.noRepeats && used[next] {
            continue
        }
        p.dfs(append(path, next), used, maxDepth)
    }
}

// Efficiently calculate the number of permutations without generating them
func CountPermutationsFromFiles(sources []sourceArg, noRepeats bool) (int, error) {
    var allItems []string
    var srcOfItem []int
    var srcDepths []int

    for srcIdx, src := range sources {
        file, err := osOpen(src.Path)
        if err != nil {
            return 0, fmt.Errorf("ERROR opening %s: %v", src.Path, err)
        }
        scanner := bufioNewScanner(file)
        for scanner.Scan() {
            line := scanner.Text()
            if line == "" {
                continue
            }
            allItems = append(allItems, line)
            srcOfItem = append(srcOfItem, srcIdx)
        }
        file.Close()
        srcDepths = append(srcDepths, src.Depth)
    }

    // For each source, count how many items belong to it
    srcCounts := make([]int, len(sources))
    for _, srcIdx := range srcOfItem {
        srcCounts[srcIdx]++
    }

    // For each source, calculate the number of permutations for its depth
    total := 0
    for srcIdx, count := range srcCounts {
        depth := srcDepths[srcIdx]
        if count == 0 {
            continue
        }
        if noRepeats {
            // n!/(n-d)!
            if count < depth {
                continue
            }
            subtotal := 1
            for i := 0; i < depth; i++ {
                subtotal *= (count - i)
            }
            total += subtotal
        } else {
            // n^d
            subtotal := 1
            for i := 0; i < depth; i++ {
                subtotal *= count
            }
            total += subtotal
        }
    }
    return total, nil
}


// Add this function to your code:

// CountOutputLines runs the permutation logic and counts the number of output lines.
func CountOutputLines(sources []sourceArg, seps []string, prefix, suffix string, noRepeats bool) (int, error) {
    var count int
    err := RunPermutator(sources, seps, prefix, suffix, noRepeats, func(_ string) {
        count++
    })
    return count, err
}



func printUsage() {
    fmt.Println(`Usage: perms [options]
Options:
  -source file.txt:depth   Input file and depth (repeatable, required)
  -sep separator           Separator string (repeatable, default: "")
  -prefix string           Prefix string for each output
  -suffix string           Suffix string for each output
  -no-repeats              Use each word only once per sequence
  -count                   Print the number of generated permutations and exit
  -help                    Show this help message and exit`)
}

func main() {
    var sources sourceArgs
    flag.Var(&sources, "source", "input file and depth in format file.txt:3 (repeatable)")

    var seps sepArgs
    flag.Var(&seps, "sep", "separator string (can be specified multiple times)")

    var prefix, suffix string
    flag.StringVar(&prefix, "prefix", "", "prefix string")
    flag.StringVar(&suffix, "suffix", "", "suffix string")

    var noRepeats bool
    flag.BoolVar(&noRepeats, "no-repeats", false, "use each word only once per sequence")

    var countOnly bool
    flag.BoolVar(&countOnly, "count", false, "print the number of generated permutations and exit")

    var showHelp bool
    flag.BoolVar(&showHelp, "help", false, "show help message and exit")

    flag.Parse()

    if showHelp {
        printUsage()
        os.Exit(0)
    }

    if len(sources) == 0 {
        fmt.Fprintln(os.Stderr, "ERROR: at least one -source must be provided")
        printUsage()
        os.Exit(1)
    }
    if len(seps) == 0 {
        seps = append(seps, "")
    }

    // In your main(), replace the countOnly block with:
	if countOnly {
		count, err := CountOutputLines(sources, seps, prefix, suffix, noRepeats)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println(count)
		os.Exit(0)
	}

    err := RunPermutator(sources, seps, prefix, suffix, noRepeats, nil)
    if err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}