"""将真实实验结果绘制为一页英文提交版 PDF。"""

import json
import math
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / "data/results-original.json").read_text(encoding="utf-8"))
OUTPUT = ROOT / "output/Wenjing_Tian_IN6227_Assignment_2_GitHub.pdf"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
W, H = landscape(A4)

# 使用可嵌入字体，确保数学符号和细小图中文字清晰。
FONT_DIR = next((p for p in [Path("/usr/share/fonts/truetype/dejavu"), Path("/Library/Fonts"), Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/Resources/fonts/truetype"] if (p / "DejaVuSans.ttf").exists()), None)
if FONT_DIR is None:
    raise FileNotFoundError("请安装 DejaVu Sans 字体后重新生成报告。")
pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")

NAVY = colors.HexColor("#12304A")
BLUE = colors.HexColor("#1975A5")
ORANGE = colors.HexColor("#C76324")
GRAY = colors.HexColor("#7D8790")
GRID = colors.HexColor("#E3E9ED")
INK = colors.HexColor("#202D36")
PALE = colors.HexColor("#FFF5EC")

c = canvas.Canvas(str(OUTPUT), pagesize=(W, H), pageCompression=1)
c.setTitle("IN6227-2026-Assignment-2 - Wenjing Tian")
c.setAuthor("Wenjing Tian")


def label(text, x, y, size=8.3, bold=False, color=INK):
    """绘制统一样式的单行文字。"""
    c.setFillColor(color)
    c.setFont("DejaVu-Bold" if bold else "DejaVu", size)
    c.drawString(x, y, text)


def para(html, x, top, width, size=8.1, leading=11.6):
    """按固定宽度排版段落，返回段落底部坐标以便检查空间。"""
    style = ParagraphStyle(
        "body", fontName="DejaVu", fontSize=size, leading=leading,
        textColor=INK, alignment=TA_LEFT, spaceAfter=0,
    )
    p = Paragraph(html, style)
    _, height = p.wrap(width, H)
    p.drawOn(c, x, top - height)
    return top - height


def dotted_polyline(points, dash=(3, 2), width=1.65, color=ORANGE):
    """虚线绘制外推区，和实测区明显区分。"""
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.setDash(*dash)
    path = c.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    c.drawPath(path)
    c.setDash()


def polyline(points, width, color):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    path = c.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    c.drawPath(path)


def plot_panel(x, title, rows, x_key, x_min, x_max, boundary, y_min, y_max,
               theory, prediction, xticks, x_log=False):
    """绘制同一坐标系中的四种曲线及拟合/外推分界。"""
    panel_w = 382
    c.setStrokeColor(GRID)
    c.setLineWidth(0.7)
    c.roundRect(x, 234, panel_w, 215, 7, stroke=1, fill=0)
    label(title, x + 13, 433, 9.2, True, NAVY)

    # 图例：理论、暴力实测、预测、Apriori 四条曲线。
    legend_y = 417
    legend = [
        ("Theory", GRAY, "dash"),
        ("Brute measured", INK, "dot"),
        ("Brute predicted", ORANGE, "solid"),
        ("Apriori", BLUE, "square"),
    ]
    starts = [x + 13, x + 97, x + 207, x + 313]
    for start, (name, color, kind) in zip(starts, legend):
        c.setStrokeColor(color)
        c.setFillColor(color)
        c.setLineWidth(1.5)
        if kind == "dash":
            c.setDash(3, 2)
            c.line(start, legend_y + 2, start + 13, legend_y + 2)
            c.setDash()
        elif kind == "dot":
            c.circle(start + 6, legend_y + 2, 2, stroke=0, fill=1)
        elif kind == "square":
            c.rect(start + 4, legend_y, 4, 4, stroke=0, fill=1)
        else:
            c.line(start, legend_y + 2, start + 13, legend_y + 2)
        label(name, start + 17, legend_y, 6.7, color=INK)

    px0, px1 = x + 49, x + 365
    py0, py1 = 267, 402

    def px(value):
        if x_log:
            return px0 + (math.log(value) - math.log(x_min)) / (math.log(x_max) - math.log(x_min)) * (px1 - px0)
        return px0 + (value - x_min) / (x_max - x_min) * (px1 - px0)

    def py(value):
        return py0 + (math.log10(value) - math.log10(y_min)) / (math.log10(y_max) - math.log10(y_min)) * (py1 - py0)

    # 浅色区域和竖线明确标记外推起点。
    bx = px(boundary)
    c.setFillColor(PALE)
    c.rect(bx, py0, px1 - bx, py1 - py0, stroke=0, fill=1)
    c.setStrokeColor(colors.HexColor("#DDAF87"))
    c.setDash(2, 2)
    c.line(bx, py0, bx, py1)
    c.setDash()
    label("extrapolated", min(bx + 5, px1 - 59), py1 - 10, 6.3, color=ORANGE)

    # 对数 y 轴网格和标签。
    power_min, power_max = round(math.log10(y_min)), round(math.log10(y_max))
    for power in range(power_min, power_max + 1):
        value = 10 ** power
        y = py(value)
        c.setStrokeColor(GRID)
        c.setLineWidth(0.5)
        c.line(px0, y, px1, y)
        c.setFont("DejaVu", 6.3)
        c.setFillColor(GRAY)
        c.drawRightString(px0 - 5, y - 2.5, f"10^{power}")
    for value, tick_label in xticks:
        tx = px(value)
        c.setStrokeColor(GRID)
        c.setLineWidth(0.4)
        c.line(tx, py0, tx, py1)
        c.setFont("DejaVu", 6.5)
        c.setFillColor(GRAY)
        c.drawCentredString(tx, py0 - 12, tick_label)
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.7)
    c.line(px0, py0, px1, py0)
    c.line(px0, py0, px0, py1)
    label("seconds (log)", px0, py1 + 3, 6.3, color=GRAY)

    # 理论线由一个小规模实测点校准；预测线拟合全部已完成的暴力法点。
    dense = [
        math.exp(math.log(x_min) + i / 100 * (math.log(x_max) - math.log(x_min)))
        if x_log else x_min + i / 100 * (x_max - x_min)
        for i in range(101)
    ]
    theory_points = [(px(v), py(theory(v))) for v in dense]
    c.setStrokeColor(GRAY)
    c.setLineWidth(1.0)
    c.setDash(4, 3)
    polyline(theory_points, 1.0, GRAY)
    c.setDash()
    fitted_values = [v for v in dense if v < boundary] + [boundary]
    extrap_values = [boundary] + [v for v in dense if v > boundary]
    polyline([(px(v), py(prediction(v))) for v in fitted_values], 1.7, ORANGE)
    dotted_polyline([(px(v), py(prediction(v))) for v in extrap_values])

    # Apriori 用完整 x 范围的真实实测点；暴力法只画完成的点。
    apriori_points = [(px(row[x_key]), py(row["apriori_seconds"])) for row in rows]
    polyline(apriori_points, 1.35, BLUE)
    for point in apriori_points:
        c.setFillColor(BLUE)
        c.rect(point[0] - 1.7, point[1] - 1.7, 3.4, 3.4, stroke=0, fill=1)
    for row in rows:
        if "brute_seconds" in row:
            c.setFillColor(INK)
            c.circle(px(row[x_key]), py(row["brute_seconds"]), 2.25, stroke=0, fill=1)

    axis_label = "Transactions n (log x)" if x_key == "n" else "Distinct items d"
    c.setFont("DejaVu", 7.1)
    c.setFillColor(INK)
    c.drawCentredString((px0 + px1) / 2, 242, axis_label)


# 页眉和研究方法。
label("IN6227-2026-Assignment-2", 28, 566, 8.5, True, BLUE)
label("Brute-force association rules: dataset size versus search space", 28, 545, 15.0, True, NAVY)
c.setFont("DejaVu", 8.4)
c.setFillColor(NAVY)
c.drawRightString(W - 28, 566, "Wenjing Tian  |  G2609709D")
c.setStrokeColor(GRID)
c.setLineWidth(1)
c.line(28, 535, W - 28, 535)

label("STEP 1 | VARIABLES AND COMPLEXITY", 28, 522, 7.8, True, BLUE)
para(
    "Let <b>n</b> be the number of transactions and <b>d</b> the number of distinct items observed. "
    "Each item is absent, in antecedent A, or in consequent B. Every disjoint A → B maps to one "
    "assignment, so enumeration is complete and unique. Excluding empty sides gives "
    "<b>R(d)=3<super>d</super>-2<super>d+1</super>+1</b> rules. Scanning n transactions per rule gives "
    "<b>O(n3<super>d</super>)</b> with constant-time word-size masks: <b>O(n)</b> for fixed d and "
    "<b>O(3<super>d</super>)</b> for fixed n.",
    28, 511, 381, size=8.0, leading=11.4,
)
label("STEP 2 | CONTROLLED EXPERIMENT", 433, 522, 7.8, True, BLUE)
para(
    "Simulated uniform four-item baskets; seeds 6227+n or 16227+d. Vary n with d=9, or d with n=300; "
    "basket size, min support 0.04 and min confidence 0.50 remain fixed. Same data for both methods; "
    "Apple M3, algorithm-only wall-clock time. Apriori (efficient-apriori 2.0.6): median of 5 runs; "
    "brute force: median of fastest 3 of 7 (biased toward fast runs). Rule counts agree at all "
    "16 measured points; matching counts do not prove identical rules.",
    433, 511, 381, size=8.0, leading=11.4,
)

n_rows = DATA["n_rows"]
d_rows = DATA["d_rows"]
n_cal = n_rows[0]["brute_seconds"] / n_rows[0]["n"]
d_cal = d_rows[0]["brute_seconds"] / 3 ** d_rows[0]["d"]
n_coeff = math.exp(DATA["n_fit"]["intercept"])
n_exp = DATA["n_fit"]["exponent"]
d_coeff = math.exp(DATA["d_fit"]["intercept"])
d_base = DATA["d_fit"]["base"]

plot_panel(
    28, "A. Transaction count n | d = 9", n_rows, "n", 100, 50000, 10000,
    1e-3, 1e2, lambda n: n_cal * n, lambda n: n_coeff * n ** n_exp,
    [(100, "100"), (1000, "1k"), (10000, "10k"), (50000, "50k")], True,
)
plot_panel(
    433, "B. Distinct items d | n = 300", d_rows, "d", 6, 16, 12,
    1e-3, 1e3, lambda d: d_cal * 3 ** d, lambda d: d_coeff * d_base ** d,
    [(6, "6"), (8, "8"), (10, "10"), (12, "12"), (14, "14"), (16, "16")], False,
)

# 两栏总结分别回应理论吻合度、不可实践阈值以及 Apriori 差距。
label("STEP 3 | REFLECTION ON n", 28, 217, 8.0, True, BLUE)
para(
    f"Theory calibrated at the <b>n=100</b> brute point: <b>t={n_cal:.2e} &times; n</b> s. "
    f"The log-log fit to n=100-10,000 is <b>t={n_coeff:.2e} &times; n<super>{n_exp:.3f}</super></b> s: "
    "its exponent is close to 1, consistent with linear growth in this range. Measured brute time rises "
    "from 0.0648 s to 6.22 s. With a chosen 10 s/run limit, the fitted model predicts a crossing near "
    "<b>n=16,400</b> and 30.3 s at n=50,000; both are extrapolations. Across measured points, "
    "brute force is about <b>51-142 times</b> slower than Apriori. The gap fluctuates without a "
    "clear monotonic trend; timing noise and changing simulated samples may contribute.",
    28, 205, 381, size=8.6, leading=13.5,
)

label("STEP 3 | REFLECTION ON d", 433, 217, 8.0, True, BLUE)
para(
    f"Theory calibrated at the <b>d=6</b> brute point: <b>t={d_cal:.2e} &times; 3<super>d</super></b> s. "
    f"The log-linear fit to d=6-12 is <b>t={d_coeff:.2e} &times; ({d_base:.3f})<super>d</super></b> s: "
    "the fitted base is close to 3, consistent with exponential growth. Loop overhead and itemset hit "
    "rates may explain deviations. Measured brute time rises from 0.00678 s to 5.40 s; with a chosen "
    "10 s/run limit, the model predicts 15.5 s at <b>d=13</b> and 448 s at d=16; neither is measured. "
    "Apriori remains around 0.001-0.003 s, while the measured brute/Apriori ratio rises from "
    "about <b>7 to 3,578</b>. Baskets become sparser as d grows; for d ≥ 9 no rules meet the thresholds, "
    "which limits generalization to other data.",
    433, 205, 381, size=8.6, leading=13.5,
)

c.setStrokeColor(GRID)
c.line(28, 30, W - 28, 30)
# 中文：页脚链接指向与当前报告对应的实验代码及数据说明。
repo_url = "https://github.com/Wenjing1206/in6227-assignment-2/tree/main/submission-004"
label("Code and experiment data: " + repo_url, 28, 17, 6.7, color=BLUE)
c.linkURL(repo_url, (28, 13, W - 28, 26), relative=0)

c.showPage()
c.save()
print(OUTPUT)
