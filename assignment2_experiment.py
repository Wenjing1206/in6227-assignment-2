"""IN6227 Assignment 2: association-rule experiments / 关联规则实验。

中文：每个商品有缺席、前件、后件三种状态，排除空前件或空后件后，
候选规则数为 R(d)=3**d-2**(d+1)+1。逐规则扫描 n 笔交易得到 O(n*3**d)。
English: Three item states yield R(d)=3**d-2**(d+1)+1 ordered rules.
Scanning n transactions per rule costs O(n*3**d), assuming word-size masks.
默认参数对应所引用会话；旧版 experiment.py 的参数与测量保持独立。
Defaults follow the referenced conversation, independently of legacy experiment.py.
"""

# 中文：
# IN6227 Assignment 2 - Experiment for variable d
# 本实验固定 transaction 数量和 transaction length，只改变 unique items 数量 d。
# 对同一 simulated dataset 分别运行 brute-force association rule mining 和 Apriori，
# 测量 wall-clock runtime，并拟合 brute-force exponential model 做 extrapolation。
#
# English:
# IN6227 Assignment 2 - Experiment for variable d
# This experiment varies only the number of unique items d while holding the
# number of transactions and transaction length fixed.
# Brute-force and Apriori are run on the same simulated datasets.
# Wall-clock runtime is measured, and an exponential model is fitted to the
# brute-force measurements for extrapolation.

import argparse
import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import time
import math
import random
import numpy as np
import pandas as pd

from itertools import combinations

# ============================================================
# 1. Experiment settings
# ============================================================

N_TRANSACTIONS = 300
TRANSACTION_LENGTH = 4

MIN_SUPPORT = 0.05
MIN_CONFIDENCE = 0.50

D_VALUES = list(range(5, 19))

# 中文：如果 brute-force 一次运行超过这个时间，之后不再继续实际运行
# English: Stop further brute-force measurements once this threshold is exceeded
STOP_SECONDS = 15

RANDOM_SEED = 20261028

# ============================================================
# 2. Simulated transaction generator
# ============================================================


def generate_transactions(n, d, transaction_length=4, seed=20261028):
    """
    中文：
    生成 simulated transaction dataset。
    每笔 transaction 恰好包含 transaction_length 个不同的 items。

    English:
    Generate a simulated transaction dataset.
    Each transaction contains exactly transaction_length distinct items.
    """

    if n <= 0 or not 1 <= transaction_length <= d:
        raise ValueError("Require n > 0 and 1 <= transaction_length <= d.")
    rng = random.Random(seed)

    items = list(range(d))

    transactions_as_sets = []
    transactions_as_masks = []

    for _ in range(n):

        transaction = set(rng.sample(items, transaction_length))

        transactions_as_sets.append(transaction)

        # 中文：把 transaction 转换成 bit mask，方便 brute-force 快速做 subset test
        # English: Convert transaction to a bit mask for efficient subset tests

        mask = 0

        for item in transaction:
            mask |= 1 << item

        transactions_as_masks.append(mask)

    # 中文：确认 d 是实际出现的商品数，避免把未出现的商品计入自变量。
    # English: Verify that d equals the observed number of distinct items.
    observed = set().union(*transactions_as_sets)
    if len(observed) != d:
        raise ValueError("Generated data does not contain all d items; increase n.")
    return transactions_as_sets, transactions_as_masks


# ============================================================
# 3. Brute-force association rule mining
# ============================================================


