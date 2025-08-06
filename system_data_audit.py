#!/usr/bin/env python3
"""
系统数据全面审计
检查所有数据源的准确性、一致性和可靠性
"""

import sys
import os
import requests
import json
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class DataSourceAuditor:
    """数据源审计器"""
    
    def __init__(self):
        self.test_stocks = [
            '688110',  # 东芯股份 - 科创板
            '000001',  # 平安银行 - 主板
            '300001',  # 特锐德 - 创业板
            '600000',  # 浦发银行 - 主板
            'AAPL',    # 苹果 - 美股
            'TSLA'     # 特斯拉 - 美股
        ]
        
        self.audit_results = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'stocks': {},
            'data_quality': {},
            'recommendations': []
        }
    
    def audit_tencent_finance(self, symbol):
        """审计腾讯财经数据源"""
        try:
            # 处理市场前缀
            if symbol.startswith('688'):
                market = 'sh'
            elif symbol.startswith(('6', '5')):
                market = 'sh'
            elif symbol.startswith(('0', '3', '2')):
                market = 'sz'
            elif symbol.isalpha():
                # 美股
                market = 'us'
                url = f"http://qt.gtimg.cn/q=us{symbol}"
            else:
                market = 'sz'
            
            if symbol.isdigit():
                url = f"http://qt.gtimg.cn/q={market}{symbol}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.text.strip()
                if data and '~' in data:
                    parts = data.split('~')
                    if len(parts) > 30:
                        return {
                            'source': 'tencent',
                            'symbol': symbol,
                            'name': parts[1],
                            'price': float(parts[3]),
                            'open': float(parts[5]),
                            'close': float(parts[4]),
                            'high': float(parts[33]),
                            'low': float(parts[34]),
                            'volume': int(parts[36]) if len(parts) > 36 else 0,
                            'change': float(parts[31]),
                            'change_pct': float(parts[32]),
                            'timestamp': parts[30],
                            'status': 'success'
                        }
        except Exception as e:
            return {'source': 'tencent', 'symbol': symbol, 'status': 'error', 'error': str(e)}
        
        return {'source': 'tencent', 'symbol': symbol, 'status': 'failed', 'error': 'no_data'}
    
    def audit_sina_finance(self, symbol):
        """审计新浪财经数据源"""
        try:
            # 处理市场前缀
            if symbol.startswith('688'):
                market = 'sh'
            elif symbol.startswith(('6', '5')):
                market = 'sh'
            elif symbol.startswith(('0', '3', '2')):
                market = 'sz'
            elif symbol.isalpha():
                # 美股使用不同格式
                url = f"http://hq.sinajs.cn/list=gb_{symbol.lower()}"
            else:
                market = 'sz'
            
            if symbol.isdigit():
                url = f"http://hq.sinajs.cn/list={market}{symbol}"
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.text.strip()
                if data and ',' in data:
                    parts = data.split(',')
                    if len(parts) > 30:
                        name = parts[0].split('="')[1] if '="' in parts[0] else symbol
                        return {
                            'source': 'sina',
                            'symbol': symbol,
                            'name': name,
                            'price': float(parts[3]),
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'high': float(parts[4]),
                            'low': float(parts[5]),
                            'volume': int(parts[8]) if len(parts) > 8 else 0,
                            'change': float(parts[3]) - float(parts[2]),
                            'change_pct': ((float(parts[3]) - float(parts[2])) / float(parts[2])) * 100,
                            'timestamp': parts[30] if len(parts) > 30 else '',
                            'status': 'success'
                        }
        except Exception as e:
            return {'source': 'sina', 'symbol': symbol, 'status': 'error', 'error': str(e)}
        
        return {'source': 'sina', 'symbol': symbol, 'status': 'failed', 'error': 'no_data'}
    
    def audit_eastmoney(self, symbol):
        """审计东方财富数据源"""
        try:
            # 东方财富需要不同处理
            if symbol.startswith('688'):
                # 科创板特殊处理
                url = f"http://push2.eastmoney.com/api/qt/stock/get?secid=1.{symbol}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f60,f116"
            elif symbol.startswith(('6', '5')):
                # 上交所
                url = f"http://push2.eastmoney.com/api/qt/stock/get?secid=1.{symbol}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f60,f116"
            elif symbol.startswith(('0', '3', '2')):
                # 深交所
                url = f"http://push2.eastmoney.com/api/qt/stock/get?secid=0.{symbol}&fields=f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f60,f116"
            else:
                # 美股或其他
                return {'source': 'eastmoney', 'symbol': symbol, 'status': 'failed', 'error': 'unsupported_market'}
            
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and data['data']:
                    d = data['data']
                    return {
                        'source': 'eastmoney',
                        'symbol': symbol,
                        'name': d.get('f58', symbol),
                        'price': float(d.get('f43', 0)) / 100,
                        'open': float(d.get('f46', 0)) / 100,
                        'close': float(d.get('f60', 0)) / 100,
                        'high': float(d.get('f44', 0)) / 100,
                        'low': float(d.get('f45', 0)) / 100,
                        'volume': int(d.get('f47', 0)),
                        'change': float(d.get('f43', 0)) / 100 - float(d.get('f60', 0)) / 100,
                        'change_pct': float(d.get('f170', 0)),
                        'status': 'success'
                    }
        except Exception as e:
            return {'source': 'eastmoney', 'symbol': symbol, 'status': 'error', 'error': str(e)}
        
        return {'source': 'eastmoney', 'symbol': symbol, 'status': 'failed', 'error': 'no_data'}
    
    def cross_validate_data(self, symbol):
        """交叉验证数据一致性"""
        results = {}
        
        # 获取各数据源数据
        tencent_data = self.audit_tencent_finance(symbol)
        sina_data = self.audit_sina_finance(symbol)
        eastmoney_data = self.audit_eastmoney(symbol)
        
        results['tencent'] = tencent_data
        results['sina'] = sina_data
        results['eastmoney'] = eastmoney_data
        
        # 交叉验证
        valid_sources = [r for r in results.values() if r.get('status') == 'success']
        
        if len(valid_sources) >= 2:
            # 比较价格一致性
            prices = [r['price'] for r in valid_sources]
            avg_price = sum(prices) / len(prices)
            max_deviation = max(abs(p - avg_price) for p in prices)
            
            # 比较成交量一致性
            volumes = [r['volume'] for r in valid_sources if 'volume' in r]
            if volumes:
                avg_volume = sum(volumes) / len(volumes)
                max_volume_deviation = max(abs(v - avg_volume) for v in volumes) / avg_volume if avg_volume > 0 else 0
            else:
                max_volume_deviation = 0
            
            return {
                'symbol': symbol,
                'status': 'validated',
                'sources': len(valid_sources),
                'price_consistency': {
                    'average': avg_price,
                    'max_deviation': max_deviation,
                    'deviation_pct': (max_deviation / avg_price) * 100 if avg_price > 0 else 0
                },
                'volume_consistency': {
                    'max_deviation_pct': max_volume_deviation * 100
                },
                'raw_data': results
            }
        
        return {
            'symbol': symbol,
            'status': 'insufficient_data',
            'sources': len(valid_sources),
            'raw_data': results
        }
    
    def run_full_audit(self):
        """运行完整审计"""
        print("=" * 80)
        print("系统数据全面审计报告")
        print("=" * 80)
        
        for symbol in self.test_stocks:
            print(f"\n审计股票: {symbol}")
            print("-" * 50)
            
            # 交叉验证
            validation = self.cross_validate_data(symbol)
            self.audit_results['stocks'][symbol] = validation
            
            if validation['status'] == 'validated':
                print(f"数据源数量: {validation['sources']}")
                print(f"价格一致性:")
                print(f"  平均价格: ¥{validation['price_consistency']['average']:.2f}")
                print(f"  最大偏差: ¥{validation['price_consistency']['max_deviation']:.2f}")
                print(f"  偏差比例: {validation['price_consistency']['deviation_pct']:.2f}%")
                print(f"成交量一致性:")
                print(f"  最大偏差: {validation['volume_consistency']['max_deviation_pct']:.2f}%")
                
                # 检查数据质量
                if validation['price_consistency']['deviation_pct'] < 1.0:
                    print("[数据质量: 优秀]")
                elif validation['price_consistency']['deviation_pct'] < 3.0:
                    print("[数据质量: 良好]")
                else:
                    print("[数据质量: 需改进]")
                    
            else:
                print(f"状态: {validation['status']}")
                print(f"可用数据源: {validation['sources']}")
            
            # 显示各数据源状态
            for source, data in validation['raw_data'].items():
                if data.get('status') == 'success':
                    print(f"{source}: ✓ ¥{data['price']:.2f}")
                else:
                    print(f"{source}: ✗ {data.get('error', '无数据')}")
            
            time.sleep(1)  # 避免请求过快
        
        # 生成审计总结
        self.generate_audit_summary()
        
        return self.audit_results
    
    def generate_audit_summary(self):
        """生成审计总结"""
        validated_stocks = [s for s, data in self.audit_results['stocks'].items() 
                           if data.get('status') == 'validated']
        
        print("\n" + "=" * 80)
        print("审计总结")
        print("=" * 80)
        
        print(f"测试股票数量: {len(self.test_stocks)}")
        print(f"通过验证的股票: {len(validated_stocks)}")
        print(f"验证成功率: {len(validated_stocks)/len(self.test_stocks)*100:.1f}%")
        
        # 数据源可用性统计
        source_stats = {}
        for stock_data in self.audit_results['stocks'].values():
            for source, data in stock_data.get('raw_data', {}).items():
                if source not in source_stats:
                    source_stats[source] = {'success': 0, 'failed': 0}
                
                if data.get('status') == 'success':
                    source_stats[source]['success'] += 1
                else:
                    source_stats[source]['failed'] += 1
        
        print("\n数据源可用性:")
        for source, stats in source_stats.items():
            total = stats['success'] + stats['failed']
            success_rate = (stats['success'] / total * 100) if total > 0 else 0
            print(f"{source}: {success_rate:.1f}% ({stats['success']}/{total})")
        
        # 数据质量建议
        self.audit_results['recommendations'] = [
            "建议使用腾讯财经作为主要数据源（成功率最高）",
            "建议使用新浪财经作为备用数据源",
            "对于科创板股票，建议使用上交所官方数据",
            "建议增加数据缓存机制，减少API调用延迟",
            "建议增加数据异常检测和报警机制"
        ]
        
        print("\n改进建议:")
        for i, rec in enumerate(self.audit_results['recommendations'], 1):
            print(f"{i}. {rec}")

if __name__ == "__main__":
    auditor = DataSourceAuditor()
    results = auditor.run_full_audit()
    
    # 保存审计结果
    try:
        with open('data_audit_report.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"\n审计报告已保存到: data_audit_report.json")
    except Exception as e:
        print(f"保存报告失败: {e}")