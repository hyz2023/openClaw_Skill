#!/usr/bin/env python3
"""
目标价位计算工具 (Target Price Calculator)

功能:
- 基于股息率计算目标买入价
- DCF 折现模型估值
- 历史估值分位分析
- 给出安全边际建议

使用示例:
    python scripts/target_price_calculator.py --symbol KO --market us
    python scripts/target_price_calculator.py --symbol 601398 --market cn --target-yield 4
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
import pandas as pd

try:
    import yfinance as yf
except ImportError:
    yf = None

try:
    import akshare as ak
except ImportError:
    ak = None


class TargetPriceCalculator:
    """目标价位计算器"""
    
    def __init__(self, symbol: str, market: str = "us"):
        """
        初始化计算器
        
        Args:
            symbol: 股票代码
            market: 市场类型 ('us' 或 'cn')
        """
        self.symbol = symbol
        self.market = market.lower()
        self.current_price = 0
        self.annual_dividend = 0
        self.data = {}
        
    def calculate_us_target_price(
        self,
        target_yield: Optional[float] = None,
        margin_of_safety: float = 0.1
    ) -> Dict:
        """
        计算美股目标价位
        
        Args:
            target_yield: 目标股息率 (None 则使用行业平均)
            margin_of_safety: 安全边际 (默认 10%)
            
        Returns:
            包含各种估值方法结果的字典
        """
        if yf is None:
            return {"error": "yfinance not installed"}
        
        stock = yf.Ticker(self.symbol)
        info = stock.info
        
        # 获取当前价格和股息
        self.current_price = info.get('currentPrice', 0) or info.get('previousClose', 0)
        dividend_rate = info.get('dividendRate', 0) or 0
        self.annual_dividend = dividend_rate
        
        # 获取历史数据用于估值分析
        try:
            hist = stock.history(period='5y')
            if not hist.empty:
                # 计算历史估值分位
                self.data['price_history'] = {
                    'high_52w': hist['High'].max(),
                    'low_52w': hist['Low'].min(),
                    'avg_52w': hist['Close'].mean(),
                    'current': self.current_price,
                }
        except:
            pass
        
        # 方法 1: 股息率目标价
        if target_yield is None:
            # 使用 5 年平均股息率作为参考
            target_yield = info.get('fiveYearAvgDividendYield', 0) or 3.0
        
        dividend_yield_target_price = self.annual_dividend / (target_yield / 100)
        
        # 方法 2: DCF 模型 (简化版)
        dcf_price = self._calculate_dcf(info)
        
        # 方法 3: 历史估值分位
        historical_target = self._calculate_historical_target()
        
        # 综合目标价 (加权平均)
        weights = {'dividend': 0.5, 'dcf': 0.3, 'historical': 0.2}
        composite_price = (
            dividend_yield_target_price * weights['dividend'] +
            (dcf_price or dividend_yield_target_price) * weights['dcf'] +
            (historical_target or dividend_yield_target_price) * weights['historical']
        )
        
        # 应用安全边际
        safe_buy_price = composite_price * (1 - margin_of_safety)
        
        self.data = {
            'symbol': self.symbol,
            'name': info.get('shortName', 'N/A'),
            'current_price': self.current_price,
            'annual_dividend': self.annual_dividend,
            'current_yield': (self.annual_dividend / self.current_price * 100) if self.current_price > 0 else 0,
            'target_yield': target_yield,
            'valuation_methods': {
                'dividend_yield_target': {
                    'price': round(dividend_yield_target_price, 2),
                    'description': f'基于{target_yield:.1f}%目标股息率',
                },
                'dcf_model': {
                    'price': round(dcf_price, 2) if dcf_price else None,
                    'description': 'DCF 折现模型 (简化)',
                },
                'historical_average': {
                    'price': round(historical_target, 2) if historical_target else None,
                    'description': '历史估值中枢',
                },
            },
            'composite_target': round(composite_price, 2),
            'safe_buy_price': round(safe_buy_price, 2),
            'margin_of_safety': margin_of_safety * 100,
            'upside_potential': round((composite_price / self.current_price - 1) * 100, 2) if self.current_price > 0 else 0,
            'recommendation': self._generate_recommendation(safe_buy_price),
        }
        
        return self.data
    
    def calculate_cn_target_price(
        self,
        target_yield: Optional[float] = None,
        margin_of_safety: float = 0.1
    ) -> Dict:
        """
        计算 A 股目标价位
        
        Args:
            target_yield: 目标股息率
            margin_of_safety: 安全边际
            
        Returns:
            估值结果字典
        """
        if ak is None:
            return {"error": "akshare not installed"}
        
        try:
            # 获取实时行情
            price_df = ak.stock_zh_a_spot_em()
            stock_row = price_df[price_df['代码'] == self.symbol]
            
            if stock_row.empty:
                return {"error": f"Stock {self.symbol} not found"}
            
            stock_row = stock_row.iloc[0]
            self.current_price = stock_row.get('最新价', 0)
            
            # 获取分红数据
            try:
                dividend_df = ak.stock_history_dividend(symbol=self.symbol)
                if not dividend_df.empty:
                    # 计算最近年度股息
                    recent_dividends = dividend_df.head(3)
                    if '每 10 股派息' in recent_dividends.columns:
                        self.annual_dividend = recent_dividends['每 10 股派息'].mean() / 10
                    else:
                        self.annual_dividend = 0
                else:
                    self.annual_dividend = 0
            except:
                self.annual_dividend = 0
            
            # 获取财务指标
            try:
                financial = ak.stock_financial_analysis_indicator(symbol=self.symbol)
                if not financial.empty:
                    latest = financial.iloc[0]
                    pe_ratio = latest.get('市盈率', 0) or 0
                    pb_ratio = latest.get('市净率', 0) or 0
                    dividend_yield = latest.get('股息率', 0) or 0
                else:
                    pe_ratio = 0
                    pb_ratio = 0
                    dividend_yield = 0
            except:
                pe_ratio = 0
                pb_ratio = 0
                dividend_yield = 0
            
            # 方法 1: 股息率目标价
            if target_yield is None:
                target_yield = dividend_yield if dividend_yield > 0 else 3.0
            
            dividend_yield_target_price = self.annual_dividend / (target_yield / 100) if self.annual_dividend > 0 else self.current_price
            
            # 方法 2: PE 估值
            pe_target_price = self._calculate_pe_based_target(pe_ratio)
            
            # 方法 3: PB 估值
            pb_target_price = self._calculate_pb_based_target(pb_ratio)
            
            # 综合目标价
            weights = {'dividend': 0.5, 'pe': 0.3, 'pb': 0.2}
            composite_price = (
                dividend_yield_target_price * weights['dividend'] +
                (pe_target_price or dividend_yield_target_price) * weights['pe'] +
                (pb_target_price or dividend_yield_target_price) * weights['pb']
            )
            
            # 应用安全边际
            safe_buy_price = composite_price * (1 - margin_of_safety)
            
            self.data = {
                'symbol': self.symbol,
                'name': stock_row.get('名称', 'N/A'),
                'current_price': self.current_price,
                'annual_dividend': self.annual_dividend,
                'current_yield': dividend_yield,
                'target_yield': target_yield,
                'pe_ratio': pe_ratio,
                'pb_ratio': pb_ratio,
                'valuation_methods': {
                    'dividend_yield_target': {
                        'price': round(dividend_yield_target_price, 2),
                        'description': f'基于{target_yield:.1f}%目标股息率',
                    },
                    'pe_based': {
                        'price': round(pe_target_price, 2) if pe_target_price else None,
                        'description': 'PE 估值法',
                    },
                    'pb_based': {
                        'price': round(pb_target_price, 2) if pb_target_price else None,
                        'description': 'PB 估值法',
                    },
                },
                'composite_target': round(composite_price, 2),
                'safe_buy_price': round(safe_buy_price, 2),
                'margin_of_safety': margin_of_safety * 100,
                'upside_potential': round((composite_price / self.current_price - 1) * 100, 2) if self.current_price > 0 else 0,
                'recommendation': self._generate_recommendation(safe_buy_price),
            }
            
        except Exception as e:
            return {"error": str(e)}
        
        return self.data
    
    def _calculate_dcf(self, info: Dict) -> Optional[float]:
        """简化 DCF 模型计算"""
        try:
            # 获取关键数据
            free_cashflow = info.get('freeCashflow', 0) or 0
            shares_outstanding = info.get('sharesOutstanding', 0) or 0
            growth_rate = 0.05  # 假设 5% 永续增长
            discount_rate = 0.10  # 假设 10% 折现率
            
            if free_cashflow <= 0 or shares_outstanding <= 0:
                return None
            
            # 计算每股自由现金流
            fcff_per_share = free_cashflow / shares_outstanding
            
            # 简化 DCF: 永续增长模型
            # Value = FCFF * (1 + g) / (r - g)
            if discount_rate <= growth_rate:
                return None
            
            intrinsic_value = fcff_per_share * (1 + growth_rate) / (discount_rate - growth_rate)
            
            return intrinsic_value if intrinsic_value > 0 else None
            
        except:
            return None
    
    def _calculate_historical_target(self) -> Optional[float]:
        """基于历史估值计算目标价"""
        if 'price_history' not in self.data:
            return None
        
        hist = self.data['price_history']
        if not hist:
            return None
        
        # 使用 52 周平均作为参考
        avg_price = hist.get('avg_52w', 0)
        return avg_price if avg_price > 0 else None
    
    def _calculate_pe_based_target(self, current_pe: float) -> Optional[float]:
        """基于 PE 的目标价计算"""
        try:
            # 获取每股收益
            if ak is None:
                return None
            
            financial = ak.stock_financial_analysis_indicator(symbol=self.symbol)
            if financial.empty:
                return None
            
            latest = financial.iloc[0]
            eps = latest.get('每股收益', 0) or 0
            
            if eps <= 0:
                return None
            
            # 使用行业平均 PE 或历史平均 PE (简化为 10-15 倍)
            target_pe = 12 if current_pe > 15 else current_pe
            
            return eps * target_pe
            
        except:
            return None
    
    def _calculate_pb_based_target(self, current_pb: float) -> Optional[float]:
        """基于 PB 的目标价计算"""
        try:
            if ak is None:
                return None
            
            financial = ak.stock_financial_analysis_indicator(symbol=self.symbol)
            if financial.empty:
                return None
            
            latest = financial.iloc[0]
            bvps = latest.get('每股净资产', 0) or 0
            
            if bvps <= 0:
                return None
            
            # 目标 PB (简化为 1-2 倍)
            target_pb = 1.5 if current_pb > 2 else current_pb
            
            return bvps * target_pb
            
        except:
            return None
    
    def _generate_recommendation(self, safe_price: float) -> str:
        """生成投资建议"""
        if self.current_price <= 0:
            return "无法评估 - 价格数据缺失"
        
        discount = (safe_price - self.current_price) / self.current_price * 100
        
        if discount > 20:
            return "强烈买入 - 当前价格远低于安全边际价"
        elif discount > 10:
            return "买入 - 当前价格低于安全边际价"
        elif discount > 0:
            return "观望 - 接近合理价位，可分批建仓"
        elif discount > -10:
            return "持有 - 略高于合理价位，持有观望"
        else:
            return "卖出/避免 - 当前价格显著高于合理价位"
    
    def generate_report(self) -> str:
        """生成 Markdown 格式报告"""
        report = []
        report.append(f"# 🎯 目标价位分析：{self.data.get('name', self.symbol)} ({self.symbol})")
        report.append(f"\n**分析日期**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        # 当前价格
        report.append("## 📊 当前价格")
        currency = "$" if self.market == 'us' else "¥"
        report.append(f"| 指标 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 当前股价 | {currency}{self.data.get('current_price', 0):.2f} |")
        report.append(f"| 年度股息 | {currency}{self.data.get('annual_dividend', 0):.4f} |")
        report.append(f"| 当前股息率 | {self.data.get('current_yield', 0):.2f}% |")
        report.append("")
        
        # 估值方法
        report.append("## 📈 估值方法")
        methods = self.data.get('valuation_methods', {})
        for method_name, method_data in methods.items():
            price = method_data.get('price')
            desc = method_data.get('description')
            if price:
                report.append(f"- **{method_name.replace('_', ' ').title()}**: {currency}{price:.2f} ({desc})")
        report.append("")
        
        # 综合目标价
        report.append("## 🎯 综合估值")
        report.append(f"| 项目 | 数值 |")
        report.append(f"|------|------|")
        report.append(f"| 综合目标价 | {currency}{self.data.get('composite_target', 0):.2f} |")
        report.append(f"| 安全边际 | {self.data.get('margin_of_safety', 0):.0f}% |")
        report.append(f"| **安全买入价** | **{currency}{self.data.get('safe_buy_price', 0):.2f}** |")
        report.append(f"| 上涨空间 | {self.data.get('upside_potential', 0):.2f}% |")
        report.append("")
        
        # 投资建议
        report.append("## 💡 投资建议")
        report.append(f"\n**{self.data.get('recommendation', 'N/A')}**\n")
        
        # 操作建议
        current = self.data.get('current_price', 0)
        safe = self.data.get('safe_buy_price', 0)
        
        if current > 0 and safe > 0:
            if current <= safe * 0.8:
                report.append("### 操作建议")
                report.append("- ✅ **积极建仓** - 价格显著低估，可加大仓位")
                report.append("- 📈 建议分批买入，避免一次性投入")
            elif current <= safe:
                report.append("### 操作建议")
                report.append("- ✅ **开始建仓** - 价格进入合理区间")
                report.append("- 📊 可分 3-5 批逐步买入")
            elif current <= safe * 1.1:
                report.append("### 操作建议")
                report.append("- ⏸️ **观望等待** - 略高于合理价，等待回调")
                report.append("- 📋 设置价格提醒，接近安全价时买入")
            else:
                report.append("### 操作建议")
                report.append("- ⚠️ **暂不买入** - 价格偏高，等待更好时机")
                report.append("- 💰 持有现金，寻找其他机会")
        
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='目标价位计算工具')
    parser.add_argument('--symbol', type=str, required=True,
                        help='股票代码')
    parser.add_argument('--market', type=str, default='us', choices=['us', 'cn'],
                        help='市场类型：us (美股) 或 cn (A 股)')
    parser.add_argument('--target-yield', type=float, default=None,
                        help='目标股息率 (%)')
    parser.add_argument('--margin', type=float, default=0.1,
                        help='安全边际 (默认 10%)')
    parser.add_argument('--output-file', type=str, default=None,
                        help='输出文件路径')
    
    args = parser.parse_args()
    
    print(f"\n🎯 计算 {args.symbol.upper()} 目标价位...\n")
    
    calculator = TargetPriceCalculator(symbol=args.symbol, market=args.market)
    
    if args.market == 'us':
        data = calculator.calculate_us_target_price(
            target_yield=args.target_yield,
            margin_of_safety=args.margin
        )
    else:
        data = calculator.calculate_cn_target_price(
            target_yield=args.target_yield,
            margin_of_safety=args.margin
        )
    
    if 'error' in data:
        print(f"❌ 错误：{data['error']}")
        return
    
    calculator.data = data
    report = calculator.generate_report()
    
    if args.output_file:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"报告已保存到：{args.output_file}")
    else:
        print(report)


if __name__ == "__main__":
    main()
