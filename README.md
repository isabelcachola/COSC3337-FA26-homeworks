# COSC 3337 — Homework Repository

Everything you need for the homework assignments in this course. Clone it to your course VM and pull before starting each assignment.

```bash
git clone git@github.com:isabelcachola/COSC3337-FA26-homeworks.git
cd COSC3337-FA26-homeworks
```

## Repository layout

```
COSC3337-FA26-homeworks/
├── README.md               this file
├── final-project/          final project — handout and templates
│   ├── cosc3337_final_project.pdf   the project handout — read this first
│   ├── checkpoint1_proposal.pdf     Checkpoint 1 (team and proposal) template
│   ├── checkpoint2_design.pdf       Checkpoint 2 (database design) template
│   └── final_report.pdf             final report template
│                                    (each PDF has a matching .tex source)
└── HW1/                    Homework 1 — relational algebra and SQL
    ├── hw1.pdf             the assignment handout — read this first
    ├── hw1_template.tex    LaTeX answer template for Part 1
    ├── hw1.sql             where you write your Part 2 SQL answers
    ├── setup_db.sh         one-time setup: loads the databases, grants you access
    ├── soundwave.sql       database dump, full dataset (loaded by setup_db.sh)
    ├── soundwave_small.sql database dump, small dataset (loaded by setup_db.sh)
    └── validate_submission.py   checks your hw1.sql before you submit
```

Later assignments will appear as `HW2/`, `HW3/`, and so on, each self-contained
in the same shape.


