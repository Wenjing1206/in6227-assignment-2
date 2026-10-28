# IN6227 Assignment 2: submission with support 0.04

This folder documents the one-page report comparing exhaustive brute-force association-rule mining with efficient-apriori 2.0.6. It uses **minimum support 0.04**, minimum confidence 0.50, and four-item simulated transactions. The separate root `assignment2_experiment.py` uses 0.05 and is a different experiment.

- [Experiment code for this report](../experiment.py)
- [Saved measurement data for this report](data/results-original.json)
- [One-page report builder](build_report.py)

中文：本报告使用的是 0.04 实验。数据文件保留原始多次计时、实测规则数量和拟合系数；未测量的暴力法点没有计时值。规则数量一致不等于规则集合已逐条验证。

The experiment uses seeded synthetic transactions. For each measured point, Apriori is the median of five runs and brute-force the median of the fastest three of seven, a policy biased toward faster timings. Brute-force was measured to n=10,000 and d=12; larger points are model extrapolations. Each algorithm uses the same dataset at a given point.

## Reproduce / 复现

From the repository root, with Python 3.10+:

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python experiment.py
```

This runs fresh measurements and writes `data/results-new.json`; measured times and fitted coefficients will vary across systems. The original results used in the report remain unchanged.

To build the linked one-page PDF, install DejaVu Sans and run `python submission-004/build_report.py`. It reads the preserved `submission-004/data/results-original.json` and writes to `submission-004/output/`. The saved results are identical to the repository's `data/results-original.json`.
