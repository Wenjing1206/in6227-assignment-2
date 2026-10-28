# IN6227 Assignment 2: Complete Python Experiment

中文：`assignment2_experiment.py` 整合所引用会话中已完成的完整实验，保留中英文注释：模拟交易生成（simulated transaction generator）、无剪枝暴力法（brute-force miner）、自写 Apriori、d/n 两组控制实验、理论估计（theoretical estimate）、拟合与外推（fitting/extrapolation），以及两张四曲线图（four-curve figures）。

English: The complete script consolidates the referenced conversation, including both miners, controlled sweeps, theoretical calibration, fitting/extrapolation, and plotting.

## Run / 运行

Requires Python 3.10+:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python assignment2_experiment.py
```

Optional output directory and practical stopping threshold:

```bash
python assignment2_experiment.py --output-dir outputs/assignment2 --stop-seconds 15
```

## Latest experiment settings / 最新实验参数

- Fixed basket size: 4 distinct items; minimum support: **0.05**; minimum confidence: **0.50**; base seed: **20261028**.
- **d experiment:** n=300, d=5..18, one timed run per algorithm at each point. After a completed brute-force run exceeds 15 seconds, retain that point and skip subsequent brute-force runs. At least two points are measured to fit the model. Apriori runs at every d.
- **n experiment:** d=9, n=[100, 200, 400, 800, 1600, 3200]; warm-up followed by three repetitions per algorithm, reporting median wall-clock runtime.
- Both algorithms use the same generated dataset at each point. Data generation, fitting and plotting are outside the algorithm timers. Matching qualifying-rule **counts** are asserted at every completed brute-force point; this does not prove equality of full rule sets.

中文：15 秒是完成一次运行后判断是否停止后续测量的阈值，**不是**当前运行的硬超时。分界点和计时随硬件及系统负载变化。脚本重新计时，不把会话中的旧数字硬编码为新测量。

English: The 15-second threshold is checked after a run finishes, not an interrupting timeout. The measured boundary depends on the machine and system load.

## Outputs and models / 输出与模型

By default, outputs go to `outputs/assignment2/`:

- `runtime_vs_unique_items.csv` and `runtime_vs_transactions.csv`: measured times, theoretical estimates, predictions, rule counts, and fitted/extrapolated labels.
- `results.json`: configuration, environment, model coefficients, both tables, and raw repeat timings for the n experiment. Unmeasured brute-force values are null.
- `runtime_vs_unique_items.png` and `runtime_vs_transactions.png`: each contains four curve types: **Theoretical estimate**, **Measured brute-force**, **Predicted brute-force**, and **Apriori**.

For d, the theoretical curve is C*3^d, calibrated at the first measured point; the fitted model is a*b^d, fitted only to completed measurements in log space. The prediction uses a solid line in the fitted region and a dashed line after the last measured d, with a vertical boundary. The d figure uses a logarithmic y-axis.

For n, theory is C*n, calibrated at the first point; prediction is c*n, fitted by least squares through the origin. All n values are measured, so the prediction is labelled fitted throughout, without inventing an extrapolated region.

中文：候选规则数 R(d)=3^d-2^(d+1)+1；逐规则扫描全部 n 笔交易，固定字长掩码（word-size masks）假设下为 O(n*3^d)。固定 d 时为 O(n)，固定 n 时为 O(3^d)。固定四件商品的合成交易会在 d 增大时变稀疏，不能直接推广到所有真实数据。

## Legacy experiment / 原有实验

The existing `experiment.py`, `data/results-original.json`, and report remain as the earlier experiment using minimum support **0.04**. Their parameters, measurements and fitted coefficients should not be mixed with the latest script's **0.05** configuration.

### Original README / 原有说明

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
