# GO tools 

Performance based script are write in go.

### `permute` Tool

A better performance perms tool.

#### 📥 Installation

From your repo root (assuming module already initialized):

```bash
cd permute/; go build -o ../bin/ ; cd ..
```

> Binaries will end up in `../bin/permute` (or your `$GOBIN`).

---

### `perms` Tool
Source idea: https://github.com/tomnomnom/hacks/tree/master/perms

Generate cross‐list permutations up to per‐source depths, with optional separators, prefix/suffix, and no-repeat control.

#### 📥 Installation

From your repo root (assuming module already initialized):

```bash
cd perms/; go build -o ../bin/perms ; cd ..
```

> Binaries will end up in `../bin/perms` (or your `$GOBIN`).

---

#### ⚙️ Usage

```bash
perms \
  -source path/to/list1.txt:3 \
  -source path/to/list2.txt:2 \
  [-sep SEP]... \
  [-prefix PFX] \
  [-suffix SFX] \
  [-count] \
  [--no-repeats]
```

- `-source file.txt:DEPTH`  
  – **repeatable**. Load each file as one “list,” assign its max depth.  
  – E.g. `-source fruits.txt:3 -source colors.txt:2`.

- `-sep SEP`  
  – **repeatable**. Join terms with `SEP` (defaults to empty string).  

- `-prefix PFX` / `-suffix SFX`  
  – Strings to prepend/append on every permutation.

- `-no-repeats`  
  – Don’t reuse the same word twice in a sequence.

- `-count`
  - Print the number of generated permutations and exit

---

#### 🧩 Example

Given:

- `animals.txt`:
  ```
  cat
  dog
  ```
- `actions.txt`:
  ```
  jump
  run
  ```

Generate up to depth 2 on animals and depth 1 on actions, with a hyphen:

```bash
perms \
  -source animals.txt:2 \
  -source actions.txt:1 \
  -sep "-" \
  --no-repeats
```

**Output**:

```
cat
cat-jump
cat-run
dog
dog-jump
dog-run
jump
run
```

---
