# Differential Equations — Interactive Notebook

Interactive explorers built while working through the MIT differential equations
sequence (OCW / MITx 18.03), gathered into one browsable site.

**Live site:** https://shammun.github.io/differential-equations-interactive/

| Course | Status |
| --- | --- |
| 1 · Introduction to Differential Equations | Completed |
| 2 · 2×2 Systems | In progress |
| 3 · Linear Algebra and N×N Systems | Upcoming |
| 4 · Fourier Series and Partial Differential Equations | Upcoming |

## Adding new interactives

Save the `.html` file anywhere inside its unit folder in the course directory, then
from this folder:

```
python build.py
git add -A
git commit -m "Add new interactives"
git push
```

`build.py` rescans the four course folders, copies every interactive into
`explorers/` and regenerates `data.js`, which `index.html` uses to draw the
catalogue. Course status (completed / ongoing / upcoming) is set at the top of
`build.py`.
