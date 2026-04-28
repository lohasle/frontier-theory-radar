#!/bin/bash
# ============================================================
# 前沿理论驱动技术雷达 - 一键运行脚本
# 用法: ./run_daily.sh [YYYY-MM-DD]
# ============================================================

set -euo pipefail

TARGET_DATE=${1:-$(date +%Y-%m-%d)}
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "============================================================"
echo "  前沿理论驱动技术雷达 - 每日运行"
echo "  日期: $TARGET_DATE"
echo "  目录: $REPO_DIR"
echo "============================================================"

cd "$REPO_DIR"

# 1. 拉取最新代码
echo ""
echo "[1/7] 拉取最新代码..."
git pull origin main || echo "[warn] git pull 失败，继续使用本地代码"

# 2. 抓取论文
echo ""
echo "[2/7] 抓取论文..."
python3 scripts/fetch_papers.py "$TARGET_DATE" || {
  echo "[error] 论文抓取失败，生成占位数据"
  YEAR=${TARGET_DATE:0:4}
  PAPERS_PATH="papers/$YEAR/$TARGET_DATE-papers.json"
  mkdir -p "papers/$YEAR"
  cat > "$PAPERS_PATH" << EOF
{
  "date": "$TARGET_DATE",
  "source_status": "fetch_failed",
  "notes": "自动抓取失败，已生成占位数据；后续可重跑 run_daily.sh 覆盖",
  "papers": [
    {
      "title": "[占位] 抓取失败，请后续重试",
      "authors": [],
      "published": "$TARGET_DATE",
      "updated": "$TARGET_DATE",
      "source": "placeholder",
      "url": "",
      "pdf_url": "",
      "openreview_url": "",
      "paperswithcode_url": "",
      "code_url": "",
      "benchmark_url": "",
      "project_url": "",
      "abstract": "抓取失败占位条目，防止日报为空。",
      "categories": [],
      "keywords": [],
      "score": 0,
      "decision": "持续观察",
      "links": []
    }
  ]
}
EOF
  echo "[fallback] 已生成占位论文文件: $PAPERS_PATH"
}

# 3. 打分
echo ""
echo "[3/7] 论文评分..."
python3 scripts/score_papers.py "$TARGET_DATE" || echo "[warn] 评分失败，使用原始分数"

# 4. 生成日报
echo ""
echo "[4/7] 生成日报..."
python3 scripts/generate_daily.py "$TARGET_DATE" || {
  echo "[error] 日报生成失败"
  # 确保至少生成一个失败说明日报
  YEAR=${TARGET_DATE:0:4}
  DAILY_PATH="daily/$YEAR/$TARGET_DATE.md"
  if [ ! -f "$DAILY_PATH" ]; then
    mkdir -p "daily/$YEAR"
    cat > "$DAILY_PATH" << EOF
# 前沿理论驱动技术雷达日报 - $TARGET_DATE

> ⚠️ 今日日报生成失败

## 失败说明

今日日报生成过程中遇到错误。可能原因：
- 论文抓取失败（网络问题或 API 限制）
- 评分脚本异常
- 日报生成脚本异常

## 下一步动作

1. 检查网络连接
2. 检查 scripts/ 目录下的脚本是否正常
3. 手动重新运行：./run_daily.sh $TARGET_DATE

---

> 生成时间：$(date -Iseconds)
> 状态：生成失败
EOF
    echo "[fallback] 已生成失败说明日报"
  fi
}

# 5. 更新索引
echo ""
echo "[5/7] 更新索引..."
python3 scripts/update_index.py "$TARGET_DATE" || echo "[warn] 索引更新失败"

# 6. 构建 Pages 数据
echo ""
echo "[6/7] 构建 Pages 数据..."
python3 scripts/build_pages.py "$TARGET_DATE" || echo "[warn] Pages 数据构建失败"

# 7. 提交和推送
echo ""
echo "[7/7] 提交和推送..."
git add -A
CHANGES=$(git diff --cached --stat)
if [ -n "$CHANGES" ]; then
  git commit -m "daily: update radar for $TARGET_DATE"
  git push origin main || echo "[warn] git push 失败，请手动推送"
  echo "[done] 已提交并推送"
else
  echo "[done] 无变更需要提交"
fi

echo ""
echo "============================================================"
echo "  完成！日期: $TARGET_DATE"
echo "============================================================"
