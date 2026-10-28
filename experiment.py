"""IN6227 Assignment 2：可复现实验与原始计时。"""

import json
import math
import random
import statistics
import time
import platform
from pathlib import Path

from efficient_apriori import apriori


def make_transactions(n: int, d: int, k: int, seed: int):
    """固定每笔交易的商品数 k，以控制交易结构。"""
    rng = random.Random(seed)
    transactions = [tuple(sorted(rng.sample(range(d), k))) for _ in range(n)]
    assert len({item for transaction in transactions for item in transaction}) == d
    masks = [sum(1 << item for item in transaction) for transaction in transactions]
    return transactions, masks


def brute_force(masks, d: int, min_support: float, min_confidence: float):
    """枚举全部非空且互不相交的规则 A→B，逐条扫描交易计算支持度与置信度。"""
    n = len(masks)
    accepted = 0
    candidates = 0
    for union in range(3, 1 << d):
        antecedent = (union - 1) & union
        while antecedent:
            consequent = union ^ antecedent
            if consequent:
                candidates += 1
                count_a = 0
                count_union = 0
                for transaction in masks:
                    if transaction & antecedent == antecedent:
                        count_a += 1
                        if transaction & union == union:
                            count_union += 1
                if count_a and count_union / n >= min_support and count_union / count_a >= min_confidence:
                    accepted += 1
            antecedent = (antecedent - 1) & union
    assert candidates == 3**d - 2 ** (d + 1) + 1
    return accepted, candidates


def timed(call, repeats=3, best_three=False):
    """使用墙钟时间；暴力法取七次中最快的三次中位数，减弱后台负载干扰。"""
    readings = []
    result = None
    for _ in range(repeats):
        start = time.perf_counter()
        result = call()
        readings.append(time.perf_counter() - start)
    selected = sorted(readings)[:3] if best_three else readings
    return statistics.median(selected), result, readings


def run_case(n, d, k, seed, min_support, min_confidence, measure_brute=True):
    transactions, masks = make_transactions(n, d, k, seed)
    apriori_time, apriori_result, apriori_readings = timed(
        lambda: apriori(transactions, min_support=min_support, min_confidence=min_confidence), 5
    )
    row = {
        "n": n, "d": d, "k": k, "seed": seed,
        "apriori_seconds": apriori_time,
        "apriori_readings": apriori_readings,
        "apriori_rules": len(apriori_result[1]),
    }
    if measure_brute:
        # 增加重复次数，选取低负载的三次运行来估计本机基准墙钟时间。
        brute_time, brute_result, brute_readings = timed(
            lambda: brute_force(masks, d, min_support, min_confidence),
            7,
            True,
        )
        row.update({
            "brute_seconds": brute_time,
            "brute_readings": brute_readings,
            "brute_rules": brute_result[0],
            "candidate_rules": brute_result[1],
        })
        assert row["brute_rules"] == row["apriori_rules"], row
    return row


def fit_log_line(points):
    """不用额外依赖，对 ln(time) 与变换后的 x 做最小二乘拟合。"""
    xs, ys = zip(*points)
    xbar, ybar = statistics.mean(xs), statistics.mean(ys)
    slope = sum((x - xbar) * (y - ybar) for x, y in points) / sum((x - xbar) ** 2 for x in xs)
    intercept = ybar - slope * xbar
    return intercept, slope


def main():
    k = 4
    min_support = 0.04
    min_confidence = 0.5
    n_values = [100, 200, 400, 800, 1200, 1800, 2400, 5000, 10000, 20000, 50000]
    d_values = list(range(6, 17))
    n_rows = []
    d_rows = []
    for n in n_values:
        row = run_case(n, 9, k, 6227 + n, min_support, min_confidence, measure_brute=n <= 10000)
        n_rows.append(row)
        print("n", n, row.get("brute_seconds"), row["apriori_seconds"], flush=True)
    for d in d_values:
        row = run_case(300, d, k, 16227 + d, min_support, min_confidence, measure_brute=d <= 12)
        d_rows.append(row)
        print("d", d, row.get("brute_seconds"), row["apriori_seconds"], flush=True)

    n_fit = fit_log_line([(math.log(r["n"]), math.log(r["brute_seconds"])) for r in n_rows if "brute_seconds" in r])
    d_measured = [r for r in d_rows if "brute_seconds" in r]
    d_fit = fit_log_line([(r["d"], math.log(r["brute_seconds"])) for r in d_measured])
    output = {
        "environment": f"{platform.platform()}; Python {platform.python_version()}; efficient-apriori 2.0.6; perf_counter wall-clock",
        "min_support": min_support,
        "min_confidence": min_confidence,
        "basket_size": k,
        "n_rows": n_rows,
        "d_rows": d_rows,
        "n_fit": {"intercept": n_fit[0], "exponent": n_fit[1]},
        "d_fit": {"intercept": d_fit[0], "log_base": d_fit[1], "base": math.exp(d_fit[1])},
    }
    output_path = Path(__file__).resolve().parent / "data/results-new.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("fits", output["n_fit"], output["d_fit"], flush=True)


if __name__ == "__main__":
    main()
