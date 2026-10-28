# IN6227 Assignment 2: Association Rule Mining

This experiment compares exhaustive brute-force association rule mining with Apriori using synthetic transaction datasets. It varies transaction count `n` and distinct item count `d`, keeping basket size at four, minimum support at 0.04 and minimum confidence at 0.50.

For every rule, each item is absent, in its antecedent, or in its consequent. Excluding empty sides gives `R(d) = 3^d - 2^(d+1) + 1`. The implementation scans all transactions for each candidate, giving `O(n * 3^d)` under the fixed-word mask assumption.

## Run

Requires Python 3 and the dependency listed in `requirements.txt`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python experiment.py
```

The full experiment can take several minutes. It saves fresh measurements and fitted models to `data/results-new.json`, leaving the original results untouched. Timings depend on hardware and system load. Apriori timings are the median of five runs; brute-force timings are the median of the fastest three of seven. Matching rule counts are checked for every completed brute-force case.

`data/results-original.json` contains the measurements used in the report (Apple M3, macOS). Brute-force times are measured only for `n <= 10,000` and `d <= 12`; the fitted models estimate larger cases. Counts matching is a useful check but does not prove the rule sets are identical. As `d` increases while basket size remains fixed, the synthetic data becomes sparser, so the comparison should not be generalized to all datasets.
