## Homework 4

### 1. Read the handout

`hw4.pdf` contains all the instructions for the assignment: the questions, the
point values, and the due date. Nothing in this README replaces it.

### 2. Get the homework and load the database

HW4 comes from my repository, which you named `upstream` in HW1. From your
`COSC3337-FA26-homeworks` directory:

```bash
git pull upstream main
cd HW4
```

(A plain `git pull` pulls from your own repository, which doesn't have HW4.)
Then, from inside the `HW4` directory, run this once:

```bash
bash setup_db.sh
```

This loads `soundwave_live`, a database with one table, `ticket_sale_wide`,
and installs the Python packages the tests need. Afterwards:

```bash
mysql soundwave_live
```

**`setup_db.sh` is also your repair command.** Re-run it at any time to restore
`ticket_sale_wide` to the original export. It also deletes any tables you
created in `soundwave_live`.

### 3. Part 1 — written

`hw4_template.tex` is an optional LaTeX template. Typesetting Part 1 in LaTeX
earns **5 bonus points**. You submit the PDF, not the `.tex` file.

### 4. Part 2 — SQL

| File | What it is | You... |
|---|---|---|
| `fd_checks.sql` | 2.1 | **edit and submit** |
| `fix.sql` | 2.2 | **edit and submit** |
| `normalize.sql` | 2.3 | **edit and submit** |
| `lossless_check.sql` | 2.4 | **edit and submit** |
| `soundwave_live.sql` | the export, loaded by `setup_db.sh` | don't edit |
| `tests/` | the tests | run |

Run a script with, for example:

```bash
mysql soundwave_live < fix.sql
```

### 5. Test your work

```bash
python3 -m pytest tests/ -v
```

The autograder runs these same tests on a **different copy of the data**, so
answers copied from your copy of the data will fail. Every test starts from
freshly loaded data, so the tests reload `soundwave_live`, and when they
finish it is restored from `soundwave_live.sql`. Any tables you created are
gone afterwards. Re-run your scripts if you want them back.

### 6. Submit

One zip file containing exactly:

1. `hw4.pdf` — Part 1
2. `fd_checks.sql`
3. `fix.sql`
4. `normalize.sql`
5. `lossless_check.sql`

Do not rename the four `.sql` files.
