#!/usr/bin/env python3
"""
Deep Solver 検証補助スクリプト

エージェント間の結論の整合性を数値的に評価する。
Red Team エージェントおよび Synthesizer が呼び出す。

使用例:
  python3 verify_consistency.py --mode matrix
  python3 verify_consistency.py --mode contradiction "仮説A" "仮説B"
  python3 verify_consistency.py --mode score 0.8 0.6 0.9 0.3
"""

import argparse
import json
import sys
from typing import List


def consistency_matrix(hypotheses: List[str]) -> dict:
    """
    複数の仮説間の整合性マトリクスの雛形を生成する。
    実際の整合性判断はLLMが行うが、構造を提供する。
    """
    n = len(hypotheses)
    matrix = {
        "hypotheses": hypotheses,
        "matrix": [[None] * n for _ in range(n)],
        "instructions": (
            "各セル [i][j] に、仮説 i と仮説 j の整合性スコア (0.0-1.0) を入力してください。\n"
            "0.0 = 完全に矛盾, 0.5 = 独立（関連なし）, 1.0 = 完全に整合"
        )
    }
    # 対角要素は自身との整合性 = 1.0
    for i in range(n):
        matrix["matrix"][i][i] = 1.0
    return matrix


def aggregate_confidence(scores: List[float]) -> dict:
    """
    複数エージェントの確信度スコアを集約する。
    単純平均ではなく、分散も考慮した統合スコアを計算する。
    """
    if not scores:
        return {"error": "スコアが空です"}

    n = len(scores)
    mean = sum(scores) / n
    variance = sum((s - mean) ** 2 for s in scores) / n if n > 1 else 0
    std_dev = variance ** 0.5

    # 合意度: 標準偏差が小さいほど合意が高い
    # 0.0 (完全不一致) 〜 1.0 (完全一致)
    agreement = max(0.0, 1.0 - 2 * std_dev)

    # 統合確信度: 平均確信度 × 合意度
    integrated = mean * agreement

    return {
        "individual_scores": scores,
        "mean_confidence": round(mean, 3),
        "std_deviation": round(std_dev, 3),
        "agreement_level": round(agreement, 3),
        "integrated_confidence": round(integrated, 3),
        "interpretation": interpret_confidence(integrated, agreement)
    }


def interpret_confidence(integrated: float, agreement: float) -> str:
    if agreement < 0.3:
        return "エージェント間の見解が大きく分かれています。追加の分析が必要です。"
    elif agreement < 0.6:
        return "部分的な合意がありますが、重要な論点で不一致が残っています。"
    elif integrated < 0.3:
        return "合意はあるが、全体の確信度が低い。情報不足の可能性があります。"
    elif integrated < 0.6:
        return "中程度の確信度。提案は条件付きで採用可能ですが、リスク緩和策が必要です。"
    elif integrated < 0.8:
        return "高い確信度と合意。提案は十分な根拠があります。"
    else:
        return "非常に高い確信度。ただし、全員一致は確証バイアスの可能性も考慮してください。"


def detect_contradiction(claim_a: str, claim_b: str) -> dict:
    """
    2つの主張間の矛盾分析の構造を提供する。
    実際の意味分析はLLMが行う。
    """
    return {
        "claim_a": claim_a,
        "claim_b": claim_b,
        "analysis_template": {
            "logical_contradiction": "AとBは論理的に矛盾するか？（AならばBでない、が成立するか）",
            "scope_difference": "AとBは異なるスコープ（時間、空間、主体）について述べていないか？",
            "abstraction_mismatch": "AとBは異なる抽象度レベルの主張ではないか？",
            "resolution_strategies": [
                "スコープの明確化（条件分岐）",
                "抽象度の統一",
                "弁証法的止揚（上位概念の発見）",
                "両方を棄却して第三の仮説を生成"
            ]
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Deep Solver 検証補助")
    parser.add_argument("--mode", choices=["matrix", "score", "contradiction"],
                       required=True, help="実行モード")
    parser.add_argument("args", nargs="*", help="モード固有の引数")

    args = parser.parse_args()

    if args.mode == "matrix":
        if not args.args:
            print("使用法: --mode matrix 仮説1 仮説2 仮説3 ...")
            sys.exit(1)
        result = consistency_matrix(args.args)

    elif args.mode == "score":
        if not args.args:
            print("使用法: --mode score 0.8 0.6 0.9 ...")
            sys.exit(1)
        try:
            scores = [float(s) for s in args.args]
        except ValueError:
            print("エラー: スコアは数値で指定してください")
            sys.exit(1)
        result = aggregate_confidence(scores)

    elif args.mode == "contradiction":
        if len(args.args) < 2:
            print("使用法: --mode contradiction '主張A' '主張B'")
            sys.exit(1)
        result = detect_contradiction(args.args[0], args.args[1])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
