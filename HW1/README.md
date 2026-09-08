## Homework 1

### 1. Read the handout

`HW1/hw1.pdf` is contains all the instructions for the assignment, including the questions, the point values, and the
due date. Nothing in this README replaces it.

### 2. Load the databases

From inside the `HW1` directory, run this once:

```bash
bash setup_db.sh
```

That loads two databases and gives your account read-only access to both. When it finishes you can connect with no username and no password:

```bash
mysql soundwave
```

```bash
mysql soundwave_small
```

MySQL recognises you from your VM login, so there is nothing to memorise and nothing to lose. Your access is read-only, which means no query you write for this assignment can damage the data.

**`setup_db.sh` is also your repair command.** It is safe to run again at any time, and doing so restores both databases to a clean, known state. If anything ever looks wrong with the data, re-run it rather than trying to diagnose it.

### 3. Parts 0 and 1 — relational algebra

`hw1_template.tex` is an optional LaTeX template with the relational-algebra
macros already defined, so you never have to write `\sigma_{...}` by hand.
Typesetting Part 1 in LaTeX earns **5 bonus points**.

Upload it to Overleaf or run `pdflatex` locally, put your name in the `\student` command, and fill in your answers. **You submit the resulting PDF, not the `.tex` file.**

If you would rather not use LaTeX, write these parts up however the handout allows.

### 4. Part 2 — SQL

Write your answers in `hw1.sql`. The file has one marker per question, and your statement goes underneath it:

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

This confirms the grader can read your file: all eight answers present, each one a single well-formed statement. To also execute every query against the right database and confirm it runs:

```bash
python3 validate_submission.py hw1.sql --check-runs
```

The script uses the `mysql` client already on your VM.

**This checks format and not correctness.** A clean report means the grader can
parse your file, not that your answers are right. Run it anyway: a file that
cannot be parsed loses points that have nothing to do with SQL.