def brute_force_mining(transaction_masks, d, min_support=0.05, min_confidence=0.50):
    """
    中文：
    枚举所有可能的 association rules。
    不使用 Apriori pruning。

    对每一个 rule：
        X -> Y

    扫描整个 transaction database，计算：
        support(X ∪ Y)
        support(X)
        confidence(X -> Y)

    English:
    Enumerate every possible association rule without pruning.

    For every rule X -> Y, scan the entire transaction database
    and calculate support and confidence.
    """

    n = len(transaction_masks)

    qualifying_rules = 0

    # s 表示 X ∪ Y
    for s in range(1, 1 << d):

        # Association rule 至少需要两个 items
        if s.bit_count() < 2:
            continue

        # 枚举 s 的所有 non-empty proper subsets 作为 antecedent X
        lhs = (s - 1) & s

        while lhs:

            rhs = s ^ lhs

            if rhs:

                union_count = 0
                lhs_count = 0

                # 中文：
                # 对每一个 candidate rule 扫描全部 transactions
                #
                # English:
                # Scan every transaction for every candidate rule

                for transaction in transaction_masks:

                    if (transaction & lhs) == lhs:

                        lhs_count += 1

                        if (transaction & rhs) == rhs:
                            union_count += 1

                support = union_count / n

                if lhs_count > 0:
                    confidence = union_count / lhs_count
                else:
                    confidence = 0

                if support >= min_support and confidence >= min_confidence:
                    qualifying_rules += 1

            # 获取下一个 subset
            lhs = (lhs - 1) & s

    return qualifying_rules


# ============================================================
# 4. Apriori
# ============================================================


def apriori_mining(transactions, d, min_support=0.05, min_confidence=0.50):
    """
    中文：
    使用 Apriori principle：
    如果一个 itemset 的任何 subset 不 frequent，
    那么这个 itemset 也不可能 frequent。

    English:
    Use the Apriori principle to prune candidate itemsets.
    """

    n = len(transactions)

    minimum_count = math.ceil(min_support * n - 1e-12)

    support_count = {}

    # --------------------------------------------------------
    # Frequent 1-itemsets
    # --------------------------------------------------------

    counts_1 = [0] * d

    for transaction in transactions:

        for item in transaction:
            counts_1[item] += 1

    previous_level = set()

    for item, count in enumerate(counts_1):

        if count >= minimum_count:

            itemset = frozenset([item])

            previous_level.add(itemset)

            support_count[itemset] = count

    all_frequent_itemsets = set(previous_level)

    k = 2

    # --------------------------------------------------------
    # Generate larger frequent itemsets
    # --------------------------------------------------------

    while previous_level:

        previous_list = list(previous_level)

        candidates = set()

        for i in range(len(previous_list)):

            for j in range(i + 1, len(previous_list)):

                candidate = previous_list[i] | previous_list[j]

                if len(candidate) != k:
                    continue

                # Apriori pruning
                all_subsets_frequent = all(
                    frozenset(subset) in previous_level
                    for subset in combinations(candidate, k - 1)
                )

                if all_subsets_frequent:
                    candidates.add(frozenset(candidate))

        if not candidates:
            break

        counts = {candidate: 0 for candidate in candidates}

        for transaction in transactions:

            for candidate in candidates:

                if candidate.issubset(transaction):
                    counts[candidate] += 1

        current_level = set()

        for candidate, count in counts.items():

            if count >= minimum_count:

                current_level.add(candidate)

                support_count[candidate] = count

        all_frequent_itemsets |= current_level

        previous_level = current_level

        k += 1

    # --------------------------------------------------------
    # Generate rules from frequent itemsets
    # --------------------------------------------------------

    qualifying_rules = 0

    for itemset in all_frequent_itemsets:

        if len(itemset) < 2:
            continue

        items = list(itemset)

        for size in range(1, len(items)):

            for lhs_tuple in combinations(items, size):

                lhs = frozenset(lhs_tuple)

                union_count = support_count[itemset]

                lhs_count = support_count.get(lhs, 0)

                if lhs_count == 0:
                    continue

                support = union_count / n

                confidence = union_count / lhs_count

                if support >= min_support and confidence >= min_confidence:
                    qualifying_rules += 1

    return qualifying_rules


