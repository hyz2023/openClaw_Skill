#!/usr/bin/env python3
"""
股息股筛选工具 (Dividend Stock Screener)

功能:
- 筛选 A 股/美股高股息股票
- 按连续分红年数、股息率、财务指标过滤
- 输出候选股票列表

使用示例:
    python scripts/dividend_screener.py --market us --min-yield 3 --years-stable 5
    python scripts/dividend_screener.py --market cn --min-yield 2.5 --output csv
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

# 添加父目录到路径以导入模块
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import akshare as ak
except ImportError:
    print("请安装 A 股数据模块：pip install akshare")
    ak = None

try:
    import yfinance as yf
except ImportError:
    print("请安装美股数据模块：pip install yfinance")
    yf = None


class DividendScreener:
    """股息股筛选器"""
    
    def __init__(self, market: str = "us"):
        """
        初始化筛选器
        
        Args:
            market: 市场类型 ('us' 或 'cn')
        """
        self.market = market.lower()
        self.results = []
        
    def screen_us_stocks(
        self,
        min_yield: float = 3.0,
        min_years: int = 10,
        max_payout: float = 70.0,
        min_market_cap: float = 5000000000,
        symbols: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        筛选美股高股息股票
        
        Args:
            min_yield: 最小股息率 (%)
            min_years: 最小连续分红年数
            max_payout: 最大派息比率 (%)
            min_market_cap: 最小市值 (美元)
            symbols: 指定股票代码列表，None 则使用预设列表
            
        Returns:
            符合条件的股票列表
        """
        if yf is None:
            print("错误：yfinance 未安装")
            return []
        
        # 预设高股息股票池 (可扩展)
        if symbols is None:
            symbols = [
                # 股息贵族/王者
                'KO', 'PEP', 'JNJ', 'PG', 'MCD', 'WMT', 'TGT',
                'LOW', 'HD', 'CAT', 'MMM', 'HON', 'UNP',
                # 高股息 REITs
                'O', 'STAG', 'MAIN', 'ARCC',
                # 电信
                'VZ', 'T',
                # 能源
                'XOM', 'CVX', 'ENB',
                # 金融
                'JPM', 'BAC', 'WFC', 'MS',
            ]
        
        results = []
        print(f"正在筛选 {len(symbols)} 只美股...\n")
        
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                
                # 获取基本信息
                dividend_yield = info.get('dividendYield', 0) or 0
                dividend_yield_pct = dividend_yield * 100
                payout_ratio = info.get('payoutRatio', 0) or 0
                market_cap = info.get('marketCap', 0) or 0
                pe_ratio = info.get('trailingPE', 0) or 0
                debt_to_equity = info.get('debtToEquity', 0) or 0
                
                # 获取分红历史
                dividends = stock.dividends
                years_of_dividends = self._calculate_dividend_years(dividends)
                
                # 计算 5 年股息增长率
                div_growth = self._calculate_dividend_growth(dividends)
                
                # 筛选条件
                if dividend_yield_pct < min_yield:
                    continue
                if years_of_dividends < min_years:
                    continue
                if payout_ratio > max_payout / 100 and payout_ratio > 0:
                    continue
                if market_cap < min_market_cap:
                    continue
                
                # 通过筛选
                stock_data = {
                    'symbol': symbol,
                    'name': info.get('shortName', 'N/A'),
                    'price': info.get('currentPrice', 0) or info.get('previousClose', 0),
                    'dividend_yield': dividend_yield_pct,
                    'payout_ratio': payout_ratio * 100 if payout_ratio else 0,
                    'market_cap': market_cap,
                    'pe_ratio': pe_ratio,
                    'debt_to_equity': debt_to_equity,
                    'years_of_dividends': years_of_dividends,
                    'dividend_growth_5y': div_growth,
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                }
                
                results.append(stock_data)
                print(f"✅ {symbol}: 股息率 {dividend_yield_pct:.2f}%, "
                      f"连续 {years_of_dividends}年, P/E {pe_ratio:.1f}")
                
            except Exception as e:
                print(f"⚠️  {symbol}: 获取数据失败 - {e}")
                continue
        
        # 按股息率排序
        results.sort(key=lambda x: x['dividend_yield'], reverse=True)
        self.results = results
        return results
    
    def screen_cn_stocks(
        self,
        min_yield: float = 2.5,
        min_years: int = 5,
        max_payout: float = 70.0,
        min_market_cap: float = 10000000000,
        symbols: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        筛选 A 股高股息股票
        
        Args:
            min_yield: 最小股息率 (%)
            min_years: 最小连续分红年数
            max_payout: 最大派息比率 (%)
            min_market_cap: 最小市值 (人民币)
            symbols: 指定股票代码列表
            
        Returns:
            符合条件的股票列表
        """
        if ak is None:
            print("错误：akshare 未安装")
            return []
        
        # 预设高股息股票池 (可扩展)
        if symbols is None:
            # 银行、能源、公用事业等高股息板块
            symbols = [
                # 银行
                '601398', '601288', '601939', '601988', '600036',
                # 能源
                '601088', '600028', '600938',
                # 公用事业
                '600900', '600886', '600025',
                # 交通运输
                '601390', '601111', '600009',
                # 消费
                '600519', '000858', '000651',
            ]
        
        results = []
        print(f"正在筛选 {len(symbols)} 只 A 股...\n")
        
        for symbol in symbols:
            try:
                # 获取分红历史
                dividend_df = ak.stock_history_dividend(symbol=symbol)
                if dividend_df.empty:
                    continue
                
                # 计算连续分红年数
                years_of_dividends = self._calculate_cn_dividend_years(dividend_df)
                
                # 获取实时行情
                price_df = ak.stock_zh_a_spot_em()
                stock_data_row = price_df[price_df['代码'] == symbol]
                
                if stock_data_row.empty:
                    continue
                
                current_price = stock_data_row['最新价'].values[0]
                market_cap = stock_data_row['总市值'].values[0] * 1e8  # 转换为元
                
                # 获取财务指标
                try:
                    financial = ak.stock_financial_analysis_indicator(symbol=symbol)
                    if not financial.empty:
                        latest = financial.iloc[0]
                        dividend_yield = latest.get('股息率', 0) or 0
                        payout_ratio = latest.get('派息比率', 0) or 0
                        pe_ratio = latest.get('市盈率', 0) or 0
                    else:
                        dividend_yield = 0
                        payout_ratio = 0
                        pe_ratio = 0
                except:
                    dividend_yield = 0
                    payout_ratio = 0
                    pe_ratio = 0
                
                # 筛选条件
                if dividend_yield < min_yield:
                    continue
                if years_of_dividends < min_years:
                    continue
                if payout_ratio > max_payout and payout_ratio > 0:
                    continue
                if market_cap < min_market_cap:
                    continue
                
                # 获取股票名称
                stock_name = stock_data_row['名称'].values[0]
                
                stock_info = {
                    'symbol': symbol,
                    'name': stock_name,
                    'price': current_price,
                    'dividend_yield': dividend_yield,
                    'payout_ratio': payout_ratio,
                    'market_cap': market_cap,
                    'pe_ratio': pe_ratio,
                    'years_of_dividends': years_of_dividends,
                    'sector': 'N/A',
                    'industry': 'N/A',
                }
                
                results.append(stock_info)
                print(f"✅ {symbol} {stock_name}: 股息率 {dividend_yield:.2f}%, "
                      f"连续 {years_of_dividends}年")
                
            except Exception as e:
                print(f"⚠️  {symbol}: 获取数据失败 - {e}")
                continue
        
        # 按股息率排序
        results.sort(key=lambda x: x['dividend_yield'], reverse=True)
        self.results = results
        return results
    
    def _calculate_dividend_years(self, dividends: pd.Series) -> int:
        """计算连续分红年数 (美股)"""
        if dividends.empty:
            return 0
        
        # 按年份分组
        years = dividends.index.year.unique()
        return len(years)
    
    def _calculate_dividend_growth(self, dividends: pd.Series) -> float:
        """计算 5 年股息增长率 (美股)"""
        if dividends.empty:
            return 0
        
        # 按年份汇总
        yearly = dividends.groupby(dividends.index.year).sum()
        if len(yearly) < 2:
            return 0
        
        # 取最近 5 年
        recent = yearly.tail(5)
        if len(recent) < 2:
            return 0
        
        # 计算 CAGR
        first_year = recent.iloc[0]
        last_year = recent.iloc[-1]
        years = len(recent) - 1
        
        if first_year <= 0:
            return 0
        
        cagr = ((last_year / first_year) ** (1 / years) - 1) * 100
        return cagr
    
    def _calculate_cn_dividend_years(self, dividend_df: pd.DataFrame) -> int:
        """计算连续分红年数 (A 股)"""
        if dividend_df.empty:
            return 0
        
        # A 股分红数据通常包含年度字段
        if '年度' in dividend_df.columns:
            years = dividend_df['年度'].unique()
            return len(years)
        elif 'date' in dividend_df.columns:
            years = pd.to_datetime(dividend_df['date']).dt.year.unique()
            return len(years)
        
        return 0
    
    def export_results(self, output_format: str = "table", output_file: Optional[str] = None):
        """
        导出筛选结果
        
        Args:
            output_format: 输出格式 ('table', 'csv', 'json')
            output_file: 输出文件路径
        """
        if not self.results:
            print("没有筛选结果")
            return
        
        df = pd.DataFrame(self.results)
        
        if output_format == "table":
            print("\n" + "="*80)
            print("筛选结果")
            print("="*80)
            
            # 格式化显示
            display_df = df.copy()
            if 'market_cap' in display_df.columns:
                display_df['market_cap'] = display_df['market_cap'] / 1e9  # 转换为十亿
            
            print(display_df.to_string(index=False, float_format="%.2f"))
            
        elif output_format == "csv":
            filename = output_file or f"dividend_screener_{self.market}_{datetime.now().strftime('%Y%m%d')}.csv"
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"\n结果已保存到：{filename}")
            
        elif output_format == "json":
            filename = output_file or f"dividend_screener_{self.market}_{datetime.now().strftime('%Y%m%d')}.json"
            df.to_json(filename, orient='records', force_ascii=False, indent=2)
            print(f"\n结果已保存到：{filename}")


def main():
    parser = argparse.ArgumentParser(description='股息股筛选工具')
    parser.add_argument('--market', type=str, default='us', choices=['us', 'cn'],
                        help='市场类型：us (美股) 或 cn (A 股)')
    parser.add_argument('--min-yield', type=float, default=3.0,
                        help='最小股息率 (百分比)')
    parser.add_argument('--years-stable', type=int, default=10,
                        help='最小连续分红年数')
    parser.add_argument('--max-payout', type=float, default=70.0,
                        help='最大派息比率 (百分比)')
    parser.add_argument('--output', type=str, default='table',
                        choices=['table', 'csv', 'json'],
                        help='输出格式')
    parser.add_argument('--output-file', type=str, default=None,
                        help='输出文件路径')
    
    args = parser.parse_args()
    
    print(f"\n🔍 开始筛选 {args.market.upper()} 市场高股息股票...")
    print(f"条件：股息率≥{args.min_yield}%, 连续分红≥{args.years_stable}年, "
          f"派息比率≤{args.max_payout}%\n")
    
    screener = DividendScreener(market=args.market)
    
    if args.market == 'us':
        results = screener.screen_us_stocks(
            min_yield=args.min_yield,
            min_years=args.years_stable,
            max_payout=args.max_payout
        )
    else:
        results = screener.screen_cn_stocks(
            min_yield=args.min_yield,
            min_years=args.years_stable,
            max_payout=args.max_payout
        )
    
    if results:
        print(f"\n✅ 找到 {len(results)} 只符合条件的股票\n")
        screener.export_results(output_format=args.output, output_file=args.output_file)
    else:
        print("\n⚠️  未找到符合条件的股票，请放宽筛选条件")


if __name__ == "__main__":
    main()
