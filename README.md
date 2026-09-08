# COSC 3337 — Homework Repository

Everything you need for the homework assignments in this course. Clone it to
your course VM and pull before starting each assignment.

```bash
git clone git@github.com:isabelcachola/COSC3337-FA26-homeworks.git
cd COSC3337-FA26-homeworks
```

## Repository layout

```
COSC3337-FA26-homeworks/
├── README.md               this file
└── HW1/                    Homework 1 — relational algebra and SQL
    ├── hw1.pdf             the assignment handout — read this first
    ├── hw1_template.tex    LaTeX answer template for Parts 0 and 1
    ├── hw1.sql             where you write your Part 2 SQL answers
    ├── setup_db.sh         one-time setup: loads the databases, grants you access
    ├── soundwave.sql       database dump, full dataset (loaded by setup_db.sh)
    ├── soundwave_small.sql database dump, small dataset (loaded by setup_db.sh)
    ├── setup.sql           superseded — see "A note on setup.sql" below
    └── validate_submission.py   checks your hw1.sql before you submit
```

Later assignments will appear as `HW2/`, `HW3/`, and so on, each self-contained
in the same shape.

## Homework 1

### 1. Read the handout

`HW1/hw1.pdf` is the assignment itself: the questions, the point values, and the
due date. Nothing in this README replaces it — if the two ever disagree, the
handout wins.

### 2. Load the databases

From inside the `HW1` directory, run this once:

```bash
bash setup_db.sh
```

That loads two databases and gives your account read-only access to both. When
it finishes you can connect with no username and no password:

```bash
mysql soundwave
```

```bash
mysql soundwave_small
```

MySQL recognises you from your VM login, so there is nothing to memorise and
nothing to lose. Your access is read-only, which means no query you write for
this assignment can damage the data.

**`setup_db.sh` is also your repair command.** It is safe to run again at any
time, and doing so restores both databases to a clean, known-good state. If
anything ever looks wrong with the data, re-run it rather than trying to
diagnose it.

### 3. Parts 0 and 1 — relational algebra

`hw1_template.tex` is an optional LaTeX template with the relational-algebra
macros already defined, so you never have to write `\sigma_{...}` by hand.
Typesetting Part 1 in LaTeX earns **5 bonus points**.

Upload it to Overleaf or run `pdflatex` locally, put your name in the
`\student` command, and fill in your answers. **You submit the resulting PDF,
not the `.tex` file.**

If you would rather not use LaTeX, write these parts up however the handout
allows — the bonus points are the only thing you give up.

### 4. Part 2 — SQL

Write your answers in `hw1.sql`. The file has one marker per question, and your
statement goes underneath it:

```sql
-- Q1
SELECT ...
FROM ...;
```

Four rules the grader depends on:

- One marker per question, exactly as `-- Q1` through `-- Q8`, in order.
- Exactly **one** statement under each marker.
- Each statement ends with a semicolon, with nothing after it.
- Do not rename the file or change the marker format.

Each question is asked against a specific database, fixed by the handout:

| Questions | Database |
|-----------|-----------------|
| Q1 – Q5   | `soundwave`       |
| Q6 – Q8   | `soundwave_small` |

### 5. Check your work before submitting

```bash
python3 validate_submission.py hw1.sql
```

This confirms the grader can read your file: all eight answers present, each one
a single well-formed statement. To also execute every query against the right
database and confirm it runs:

```bash
python3 validate_submission.py hw1.sql --check-runs
```

No password is needed for either command, and no installation is required — it
uses the `mysql` client already on your VM.

**This checks format and not correctness.** A clean report means the grader can
parse your file, not that your answers are right. Run it anyway: a file that
cannot be parsed loses points that have nothing to do with SQL.

## A note on setup.sql

`HW1/setup.sql` is an earlier version of the setup step that created a separate
`soundwave_ro` account with a password. **You do not need it** — `setup_db.sh`
replaces it and requires no password at all. It is left here only so that
anyone who already followed the older instructions is not confused by its
disappearance. Ignore it.

## Getting help

If a command in this README fails, include in your question: the exact command
you ran, the full output, and whether `bash setup_db.sh` completed successfully.
That is almost always enough to identify the problem immediately.
