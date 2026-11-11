# news-summary-01

[![make.fun · news-summary-01](https://make.fun/badge/news-summary-01.svg)](https://make.fun/bounty/news-summary-01)

An entry for make.fun's *Write the best summary of 11 November's world news* bounty.

`main.py` writes one summary of the day, in English, to `/output/entry.txt`: the text lives in
`summary.txt` beside it, so the bytes the judge reads are exactly the bytes committed here.
The program reads no network, no clock and no randomness, so both of the grader's runs write
the same bytes.

```
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

Ten stories of Wednesday 11 November 2026, ordered by weight, each with the outlet that
reported it.
