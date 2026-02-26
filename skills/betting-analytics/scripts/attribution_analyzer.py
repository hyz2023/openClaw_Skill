#!/usr/bin/env python3
"""
博彩数据归因分析工具
Attribution Analyzer for Betting Data

功能:
- 特征重要性分析
- SHAP 值解释
- 贡献度分解
- 因果推断
- 影响因素排序
"""

import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score


def load_data(data_path: str) -> pd.DataFrame:
    """加载数据文件"""
    path = Path(data_path)
    if path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif path.suffix == '.json':
        df = pd.read_json(data_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    
    return df


def encode_categorical_features(df: pd.DataFrame, 
                                 exclude_cols: list = None) -> tuple:
    """
    编码分类特征
    
    Returns:
        encoded_df: 编码后的 DataFrame
        encoders: 编码器字典
    """
    if exclude_cols is None:
        exclude_cols = []
    
    encoded_df = df.copy()
    encoders = {}
    
    for col in df.columns:
        if col in exclude_cols:
            continue
        
        if df[col].dtype == 'object' or isinstance(df[col].dtype, pd.CategoricalDtype):
            le = LabelEncoder()
            # 处理 NaN 值
            mask = df[col].notna()
            encoded_df.loc[mask, col] = le.fit_transform(df.loc[mask, col].astype(str))
            encoded_df[col] = encoded_df[col].fillna(-1).astype(int)
            encoders[col] = le
    
    return encoded_df, encoders


def calculate_feature_importance(X: pd.DataFrame, 
                                  y: pd.Series,
                                  method: str = 'random_forest',
                                  n_estimators: int = 100) -> pd.Series:
    """
    计算特征重要性
    
    Args:
        X: 特征 DataFrame
        y: 目标变量
        method: 方法 (random_forest / gradient_boosting)
        n_estimators: 树的数量
    
    Returns:
        特征重要性 Series
    """
    # 处理缺失值
    X_clean = X.fillna(X.median(numeric_only=True))
    
    if method == 'random_forest':
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            random_state=42,
            n_jobs=-1,
            max_depth=10
        )
    elif method == 'gradient_boosting':
        model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            random_state=42,
            max_depth=5
        )
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # 训练模型
    model.fit(X_clean, y)
    
    # 获取特征重要性
    importance = pd.Series(
        model.feature_importances_,
        index=X.columns,
        name='importance'
    )
    
    # 排序
    importance = importance.sort_values(ascending=False)
    
    return importance


def calculate_shap_values(X: pd.DataFrame, 
                          y: pd.Series,
                          n_samples: int = 100) -> dict:
    """
    计算 SHAP 值 (简化版本)
    
    注意：完整 SHAP 需要 shap 库，这里提供简化实现
    """
    try:
        import shap
        has_shap = True
    except ImportError:
        has_shap = False
        print("警告：shap 库未安装，使用简化 SHAP 近似")
    
    # 处理缺失值
    X_clean = X.fillna(X.median(numeric_only=True))
    
    # 训练模型
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_clean, y)
    
    # 采样
    if len(X_clean) > n_samples:
        X_sample = X_clean.sample(n=n_samples, random_state=42)
    else:
        X_sample = X_clean
    
    if has_shap:
        # 使用真正的 SHAP
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        
        # 对于多分类，取平均绝对值
        if isinstance(shap_values, list):
            shap_summary = np.mean([np.abs(sv) for sv in shap_values], axis=0)
        else:
            shap_summary = np.abs(shap_values)
        
        shap_importance = pd.Series(
            shap_summary.mean(axis=0),
            index=X.columns,
            name='shap_importance'
        )
    else:
        # 简化 SHAP 近似 (基于排列重要性)
        base_score = model.score(X_clean, y)
        shap_scores = []
        
        for col in X.columns:
            X_permuted = X_clean.copy()
            X_permuted[col] = np.random.permutation(X_permuted[col])
            permuted_score = model.score(X_permuted, y)
            score_drop = base_score - permuted_score
            shap_scores.append(max(0, score_drop))
        
        shap_importance = pd.Series(
            shap_scores,
            index=X.columns,
            name='shap_importance'
        )
    
    shap_importance = shap_importance.sort_values(ascending=False)
    
    return {
        'importance': shap_importance,
        'model': model
    }


