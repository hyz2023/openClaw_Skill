#!/usr/bin/env python3
"""
基本面分析工具 (Fundamental Analyzer)

功能:
- 深度分析单只股票的基本面
- 评估财务健康状况
- 计算分红确定性评分
- 生成详细分析报告

使用示例:
    python scripts/fundamental_analyzer.py --symbol KO --market us
    python scripts/fundamental_analyzer.py --symbol 601398 --market cn --output report
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, List
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import akshare as ak
except ImportError:
    ak = None


class FundamentalAnalyzer:
    """基本面分析器"""
    
    def __init__(self, symbol: str, market: str = "us"):
        """
        初始化分析器
        
        Args:
            symbol: 股票代码
            market: 市场类型 ('us' 或 'cn')
        """
        self.symbol = symbol
        self.market = market.lower()
        self.data = {}
        self.score = 0
        
    def analyze_us_stock(self) -> Dict:
        """分析美股基本面"""
        if yf is None:
            return {"error": "yfinance not installed"}
        
        stock = yf.Ticker(self.symbol)
        info = stock.info
        
        # 基本信息
        self.data = {
            'symbol': self.symbol,
            'name': info.get('shortName', 'N/A'),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'price': info.get('currentPrice', 0) or info.get('previousClose', 0),
            'market_cap': info.get('marketCap', 0),
            'employees': info.get('fullTimeEmployees', 0),
        }
        
        # 股息相关
        dividends = stock.dividends
        self.data['dividend_history'] = self._process_dividend_history(dividends)
        self.data['dividend_yield'] = (info.get('dividendYield', 0) or 0) * 100
        self.data['payout_ratio'] = (info.get('payoutRatio', 0) or 0) * 100
        self.data['five_year_avg_yield'] = info.get('fiveYearAvgDividendYield', 0) or 0
        
        # 财务指标
        self.data['financials'] = {
            'pe_ratio': info.get('trailingPE', 0) or 0,
            'forward_pe': info.get('forwardPE', 0) or 0,
            'peg_ratio': info.get('pegRatio', 0) or 0,
            'price_to_book': info.get('priceToBook', 0) or 0,
            'price_to_sales': info.get('priceToSalesTrailing12Months', 0) or 0,
            'debt_to_equity': info.get('debtToEquity', 0) or 0,
            'current_ratio': info.get('currentRatio', 0) or 0,
            'quick_ratio': info.get('quickRatio', 0) or 0,
            'roe': (info.get('returnOnEquity', 0) or 0) * 100,
            'roa': (info.get('returnOnAssets', 0) or 0) * 100,
            'profit_margin': (info.get('profitMargins', 0) or 0) * 100,
            'operating_margin': (info.get('operatingMargins', 0) or 0) * 100,
        }
        
        # 现金流
        try:
            cashflow = stock.cashflow
            if cashflow is not None and not cashflow.empty:
                latest_cf = cashflow.iloc[:, 0]
                self.data['cashflow'] = {
                    'operating_cashflow': latest_cf.get('Operating Cash Flow', 0) or 0,
                    'free_cashflow': latest_cf.get('Free Cash Flow', 0) or 0,
                    'capital_expenditure': latest_cf.get('Capital Expenditure', 0) or 0,
                }
        except:
            self.data['cashflow'] = {}
        
        # 计算评分
        self.score = self._calculate_us_score()
        self.data['dividend_certainty_score'] = self.score
        
        return self.data
    
    def analyze_cn_stock(self) -> Dict:
        """分析 A 股基本面"""
        if ak is None:
            return {"error": "akshare not installed"}
        
        try:
            # 获取实时行情
            price_df = ak.stock_zh_a_spot_em()
            stock_row = price_df[price_df['代码'] == self.symbol]
            
            if stock_row.empty:
                return {"error": f"Stock {self.symbol} not found"}
            
            stock_row = stock_row.iloc[0]
            
            self.data = {
                'symbol': self.symbol,
                'name': stock_row.get('名称', 'N/A'),
                'sector': 'N/A',
                'industry': stock_row.get('行业', 'N/A'),
                'price': stock_row.get('最新价', 0),
                'market_cap': stock_row.get('总市值', 0) * 1e8,
                'pe_ratio': stock_row.get('市盈率', 0),
                'pb_ratio': stock_row.get('市净率', 0),
            }
            
            # 获取分红历史
            dividend_df = ak.stock_history_dividend(symbol=self.symbol)
            self.data['dividend_history'] = self._process_cn_dividend_history(dividend_df)
            
            # 获取财务指标
            try:
                financial = ak.stock_financial_analysis_indicator(symbol=self.symbol)
                if not financial.empty:
                    latest = financial.iloc[0]
                    self.data['financials'] = {
                        'pe_ratio': latest.get('市盈率', 0) or 0,
                        'pb_ratio': latest.get('市净率', 0) or 0,
                        'roe': latest.get('净资产收益率', 0) or 0,
                        'profit_margin': latest.get('销售净利率', 0) or 0,
                        'debt_to_equity': latest.get('资产负债率', 0) or 0,
                        'current_ratio': latest.get('流动比率', 0) or 0,
                    }
                    self.data['dividend_yield'] = latest.get('股息率', 0) or 0
                    self.data['payout_ratio'] = latest.get('派息比率', 0) or 0
            except:
                self.data['financials'] = {}
                self.data['dividend_yield'] = 0
                self.data['payout_ratio'] = 0
            
            # 计算评分
            self.score = self._calculate_cn_score()
            self.data['dividend_certainty_score'] = self.score
            
        except Exception as e:
            return {"error": str(e)}
        
        return self.data
    
    def _process_dividend_history(self, dividends: pd.Series) -> List[Dict]:
        """处理美股分红历史"""
        if dividends.empty:
            return []
        
        yearly = dividends.groupby(dividends.index.year).sum()
        history = []
        
        for year, amount in yearly.items():
            history.append({
                'year': int(year),
                'amount': round(amount, 4)
            })
        
        return sorted(history, key=lambda x: x['year'], reverse=True)[:10]
    
    def _process_cn_dividend_history(self, dividend_df: pd.DataFrame) -> List[Dict]:
        """处理 A 股分红历史"""
        if dividend_df.empty:
            return []
        
        history = []
        for _, row in dividend_df.head(10).iterrows():
            history.append({
                'year': str(row.get('年度', 'N/A')),
                'amount': row.get('每 10 股派息', 0) / 10 if '每 10 股派息' in row else 0,
                'ex_date': row.get('除权除息日', 'N/A')
            })
        
        return history
    
    def _calculate_us_score(self) -> int:
        """计算美股分红确定性评分 (0-100)"""
        score = 0
        
        # 1. 连续分红年数 (25 分)
        dividend_history = self.data.get('dividend_history', [])
        years = len(dividend_history)
        if years >= 50:
            score += 25
        elif years >= 25:
            score += 20
        elif years >= 10:
            score += 15
        elif years >= 5:
            score += 10
        elif years >= 3:
            score += 5
        
        # 2. 股息率 (20 分)
        dividend_yield = self.data.get('dividend_yield', 0)
        if dividend_yield >= 5:
            score += 20
        elif dividend_yield >= 3:
            score += 15
        elif dividend_yield >= 2:
            score += 10
        elif dividend_yield >= 1:
            score += 5
        
        # 3. 派息比率 (20 分)
        payout_ratio = self.data.get('payout_ratio', 0)
        if 30 <= payout_ratio <= 50:
            score += 20
        elif 50 < payout_ratio <= 70:
            score += 15
        elif payout_ratio < 30:
            score += 10
        elif 70 < payout_ratio <= 90:
            score += 5
        
        # 4. 财务健康 (20 分)
        financials = self.data.get('financials', {})
        debt_to_equity = financials.get('debt_to_equity', 999)
        current_ratio = financials.get('current_ratio', 0)
        roe = financials.get('roe', 0)
        
        if debt_to_equity < 0.5:
            score += 8
        elif debt_to_equity < 1:
            score += 5
        
        if current_ratio > 1.5:
            score += 7
        elif current_ratio > 1:
            score += 4
        
        if roe > 15:
            score += 5
        elif roe > 10:
            score += 3
        
        # 5. 增长性 (15 分)
        if dividend_history and len(dividend_history) >= 2:
            recent_growth = self._calculate_growth_rate(dividend_history)
            if recent_growth >= 10:
                score += 15
            elif recent_growth >= 5:
                score += 10
            elif recent_growth >= 2:
                score += 5
        
        return min(score, 100)
    
    def _calculate_cn_score(self) -> int:
        """计算 A 股分红确定性评分 (0-100)"""
        score = 0
        
        # 1. 连续分红年数 (25 分)
        dividend_history = self.data.get('dividend_history', [])
        years = len(dividend_history)
        if years >= 10:
            score += 25
        elif years >= 7:
            score += 20
        elif years >= 5:
            score += 15
        elif years >= 3:
            score += 10
        
        # 2. 股息率 (20 分)
        dividend_yield = self.data.get('dividend_yield', 0)
        if dividend_yield >= 6:
            score += 20
        elif dividend_yield >= 4:
            score += 15
        elif dividend_yield >= 2.5:
            score += 10
        elif dividend_yield >= 1.5:
            score += 5
        
        # 3. 派息比率 (20 分)
        payout_ratio = self.data.get('payout_ratio', 0)
        if 30 <= payout_ratio <= 60:
            score += 20
        elif 60 < payout_ratio <= 80:
            score += 10
        elif payout_ratio < 30:
            score += 5
        
        # 4. 财务健康 (20 分)
        financials = self.data.get('financials', {})
        debt_ratio = financials.get('debt_to_equity', 999)
        roe = financials.get('roe', 0)
        
        if debt_ratio < 50:
            score += 10
        elif debt_ratio < 70:
            score += 5
        
        if roe > 15:
            score += 10
        elif roe > 10:
            score += 5
        
        # 5. 估值合理性 (15 分)
        pe_ratio = self.data.get('pe_ratio', 999)
        if 5 <= pe_ratio <= 15:
            score += 15
        elif 15 < pe_ratio <= 25:
            score += 10
        elif pe_ratio < 5 or pe_ratio > 25:
            score += 5
        
        return min(score, 100)
    
    def _calculate_growth_rate(self, dividend_history: List[Dict]) -> float:
        """计算股息增长率"""
        if len(dividend_history) < 2:
            return 0
        
        recent = dividend_history[:3]
        if len(recent) < 2:
            return 0
        
        first = recent[-1]['amount']
        last = recent[0]['amount']
        years = len(recent) - 1
        
        if first <= 0:
            return 0
        
        cagr = ((last / first) ** (1 / years) - 1) * 100
        return cagr
    
    def generate_report(self, output_format: str = "markdown") -> str:
        """生成分析报告"""
        if output_format == "markdown":
            return self._generate_markdown_report()
        elif output_format == "json":
            return json.dumps(self.data, indent=2, ensure_ascii=False)
        else:
            return str(self.data)
    
    def _generate_markdown_report(self) -> str:
        """生成 Markdown 格式报告"""
        report = []
        report.append(f"# 📊 股票分析报告: {self.data.get('name', self.symbol)} ({self.symbol})")
        report.append(f"\n**分析日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        # 基本信息
        report.append("## 📌 基本信息")
        report.append(f"| 项目 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 当前股价 | ${self.data.get('price', 0):.2f}" if self.market == 'us' else f"| 当前股价 | ¥{self.data.get('price', 0):.2f}")
        report.append(f"| 市值 | ${self.data.get('market_cap', 0)/1e9:.2f}B" if self.market == 'us' else f"| 市值 | ¥{self.data.get('market_cap', 0)/1e8:.2f}亿")
        report.append(f"| 行业 | {self.data.get('industry', 'N/A')} |")
        report.append("")
        
        # 股息指标
        report.append("## 💰 股息指标")
        report.append(f"| 指标 | 数值 | 评级 |")
        report.append(f"|------|------|------|")
        
        dividend_yield = self.data.get('dividend_yield', 0)
        yield_rating = "✅" if dividend_yield >= 3 else "⚠️" if dividend_yield >= 1 else "❌"
        report.append(f"| 股息率 | {dividend_yield:.2f}% | {yield_rating} |")
        
        payout_ratio = self.data.get('payout_ratio', 0)
        payout_rating = "✅" if 30 <= payout_ratio <= 60 else "⚠️" if payout_ratio <= 80 else "❌"
        report.append(f"| 派息比率 | {payout_ratio:.1f}% | {payout_rating} |")
        
        dividend_history = self.data.get('dividend_history', [])
        years = len(dividend_history)
        years_rating = "✅✅✅" if years >= 25 else "✅✅" if years >= 10 else "✅" if years >= 5 else "⚠️"
        report.append(f"| 分红年数 | {years}年 | {years_rating} |")
        report.append("")
        
        # 财务指标
        report.append("## 📈 财务指标")
        financials = self.data.get('financials', {})
        if financials:
            report.append(f"| 指标 | 数值 |")
            report.append(f"|------|------|")
            for key, value in financials.items():
                if isinstance(value, (int, float)):
                    report.append(f"| {key.replace('_', ' ').title()} | {value:.2f} |")
            report.append("")
        
        # 分红历史
        if dividend_history:
            report.append("## 📅 分红历史 (近 10 年)")
            report.append("| 年份 | 每股股息 |")
            report.append("|------|----------|")
            for item in dividend_history[:10]:
                year = item.get('year', 'N/A')
                amount = item.get('amount', 0)
                report.append(f"| {year} | ${amount:.4f}" if self.market == 'us' else f"| {year} | ¥{amount:.2f}")
            report.append("")
        
        # 综合评分
        report.append("## 🎯 综合评分")
        score = self.data.get('dividend_certainty_score', 0)
        rating = "极高" if score >= 90 else "高" if score >= 75 else "中等" if score >= 60 else "低"
        report.append(f"\n**分红确定性评分**: {score}/100 ({rating})\n")
        
        # 评级说明
        report.append("### 评级说明")
        if score >= 90:
            report.append("- ✅ 极高确定性，适合作为核心持仓")
        elif score >= 75:
            report.append("- ✅ 高确定性，可重点配置")
        elif score >= 60:
            report.append("- ⚠️ 中等确定性，适量配置")
        else:
            report.append("- ❌ 低确定性，建议谨慎或避免")
        
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='基本面分析工具')
    parser.add_argument('--symbol', type=str, required=True,
                        help='股票代码')
    parser.add_argument('--market', type=str, default='us', choices=['us', 'cn'],
                        help='市场类型：us (美股) 或 cn (A 股)')
    parser.add_argument('--output', type=str, default='markdown',
                        choices=['markdown', 'json', 'print'],
                        help='输出格式')
    parser.add_argument('--output-file', type=str, default=None,
                        help='输出文件路径')
    
    args = parser.parse_args()
    
    print(f"\n🔍 分析 {args.symbol.upper()} ({args.market.upper()})...\n")
    
    analyzer = FundamentalAnalyzer(symbol=args.symbol, market=args.market)
    
    if args.market == 'us':
        data = analyzer.analyze_us_stock()
    else:
        data = analyzer.analyze_cn_stock()
    
    if 'error' in data:
        print(f"❌ 错误：{data['error']}")
        return
    
    report = analyzer.generate_report(output_format=args.output)
    
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存到：{args.output_file}")
    else:
        print(report)


if __name__ == "__main__":
    main()
