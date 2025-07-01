package main

import (
	"bufio"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
	"sync"
	"math/big"
)

// --- Argument Types ---

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

// --- Patch points for testability (must be defined at package level) ---

var (
	osOpen          = func(name string) (*os.File, error) { return os.Open(name) }
	bufioNewScanner = func(file *os.File) *bufio.Scanner { return bufio.NewScanner(file) }
)

// --- Fast Permutator Implementation ---

type PermutatorFast struct {
	allItems    []string
	srcOfItem   []int
	srcDepths   []int
	seps        []string
	prefix      string
	suffix      string
	noRepeats   bool

	out *bufio.Writer
	mu  sync.Mutex // protects out

	pool sync.Pool // for *strings.Builder
}

func NewPermutatorFast(
	allItems []string, srcOfItem []int, srcDepths []int,
	seps []string, prefix, suffix string, noRepeats bool,
	writer io.Writer,
) *PermutatorFast {
	p := &PermutatorFast{
		allItems:  allItems,
		srcOfItem: srcOfItem,
		srcDepths: srcDepths,
		seps:      seps,
		prefix:    prefix,
		suffix:    suffix,
		noRepeats: noRepeats,
		out:       bufio.NewWriterSize(writer, 64*1024), // 64 KiB buffer
	}
	p.pool.New = func() any { return &strings.Builder{} }
	return p
}

func (p *PermutatorFast) writeLine(s string) {
	p.mu.Lock()
	p.out.WriteString(s)
	p.out.WriteByte('\n')
	p.mu.Unlock()
}

func (p *PermutatorFast) dfs(path []int, depth, maxDepth int, used []bool) {
	last := path[depth-1]

	if p.noRepeats {
		used[last] = true
		defer func() { used[last] = false }()
	}

	if depth >= 1 {
		for _, sep := range p.seps {
			builder := p.pool.Get().(*strings.Builder)
			builder.Reset()

			builder.WriteString(p.prefix)
			builder.WriteString(p.allItems[path[0]])
			for i := 1; i < depth; i++ {
				builder.WriteString(sep)
				builder.WriteString(p.allItems[path[i]])
			}
			builder.WriteString(p.suffix)

			p.writeLine(builder.String())
			p.pool.Put(builder)
		}
	}

	if depth == maxDepth {
		return
	}

	n := len(p.allItems)
	for next := 0; next < n; next++ {
		if p.noRepeats && used[next] {
			continue
		}
		path[depth] = next
		p.dfs(path, depth+1, maxDepth, used)
	}
}

func (p *PermutatorFast) Generate() {
	var wg sync.WaitGroup
	n := len(p.allItems)

	for i := 0; i < n; i++ {
		wg.Add(1)
		go func(start int) {
			defer wg.Done()

			maxDepth := p.srcDepths[p.srcOfItem[start]]
			path := make([]int, maxDepth)
			used := make([]bool, n)
			path[0] = start
			p.dfs(path, 1, maxDepth, used)
		}(i)
	}

	wg.Wait()
	p.out.Flush()
}

// --- Original Permutator (for testability/callbacks) ---

type permutator struct {
	allItems    []string
	srcOfItem   []int
	srcDepths   []int
	seps        []string
	prefix      string
	suffix      string
	noRepeats   bool
	output      func(string)
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

// --- Fast Permutator Entry Point ---

func RunPermutatorFast(sources []sourceArg, seps []string, prefix, suffix string, noRepeats bool, output func(string)) error {
	var allItems []string
	var srcOfItem []int
	var srcDepths []int

	for srcIdx, src := range sources {
		file, err := osOpen(src.Path)
		if err != nil {
			return fmt.Errorf("ERROR opening %s: %v", src.Path, err)
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

	if output != nil {
		p := &permutator{
			allItems:  allItems,
			srcOfItem: srcOfItem,
			srcDepths: srcDepths,
			seps:      seps,
			prefix:    prefix,
			suffix:    suffix,
			noRepeats: noRepeats,
			output:    output,
		}
		p.generate()
		return nil
	}

	fast := NewPermutatorFast(allItems, srcOfItem, srcDepths, seps, prefix, suffix, noRepeats, os.Stdout)
	fast.Generate()
	return nil
}

// --- Counting Logic (unchanged) ---

// CalculateOutputLines returns the number of output lines (permutations) as *big.Int
func CalculateOutputLines(sources []sourceArg, seps []string, noRepeats bool) (*big.Int, error) {
    // Gather all items and their source/depth
    var allItems []string
    var srcOfItem []int
    var srcDepths []int

    for srcIdx, src := range sources {
        f, err := osOpen(src.Path)
        if err != nil {
            return nil, fmt.Errorf("ERROR opening %s: %v", src.Path, err)
        }
        sc := bufioNewScanner(f)
        for sc.Scan() {
            txt := sc.Text()
            if txt == "" {
                continue
            }
            allItems = append(allItems, txt)
            srcOfItem = append(srcOfItem, srcIdx)
        }
        f.Close()
        srcDepths = append(srcDepths, src.Depth)
    }

    n := len(allItems)
    if n == 0 || len(seps) == 0 {
        return big.NewInt(0), nil
    }

    // Helper: nPr (order matters, no repeats)
    perm := func(n, r int) *big.Int {
        if r < 0 || n < 0 || n < r {
            return big.NewInt(0)
        }
        res := big.NewInt(1)
        for i := 0; i < r; i++ {
            res.Mul(res, big.NewInt(int64(n-i)))
        }
        return res
    }
    // Helper: base^exp (repeats allowed)
    pow := func(base, exp int) *big.Int {
        if exp < 0 || base < 0 {
            return big.NewInt(0)
        }
        res := big.NewInt(1)
        b := big.NewInt(int64(base))
        for i := 0; i < exp; i++ {
            res.Mul(res, b)
        }
        return res
    }

    total := big.NewInt(0)
    sepFactor := big.NewInt(int64(len(seps)))

    for i := 0; i < n; i++ {
        maxDepth := srcDepths[srcOfItem[i]]
        for l := 1; l <= maxDepth; l++ {
            var cnt *big.Int
            if noRepeats {
                // pick l-1 more items out of (n-1) without repetition
                cnt = perm(n-1, l-1)
            } else {
                // any of (n-1) items can occupy each of (l-1) positions
                cnt = pow(n-1, l-1)
            }
            cnt.Mul(cnt, sepFactor)
            total.Add(total, cnt)
        }
    }
    return total, nil
}


// --- CLI and Usage ---

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

	if countOnly {
		total, err := CalculateOutputLines(sources, seps, noRepeats)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println(total)
		os.Exit(0)
	}

	err := RunPermutatorFast(sources, seps, prefix, suffix, noRepeats, nil)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}