def decompose_contribution(X: pd.DataFrame,
                           y: pd.Series,
                           target_value: float = None) -> pd.DataFrame:
    """
    分解每个样本的贡献度
    
    Returns:
        贡献度 DataFrame
    """
    # 处理缺失值
    X_clean = X.fillna(X.median(numeric_only=True))
    
    # 训练模型
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_clean, y)
    
    # 计算基准预测
    base_pred = model.predict_proba(X_clean)[:, 1].mean()
    
    # 对于每个特征，计算移除该特征后的预测变化
    contributions = pd.DataFrame(index=X.index)
    contributions['base_prediction'] = base_pred
    contributions['actual_prediction'] = model.predict_proba(X_clean)[:, 1]
    
    for col in X.columns:
        X_modified = X_clean.copy()
        # 将该特征替换为中位数
        X_modified[col] = X_clean[col].median()
        
        modified_pred = model.predict_proba(X_modified)[:, 1]
        contribution = contributions['actual_prediction'] - modified_pred
        
        contributions[col] = contribution
    
    contributions['total_contribution'] = contributions['actual_prediction'] - contributions['base_prediction']
    
    return contributions


def analyze_attribution(df: pd.DataFrame,
                        target_col: str,
                        method: str = 'shap',
                        exclude_cols: list = None) -> dict:
    """
    执行归因分析
    
    Args:
        df: 数据 DataFrame
        target_col: 目标变量列
        method: 分析方法 (feature_importance / shap / decomposition)
        exclude_cols: 排除的列
    
    Returns:
        分析结果字典
    """
    if exclude_cols is None:
        exclude_cols = []
    
    # 添加目标变量到排除列表
    if target_col not in exclude_cols:
        exclude_cols.append(target_col)
    
    # 编码分类特征
    print("编码分类特征...")
    encoded_df, encoders = encode_categorical_features(df, exclude_cols)
    
    # 准备特征和目标
    feature_cols = [col for col in encoded_df.columns if col not in exclude_cols]
    feature_cols = [col for col in feature_cols if encoded_df[col].dtype in [np.number, int]]
    
    X = encoded_df[feature_cols]
    y = encoded_df[target_col]
    
    # 处理目标变量 (如果是多分类，转为二分类)
    if y.nunique() > 2:
        print(f"目标变量有 {y.nunique()} 个类别，转为二分类 (>=中位数)")
        y = (y >= y.median()).astype(int)
    
    # 处理缺失值
    X = X.fillna(X.median(numeric_only=True))
    
    print(f"特征数量：{len(feature_cols)}")
    print(f"样本数量：{len(X)}")
    
    # 执行分析
    if method == 'feature_importance':
        print("计算特征重要性 (Random Forest)...")
        importance = calculate_feature_importance(X, y, method='random_forest')
        results = {
            'method': 'feature_importance',
            'importance': importance,
            'model_type': 'Random Forest'
        }
    
    elif method == 'shap':
        print("计算 SHAP 值...")
        shap_results = calculate_shap_values(X, y)
        results = {
            'method': 'shap',
            'importance': shap_results['importance'],
            'model': shap_results['model'],
            'model_type': 'Random Forest + SHAP'
        }
    
    elif method == 'decomposition':
        print("计算贡献度分解...")
        contributions = decompose_contribution(X, y)
        importance = calculate_feature_importance(X, y)
        results = {
            'method': 'decomposition',
            'importance': importance,
            'contributions': contributions,
            'model_type': 'Random Forest'
        }
    
    else:
        raise ValueError(f"Unknown method: {method}")
    
    # 模型评估
    from sklearn.model_selection import cross_val_score
    model = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    
    results['model_performance'] = {
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
        'cv_scores': cv_scores.tolist()
    }
    
    # 添加特征统计
    results['feature_stats'] = {}
    for col in feature_cols[:10]:  # 只显示前 10 个特征
        results['feature_stats'][col] = {
            'type': str(X[col].dtype),
            'unique_values': X[col].nunique(),
            'missing_rate': X[col].isna().sum() / len(X)
        }
    
    return results


