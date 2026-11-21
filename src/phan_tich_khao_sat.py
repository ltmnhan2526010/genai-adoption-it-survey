"""Phân tích dữ liệu khảo sát (mô phỏng) về việc dùng AI của nhân sự CNTT.

Sinh các hình dùng cho báo cáo LaTeX (YC1) và poster (YC2), đồng thời
xuất các con số thống kê vào figures/thong_ke.json.

Chạy:  python phan_tich_khao_sat.py <file.csv> [thu_muc_xuat]
  vd.  python src/phan_tich_khao_sat.py data/khao_sat_AI_CNTT.csv results/figures
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../../data/khao_sat_AI_CNTT.csv")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).with_name("figures")
OUT.mkdir(exist_ok=True)

LIKERT = {
    "Q8_TietKiemThoiGian": "Tiết kiệm thời gian",
    "Q9_TimKiemXuLyTT": "Tìm kiếm, xử lý TT",
    "Q10_PhoiHop": "Phối hợp nhóm",
    "Q11_GiamViecLapLai": "Giảm việc lặp lại",
    "Q12_KienThucKyNang": "Nâng cao kỹ năng",
}
USE_ORDER = ["Chưa từng sử dụng", "Đã thử nhưng ít sử dụng", "Thỉnh thoảng", "Thường xuyên"]
COLORS = ["#1f4e79", "#2e86c1", "#5dade2", "#aed6f1", "#f39c12", "#7f8c8d"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False})

df = pd.read_csv(CSV, encoding="utf-8-sig")
df["DiemLoiIch"] = df[list(LIKERT)].mean(axis=1)
df["MucDoDung"] = df["Q5_DungAI"].map({k: i for i, k in enumerate(USE_ORDER)})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=300)
    plt.close(fig)


# Hình 1: mức độ sử dụng AI (hình đơn)
cnt = df["Q5_DungAI"].value_counts().reindex(USE_ORDER, fill_value=0)
fig, ax = plt.subplots(figsize=(6.4, 3.2))
bars = ax.barh(cnt.index, cnt.values, color=COLORS[:4][::-1])
ax.bar_label(bars, labels=[f"{v} ({v / len(df):.0%})" for v in cnt.values], padding=3)
ax.set_xlabel("Số người trả lời (n = %d)" % len(df))
ax.set_xlim(0, cnt.max() * 1.3)
save(fig, "h1_muc_do_dung_ai")

# Cụm 4 hình
# (a) vai trò
fig, ax = plt.subplots(figsize=(4.2, 3.2))
role = df["Q1_VaiTro"].value_counts()
ax.bar(role.index, role.values, color=COLORS[1])
ax.set_ylabel("Số người")
ax.tick_params(axis="x", rotation=35)
plt.setp(ax.get_xticklabels(), ha="right")
save(fig, "h2a_vai_tro")

# (b) công cụ AI (câu hỏi nhiều lựa chọn)
tools = df["Q6_CongCuAI"].dropna().str.split(r",\s*").explode().value_counts()
fig, ax = plt.subplots(figsize=(4.2, 3.2))
ax.barh(tools.index[::-1], tools.values[::-1], color=COLORS[0])
ax.set_xlabel("Số lượt chọn")
save(fig, "h2b_cong_cu_ai")

# (c) điểm Likert trung bình
means = df[list(LIKERT)].mean().rename(LIKERT)
sds = df[list(LIKERT)].std().rename(LIKERT)
fig, ax = plt.subplots(figsize=(4.2, 3.2))
ax.barh(means.index[::-1], means.values[::-1], xerr=sds.values[::-1],
        color=COLORS[2], capsize=3)
ax.set_xlim(1, 5)
ax.set_xlabel("Điểm trung bình (thang 1–5)")
save(fig, "h2c_loi_ich_likert")

# (d) khó khăn
diff = df["Q13_KhoKhan"].value_counts()
fig, ax = plt.subplots(figsize=(4.2, 3.2))
b = ax.barh([s.replace(" và ", "\nvà ").replace("AI chưa", "AI\nchưa") for s in diff.index[::-1]],
            diff.values[::-1], color=COLORS[4])
ax.bar_label(b, labels=[f"{v / len(df):.0%}" for v in diff.values[::-1]], padding=3)
ax.set_xlim(0, diff.max() * 1.3)
ax.set_xlabel("Số người")
save(fig, "h2d_kho_khan")

# Hình 3: điểm lợi ích theo mức độ dùng AI
grp = [df.loc[df["Q5_DungAI"] == k, "DiemLoiIch"] for k in USE_ORDER]
fig, ax = plt.subplots(figsize=(6.4, 3.2))
ax.boxplot(grp, tick_labels=[k.replace(" nhưng ", "\nnhưng ") for k in USE_ORDER])
ax.set_ylabel("Điểm lợi ích TB (1–5)")
save(fig, "h3_loi_ich_theo_muc_do")

# Thống kê
items = df[list(LIKERT)]
k = items.shape[1]
alpha = k / (k - 1) * (1 - items.var(ddof=1).sum() / items.sum(axis=1).var(ddof=1))
rho = df["MucDoDung"].corr(df["DiemLoiIch"], method="spearman")
stats = {
    "n": int(len(df)),
    "ty_le_dung_thuong_xuyen": round(float((df["Q5_DungAI"] == "Thường xuyên").mean()), 3),
    "ty_le_chua_dung": round(float((df["Q5_DungAI"] == "Chưa từng sử dụng").mean()), 3),
    "cronbach_alpha": round(float(alpha), 3),
    "spearman_rho_mucdo_loiich": round(float(rho), 3),
    "likert": {LIKERT[c]: {"mean": round(float(items[c].mean()), 2),
                           "sd": round(float(items[c].std()), 2)} for c in LIKERT},
    "diem_loi_ich_theo_muc_do": {k: round(float(g.mean()), 2) for k, g in zip(USE_ORDER, grp)},
    "cong_cu": tools.to_dict(),
    "kho_khan": diff.to_dict(),
    "vai_tro": role.to_dict(),
}
(OUT / "thong_ke.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(stats, ensure_ascii=False, indent=2))