def plot_results(df, df_n, output_dir):
    """中文：绘制两张四曲线图。English: Plot both four-curve figures."""
    # 中文：
    # Final plotting code for IN6227 Assignment 2
    # 两张图都包含老师要求的四条 curves。
    # Figure 1 额外明确标出 fitted region 与 extrapolated region。
    #
    # English:
    # Final plotting code for IN6227 Assignment 2.
    # Both figures contain the four required curves.
    # Figure 1 explicitly marks the transition from fitted to extrapolated region.

    import matplotlib.pyplot as plt

    # ============================================================
    # Figure 1 - Runtime vs Number of Unique Items d
    # ============================================================

    plt.figure(figsize=(7, 5))

    # ------------------------------------------------------------
    # 1. Theoretical estimate
    # ------------------------------------------------------------

    plt.plot(df["d"], df["theoretical_sec"], marker="o", label="Theoretical estimate")

    # ------------------------------------------------------------
    # 2. Measured brute-force
    # ------------------------------------------------------------

    plt.plot(
        df["d"],
        df["measured_brute_force_sec"],
        marker="o",
        linewidth=2,
        label="Measured brute-force",
    )

    # ------------------------------------------------------------
    # 3. Predicted brute-force
    # Split into fitted and extrapolated regions
    # ------------------------------------------------------------

    max_measured_d = int(df.loc[df["measured_brute_force_sec"].notna(), "d"].max())

    fitted_region = df[df["d"] <= max_measured_d]

    extrapolated_region = df[df["d"] >= max_measured_d]

    # 中文：
    # 拟合范围使用实线
    # English:
    # Use a solid line for the fitted region

    plt.plot(
        fitted_region["d"],
        fitted_region["predicted_brute_force_sec"],
        linewidth=2,
        color="tab:green",
        label="Predicted brute-force",
    )

    # 中文：
    # extrapolation 范围使用虚线
    # English:
    # Use a dashed line for the extrapolated region

    plt.plot(
        extrapolated_region["d"],
        extrapolated_region["predicted_brute_force_sec"],
        linestyle="--",
        linewidth=2,
        color="tab:green",
        label="_nolegend_",
    )

    # ------------------------------------------------------------
    # 4. Apriori
    # ------------------------------------------------------------

    plt.plot(
        df["d"],
        df["apriori_sec"],
        marker="o",
        linewidth=2,
        color="tab:purple",
        label="Apriori",
    )

    # ------------------------------------------------------------
    # Mark extrapolation boundary
    # ------------------------------------------------------------

    plt.axvline(x=max_measured_d, linestyle=":", linewidth=1.5)

    plt.text(
        max_measured_d + 0.15,
        0.97,
        "Extrapolated\n(dashed)",
        transform=plt.gca().get_xaxis_transform(),
        fontsize=9,
        va="top",
    )

    # ------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------

    # 中文：
    # runtime 跨越多个数量级，因此使用 log scale
    #
    # English:
    # Runtime spans several orders of magnitude,
    # so a logarithmic y-axis is appropriate.

    plt.yscale("log")

    plt.xlabel("Number of unique items (d)")
    plt.ylabel("Runtime (seconds)")
    plt.title("Runtime vs Number of Unique Items")

    plt.legend(fontsize=8)

    plt.grid(True, which="both", alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        output_dir / "runtime_vs_unique_items.png", dpi=300, bbox_inches="tight"
    )

    plt.close()

    # ============================================================
    # Figure 2 - Runtime vs Number of Transactions n
    # ============================================================

    plt.figure(figsize=(7, 5))

    # ------------------------------------------------------------
    # 1. Theoretical estimate
    # ------------------------------------------------------------

    plt.plot(
        df_n["n"], df_n["theoretical_sec"], marker="o", label="Theoretical estimate"
    )

    # ------------------------------------------------------------
    # 2. Measured brute-force
    # ------------------------------------------------------------

    plt.plot(
        df_n["n"],
        df_n["measured_brute_force_sec"],
        marker="o",
        linewidth=2,
        label="Measured brute-force",
    )

    # ------------------------------------------------------------
    # 3. Predicted brute-force
    # ------------------------------------------------------------

    plt.plot(
        df_n["n"],
        df_n["predicted_brute_force_sec"],
        linestyle="--",
        linewidth=2,
        color="tab:green",
        label="Predicted brute-force",
    )

    # ------------------------------------------------------------
    # 4. Apriori
    # ------------------------------------------------------------

    plt.plot(
        df_n["n"],
        df_n["apriori_sec"],
        marker="o",
        linewidth=2,
        color="tab:purple",
        label="Apriori",
    )

    # ------------------------------------------------------------
    # Formatting
    # ------------------------------------------------------------

    plt.xlabel("Number of transactions (n)")
    plt.ylabel("Runtime (seconds)")
    plt.title("Runtime vs Number of Transactions")

    plt.legend(fontsize=8)

    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        output_dir / "runtime_vs_transactions.png", dpi=300, bbox_inches="tight"
    )

    plt.close()