def generate_report(results: dict, output_path: str = None) -> str:
    """生成归因分析报告"""
    report = []
    report.append("## 🎯 归因分析报告")
    report.append("")
    report.append(f"**分析方法**: {results['method']}")
    report.append(f"**模型类型**: {results['model_type']}")
    report.append("")
    
    # 模型性能
    perf = results['model_performance']
    report.append("### 模型性能")
    report.append(f"| 指标 | 数值 |")
    report.append(f"|------|------|")
    report.append(f"| 交叉验证准确率 | {perf['cv_mean']:.2%} |")
    report.append(f"| 标准差 | {perf['cv_std']:.2%} |")
    report.append("")
    
    # 特征重要性
    report.append("### 特征重要性 (Top 10)")
    report.append("")
    importance = results['importance']
    
    report.append("| 排名 | 特征 | 重要性 | 占比 |")
    report.append("|------|------|--------|------|")
    
    total_importance = importance.sum()
    for i, (feature, imp) in enumerate(importance.head(10).items(), 1):
        percentage = (imp / total_importance * 100) if total_importance > 0 else 0
        # 可视化条
        bar_len = int(percentage / 5)
        bar = "█" * bar_len
        report.append(f"| {i} | {feature} | {imp:.4f} | {percentage:.1f}% {bar} |")
    
    report.append("")
    
    # 关键发现
    report.append("### 关键发现")
    report.append("")
    
    top_3 = importance.head(3)
    if len(top_3) > 0:
        report.append(f"**Top 3 影响因素**:")
        for feature, imp in top_3.items():
            report.append(f"1. **{feature}**: 重要性 {imp:.4f} ({imp/total_importance*100:.1f}%)")
        report.append("")
    
    # 累计贡献
    cumsum = importance.cumsum() / total_importance * 100
    top_5_idx = cumsum.head(5).index.tolist()
    top_5_coverage = cumsum.head(5).values[-1] if len(cumsum) >= 5 else cumsum.values[-1]
    
    report.append(f"**前 5 大特征累计贡献**: {top_5_coverage:.1f}%")
    report.append("")
    
    # 建议
    report.append("### 建议")
    report.append("")
    
    if perf['cv_mean'] > 0.8:
        report.append("✅ 模型性能优秀，特征重要性可信度高")
    elif perf['cv_mean'] > 0.6:
        report.append("⚡ 模型性能良好，可参考特征重要性进行分析")
    else:
        report.append("⚠️ 模型性能一般，建议:")
        report.append("1. 增加更多特征")
        report.append("2. 收集更多样本数据")
        report.append("3. 尝试其他模型")
    
    report.append("")
    
    # 如果有贡献度分解
    if 'contributions' in results:
        report.append("### 样本贡献度示例")
        report.append("")
        contrib = results['contributions'].head(5)
        report.append("前 5 个样本的预测贡献度:")
        report.append(contrib.to_string())
        report.append("")
    
    report_text = '\n'.join(report)
    
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
    
    return report_text


def main():
    parser = argparse.ArgumentParser(description='博彩数据归因分析工具')
    parser.add_argument('--data', required=True, help='输入数据文件路径 (CSV/JSON)')
    parser.add_argument('--target', required=True, help='目标变量列名')
    parser.add_argument('--method', default='shap',
                        choices=['feature_importance', 'shap', 'decomposition'],
                        help='分析方法')
    parser.add_argument('--exclude', nargs='+', default=None, 
                        help='排除的列名列表')
    parser.add_argument('--output', default=None, help='输出报告文件路径')
    
    args = parser.parse_args()
    
    # 加载数据
    print(f"加载数据：{args.data}")
    df = load_data(args.data)
    print(f"数据加载完成，共 {len(df)} 条记录")
    
    # 检查目标列
    if args.target not in df.columns:
        print(f"错误：目标列 '{args.target}' 不存在")
        print(f"可用列：{list(df.columns)}")
        return
    
    # 执行归因分析
    print("执行归因分析...")
    results = analyze_attribution(
        df, 
        args.target, 
        args.method,
        args.exclude
    )
    
    # 生成报告
    report = generate_report(results, args.output)
    print("\n" + report)
    
    if args.output:
        print(f"\n报告已保存至：{args.output}")


if __name__ == '__main__':
    main()
