## Homework 3

### 1. Read the handout

`hw3.pdf` contains all the instructions for the assignment: the questions, the
point values, and the due date. Nothing in this README replaces it.

### 2. Get the homework and load the database

HW3 comes from my repository, which you named `upstream` in HW1. From your
`COSC3337-FA26-homeworks` directory:

```bash
git pull upstream main
cd HW3
```

(A plain `git pull` pulls from your own repository, which doesn't have HW3.)
Then, from inside the `HW3` directory, run this once:

```bash
bash setup_db.sh
```

This loads `soundwave_app` (the HW 1 catalog plus listeners, playlists and
plays) and installs the Python packages the starter code needs. Afterwards:

```bash
mysql soundwave_app
```

**`setup_db.sh` is also your repair command.** Re-run it at any time to restore
`soundwave_app` to a clean state.

### 3. Part 1 — written

`hw3_template.tex` is an optional LaTeX template. Typesetting Part 1 in LaTeX
earns **5 bonus points**. You submit the PDF, not the `.tex` file.

### 4. Part 2 — code

| File | What it is | You... |
|---|---|---|
| `app_queries.py` | 2.1 and 2.2 | **edit and submit** |
| `mapreduce_jobs.py` | 2.3 | **edit and submit** |
| `db.py` | `get_connection()` and `QueryCounter` | use, don't edit |
| `mapreduce_driver.py` | `run_mapreduce()` and `read_plays()` | use, don't edit |
| `data/plays.csv` | the `play` table, exported for 2.3 | read |
| `tests/` | public tests | run |

Do not rename functions or change their parameters: the autograder calls them
exactly as written.

### 5. Test your work

```bash
python3 -m pytest tests/ -v
```

The public tests are a subset of the autograder's tests. The autograder runs
more of them, on a **different copy of the data**, so passing every public
test is necessary but not sufficient. Test your own edge cases too.

Running the tests never changes your database. Any playlist a test creates is
deleted afterwards.

### 6. Submit

One zip file containing exactly:

1. `hw3.pdf` — Part 1
2. `app_queries.py`
3. `mapreduce_jobs.py`

Do not rename the two `.py` files.
