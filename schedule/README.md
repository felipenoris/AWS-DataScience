# Schedule report

An A4 PDF with the schedule of everything left in the plan, written in Portuguese as a deliverable for
the user.

The report's content is data inside [`build.py`](build.py): the blocks, their times, stages and owners
are Python literals. The script writes `out/report.html`, and headless Chrome prints it to
`out/schedule.pdf`. Edit the data, then render:

```bash
make schedule
```

The target reads nothing in AWS. `out/` is not tracked. `CHROME=` overrides the browser's path.