def main():
    """中文：运行两组实验并生成结果。English: Run both sweeps and save outputs."""
    parser = argparse.ArgumentParser(description="IN6227 Assignment 2 experiments")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "outputs/assignment2",
    )
    parser.add_argument(
        "--stop-seconds",
        type=float,
        default=STOP_SECONDS,
        help="Stop later d-sweep BF runs after a completed run exceeds this value.",
    )
    args = parser.parse_args()
    if args.stop_seconds <= 0:
        parser.error("--stop-seconds must be positive")
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    stop_seconds = args.stop_seconds

    # ============================================================
    # 5. Run d experiment
    # ============================================================

    results = []

    brute_force_active = True

    for d in D_VALUES:

        print(f"Running d = {d}")

        transactions, transaction_masks = generate_transactions(
            n=N_TRANSACTIONS,
            d=d,
            transaction_length=TRANSACTION_LENGTH,
            seed=RANDOM_SEED + d,
        )

        # --------------------------------------------------------
        # Brute-force runtime
        # --------------------------------------------------------

        brute_force_runtime = np.nan

        brute_force_rules = None

        if brute_force_active:

            start = time.perf_counter()

            brute_force_rules = brute_force_mining(
                transaction_masks, d, MIN_SUPPORT, MIN_CONFIDENCE
            )

            brute_force_runtime = time.perf_counter() - start

            print("  brute-force:", round(brute_force_runtime, 6), "seconds")

            # 中文：
            # 当前 point 保留，但之后停止继续运行 brute-force
            #
            # English:
            # Keep this measured point but stop later brute-force runs

            if brute_force_runtime > stop_seconds and len(results) >= 1:

                brute_force_active = False

                print("  Brute-force is now considered impractical.")

        # --------------------------------------------------------
        # Apriori runtime
        # --------------------------------------------------------

        start = time.perf_counter()

        apriori_rules = apriori_mining(transactions, d, MIN_SUPPORT, MIN_CONFIDENCE)

        apriori_runtime = time.perf_counter() - start

        print("  Apriori:", round(apriori_runtime, 6), "seconds")

        # 中文：
        # 在仍然运行 brute-force 的范围内，
        # 两种算法应该找到相同数量的 qualifying rules
        #
        # English:
        # Both algorithms should return the same number of qualifying rules

        if brute_force_rules is not None:

            assert brute_force_rules == apriori_rules

        results.append(
            {
                "brute_force_rules": brute_force_rules,
                "apriori_rules": apriori_rules,
                "d": d,
                "measured_brute_force_sec": brute_force_runtime,
                "apriori_sec": apriori_runtime,
            }
        )

    # ============================================================
    # 6. Convert to DataFrame
    # ============================================================

    df = pd.DataFrame(results)

    # ============================================================
    # 7. Theoretical estimate
    # ============================================================

    measured = df[df["measured_brute_force_sec"].notna()].copy()

    # 中文：
    # 用第一个 small measured point calibration constant C
    #
    # English:
    # Calibrate C using the first small measured brute-force point

    calibration_d = int(measured.iloc[0]["d"])

    calibration_time = float(measured.iloc[0]["measured_brute_force_sec"])

    # Theory:
    # T(d) = C * 3^d

    C = calibration_time / (3**calibration_d)

    df["theoretical_sec"] = C * (3 ** df["d"])

    # ============================================================
    # 8. Fit measured brute-force runtime
    # ============================================================

    # Model:
    #
    # T(d) = a * b^d
    #
    # Taking log:
    #
    # log T = log a + d log b

    x = measured["d"].to_numpy()

    y = np.log(measured["measured_brute_force_sec"].to_numpy())

    beta, alpha = np.polyfit(x, y, 1)

    a = np.exp(alpha)

    b = np.exp(beta)

    df["predicted_brute_force_sec"] = a * (b ** df["d"])

    # ============================================================
    # 9. Mark fitted vs extrapolated
    # ============================================================

    largest_measured_d = int(measured["d"].max())

    df["prediction_region"] = np.where(
        df["d"] <= largest_measured_d, "fitted", "extrapolated"
    )

    # ============================================================
    # 10. Final runtime table
    # ============================================================

    output_columns = [
        "d",
        "theoretical_sec",
        "measured_brute_force_sec",
        "predicted_brute_force_sec",
        "apriori_sec",
        "prediction_region",
    ]

    print("\nFinal runtime table:\n")

    print(df[output_columns].round(6))

    print("\nFitted brute-force model:")

    print(f"T(d) = {a:.8f} * ({b:.4f})^d")

    print("\nTheoretical model:")

    print(f"T(d) = {C:.8f} * 3^d")

    # 中文：
    # Experiment 2 - Number of transactions n
    # 固定 unique items d，只改变 transaction 数量 n。
    # 每个实验重复三次并取 median runtime，以降低偶然 timing noise。
    #
    # English:
    # Experiment 2 - Number of transactions n
    # Hold d fixed and vary only the number of transactions n.
    # Repeat each measurement three times and use the median runtime.

    import statistics

    FIXED_D = 9

    N_VALUES = [100, 200, 400, 800, 1600, 3200]

    REPEATS = 3

    n_results = []

    # ============================================================
    # Warm-up
    # ============================================================

    warm_transactions, warm_masks = generate_transactions(
        n=50, d=FIXED_D, transaction_length=TRANSACTION_LENGTH, seed=123
    )

    brute_force_mining(warm_masks, FIXED_D, MIN_SUPPORT, MIN_CONFIDENCE)

    apriori_mining(warm_transactions, FIXED_D, MIN_SUPPORT, MIN_CONFIDENCE)

    # ============================================================
    # Run experiment
    # ============================================================

    for n in N_VALUES:

        print(f"Running n = {n}")

        transactions, transaction_masks = generate_transactions(
            n=n, d=FIXED_D, transaction_length=TRANSACTION_LENGTH, seed=RANDOM_SEED + n
        )

        brute_force_times = []
        apriori_times = []

        brute_force_rules = None
        apriori_rules = None

        for repeat in range(REPEATS):

            # ----------------------------------------------------
            # Brute-force
            # ----------------------------------------------------

            start = time.perf_counter()

            brute_force_rules = brute_force_mining(
                transaction_masks, FIXED_D, MIN_SUPPORT, MIN_CONFIDENCE
            )

            brute_force_times.append(time.perf_counter() - start)

            # ----------------------------------------------------
            # Apriori
            # ----------------------------------------------------

            start = time.perf_counter()

            apriori_rules = apriori_mining(
                transactions, FIXED_D, MIN_SUPPORT, MIN_CONFIDENCE
            )

            apriori_times.append(time.perf_counter() - start)

        # 中文：
        # 检查两个算法最终得到相同数量的 qualifying rules。
        #
        # English:
        # Confirm both algorithms return the same number of qualifying rules.

        assert brute_force_rules == apriori_rules

        brute_force_runtime = statistics.median(brute_force_times)

        apriori_runtime = statistics.median(apriori_times)

        n_results.append(
            {
                "brute_force_rules": brute_force_rules,
                "apriori_rules": apriori_rules,
                "brute_force_readings": brute_force_times,
                "apriori_readings": apriori_times,
                "n": n,
                "measured_brute_force_sec": brute_force_runtime,
                "apriori_sec": apriori_runtime,
            }
        )

    # ============================================================
    # Convert to DataFrame
    # ============================================================

    df_n = pd.DataFrame(n_results)

    # ============================================================
    # Theoretical curve
    # T(n) = Cn
    # ============================================================

    calibration_n = float(df_n.iloc[0]["n"])

    calibration_time = float(df_n.iloc[0]["measured_brute_force_sec"])

    C_n = calibration_time / calibration_n

    df_n["theoretical_sec"] = C_n * df_n["n"]

    # ============================================================
    # Fit T(n) = c*n
    # ============================================================

    x = df_n["n"].to_numpy(dtype=float)

    y = df_n["measured_brute_force_sec"].to_numpy(dtype=float)

    # 中文：
    # 由于理论模型是 O(n)，这里拟合 through-origin linear model。
    #
    # English:
    # Since the theoretical model is O(n), fit a linear model
    # through the origin.

    c_fit = np.dot(x, y) / np.dot(x, x)

    df_n["predicted_brute_force_sec"] = c_fit * df_n["n"]

    # ============================================================
    # Compare brute-force with Apriori
    # ============================================================

    df_n["brute_force_apriori_ratio"] = (
        df_n["measured_brute_force_sec"] / df_n["apriori_sec"]
    )

    # ============================================================
    # Print results
    # ============================================================

    print(df_n.round(6))

    print("\nTheoretical model:")

    print(f"T(n) = {C_n:.8f} * n")

    print("\nFitted brute-force model:")

    print(f"T(n) = {c_fit:.8f} * n")

    plot_results(df, df_n, output_dir)

    # 中文：保存真实测量、模型和配置；未测暴力法值在 JSON 中写为 null。
    # English: Save measurements, fitted models and settings; missing BF values use null.
    df_n["prediction_region"] = "fitted"
    df.to_csv(output_dir / "runtime_vs_unique_items.csv", index=False)
    df_n.to_csv(output_dir / "runtime_vs_transactions.csv", index=False)
    output = {
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
        },
        "settings": {
            "n_transactions_for_d": N_TRANSACTIONS,
            "fixed_d_for_n": FIXED_D,
            "transaction_length": TRANSACTION_LENGTH,
            "min_support": MIN_SUPPORT,
            "min_confidence": MIN_CONFIDENCE,
            "d_values": D_VALUES,
            "n_values": N_VALUES,
            "random_seed": RANDOM_SEED,
            "stop_seconds": stop_seconds,
            "d_repeats": 1,
            "n_repeats": REPEATS,
        },
        "models": {
            "d_theory": {"C": C, "form": "C * 3**d"},
            "d_prediction": {
                "a": float(a),
                "b": float(b),
                "form": "a * b**d",
                "largest_measured_d": largest_measured_d,
            },
            "n_theory": {"C": C_n, "form": "C * n"},
            "n_prediction": {"c": float(c_fit), "form": "c * n"},
        },
        "d_rows": json.loads(df.to_json(orient="records", double_precision=15)),
        "n_rows": json.loads(df_n.to_json(orient="records", double_precision=15)),
    }
    (output_dir / "results.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    print(f"Results and figures saved to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
