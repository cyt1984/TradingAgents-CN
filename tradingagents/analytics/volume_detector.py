"""
成交量异动检测模块
检测成交量异常、换手率异动、资金流向等
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class VolumeAnomaly:
    """成交量异动数据类"""
    symbol: str
    anomaly_score: float
    volume_ratio: float
    turnover_ratio: float
    anomaly_type: str
    timestamp: datetime
    details: Dict


class VolumeAnomalyDetector:
    """成交量异动检测器"""
    
    def __init__(self):
        self.base_url = "https://push2.eastmoney.com/api"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def detect_anomaly(self, symbol: str, days: int = 20) -> Dict:
        """
        检测成交量异动
        
        Args:
            symbol: 股票代码
            days: 分析天数
            
        Returns:
            异动检测结果
        """
        try:
            logger.info(f"[ANALYZE] 开始检测 {symbol} 成交量异动...")
            
            # 获取历史数据
            historical_data = self._get_historical_data(symbol, days + 5)
            if not historical_data:
                return self._get_empty_result(symbol)
            
            df = pd.DataFrame(historical_data)
            if len(df) < days:
                return self._get_empty_result(symbol)
            
            # 计算各种指标
            volume_analysis = self._analyze_volume_patterns(df)
            turnover_analysis = self._analyze_turnover_patterns(df)
            flow_analysis = self._analyze_money_flow(symbol)
            
            # 计算综合异动得分
            anomaly_score = self._calculate_anomaly_score(
                volume_analysis, turnover_analysis, flow_analysis
            )
            
            # 生成详细结果
            result = {
                'symbol': symbol,
                'anomaly_score': anomaly_score,
                'anomaly_level': self._get_anomaly_level(anomaly_score),
                'volume_analysis': volume_analysis,
                'turnover_analysis': turnover_analysis,
                'money_flow': flow_analysis,
                'alerts': self._generate_alerts(volume_analysis, turnover_analysis, flow_analysis),
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"[COMPLETE] {symbol} 成交量异动检测完成: 得分{anomaly_score:.1f}")
            return result
            
        except Exception as e:
            logger.error(f"[ERROR] 成交量异动检测失败 {symbol}: {e}")
            return self._get_error_result(symbol, str(e))
    
    def _get_historical_data(self, symbol: str, days: int) -> List[Dict]:
        """获取历史交易数据"""
        try:
            # 东方财富API获取历史数据
            market = '1' if symbol.startswith(('6', '5', '688')) else '0'
            url = f"{self.base_url}/qt/stock/kline/get"
            params = {
                'secid': f'{market}.{symbol}',
                'fields1': 'f1,f2,f3,f4,f5',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
                'klt': '101',  # 日线
                'fqt': '1',
                'end': '20500101',
                'lmt': str(days)
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    klines = data['data'].get('klines', [])
                    historical_data = []
                    
                    for kline in klines:
                        items = kline.split(',')
                        if len(items) >= 6:
                            historical_data.append({
                                'date': items[0],
                                'open': float(items[1]),
                                'close': float(items[2]),
                                'high': float(items[3]),
                                'low': float(items[4]),
                                'volume': int(items[5]),
                                'turnover': float(items[6]) if len(items) > 6 else 0
                            })
                    
                    return historical_data
            
        except Exception as e:
            logger.error(f"[ERROR] 历史数据获取失败 {symbol}: {e}")
        
        return []
    
    def _analyze_volume_patterns(self, df: pd.DataFrame) -> Dict:
        """分析成交量模式"""
        try:
            df = df.sort_values('date').reset_index(drop=True)
            
            # 计算基础指标
            df['volume_ma5'] = df['volume'].rolling(window=5).mean()
            df['volume_ma10'] = df['volume'].rolling(window=10).mean()
            df['volume_ma20'] = df['volume'].rolling(window=20).mean()
            
            # 计算成交量比率
            df['volume_ratio_5'] = df['volume'] / df['volume_ma5']
            df['volume_ratio_10'] = df['volume'] / df['volume_ma10']
            df['volume_ratio_20'] = df['volume'] / df['volume_ma20']
            
            # 最新数据
            latest = df.iloc[-1]
            
            # 异动检测
            volume_anomaly = {
                'latest_volume': latest['volume'],
                'volume_ratio_5': latest['volume_ratio_5'],
                'volume_ratio_10': latest['volume_ratio_10'],
                'volume_ratio_20': latest['volume_ratio_20'],
                'is_anomaly_5': latest['volume_ratio_5'] > 2.0,
                'is_anomaly_10': latest['volume_ratio_10'] > 2.5,
                'is_anomaly_20': latest['volume_ratio_20'] > 3.0,
                'anomaly_strength': max(
                    latest['volume_ratio_5'] - 1,
                    latest['volume_ratio_10'] - 1,
                    latest['volume_ratio_20'] - 1
                )
            }
            
            # 成交量趋势
            recent_volumes = df['volume'].tail(5).values
            volume_trend = np.polyfit(range(len(recent_volumes)), recent_volumes, 1)[0]
            volume_anomaly['trend_direction'] = 'up' if volume_trend > 0 else 'down'
            volume_anomaly['trend_strength'] = abs(volume_trend) / np.mean(recent_volumes)
            
            return volume_anomaly
            
        except Exception as e:
            logger.error(f"[ERROR] 成交量模式分析失败: {e}")
            return {}
    
    def _analyze_turnover_patterns(self, df: pd.DataFrame) -> Dict:
        """分析换手率模式"""
        try:
            # 计算换手率 (假设流通股本为1亿股，实际应该从API获取)
            circulation_shares = 100_000_000  # 需要实际数据
            df['turnover_rate'] = (df['volume'] / circulation_shares) * 100
            
            # 计算换手率移动平均
            df['turnover_ma5'] = df['turnover_rate'].rolling(window=5).mean()
            df['turnover_ma10'] = df['turnover_rate'].rolling(window=10).mean()
            df['turnover_ma20'] = df['turnover_rate'].rolling(window=20).mean()
            
            latest = df.iloc[-1]
            
            turnover_analysis = {
                'latest_turnover': latest['turnover_rate'],
                'turnover_ma5': latest['turnover_ma5'],
                'turnover_ma10': latest['turnover_ma10'],
                'turnover_ma20': latest['turnover_ma20'],
                'turnover_ratio_5': latest['turnover_rate'] / max(latest['turnover_ma5'], 0.01),
                'turnover_ratio_10': latest['turnover_rate'] / max(latest['turnover_ma10'], 0.01),
                'is_high_turnover': latest['turnover_rate'] > 10,  # 换手率高于10%
                'is_low_turnover': latest['turnover_rate'] < 1   # 换手率低于1%
            }
            
            # 换手率异常检测
            turnover_std = df['turnover_rate'].rolling(window=20).std().iloc[-1]
            turnover_mean = df['turnover_ma20'].iloc[-1]
            
            if turnover_std > 0:
                z_score = (latest['turnover_rate'] - turnover_mean) / turnover_std
                turnover_analysis['turnover_z_score'] = z_score
                turnover_analysis['is_turnover_anomaly'] = abs(z_score) > 2
            else:
                turnover_analysis['turnover_z_score'] = 0
                turnover_analysis['is_turnover_anomaly'] = False
            
            return turnover_analysis
            
        except Exception as e:
            logger.error(f"[ERROR] 换手率分析失败: {e}")
            return {}
    
    def _analyze_money_flow(self, symbol: str) -> Dict:
        """分析资金流向"""
        try:
            # 获取资金流向数据
            market = '1' if symbol.startswith(('6', '5', '688')) else '0'
            url = f"{self.base_url}/qt/stock/fflow/kline/get"
            params = {
                'secid': f'{market}.{symbol}',
                'lmt': '10',
                'klt': '101',
                'fields1': 'f1,f2,f3,f7',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f62,f63,f64,f65'
            }
            
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    klines = data['data'].get('klines', [])
                    if klines:
                        latest = klines[-1].split(',')
                        
                        # 解析资金流向数据
                        money_flow = {
                            'main_net_inflow': float(latest[1]) if len(latest) > 1 else 0,
                            'main_net_ratio': float(latest[2]) if len(latest) > 2 else 0,
                            'large_net_inflow': float(latest[3]) if len(latest) > 3 else 0,
                            'large_net_ratio': float(latest[4]) if len(latest) > 4 else 0,
                            'medium_net_inflow': float(latest[5]) if len(latest) > 5 else 0,
                            'medium_net_ratio': float(latest[6]) if len(latest) > 6 else 0,
                            'small_net_inflow': float(latest[7]) if len(latest) > 7 else 0,
                            'small_net_ratio': float(latest[8]) if len(latest) > 8 else 0
                        }
                        
                        # 计算散户-机构博弈指标
                        money_flow['retail_institutional_ratio'] = (
                            money_flow['small_net_inflow'] / max(abs(money_flow['main_net_inflow']), 1)
                        )
                        
                        # 资金流向异常检测
                        money_flow['is_main_inflow'] = money_flow['main_net_inflow'] > 0
                        money_flow['is_retail_outflow'] = money_flow['small_net_inflow'] < 0
                        money_flow['is_divergence'] = (
                            money_flow['main_net_inflow'] > 0 and money_flow['small_net_inflow'] < 0
                        ) or (
                            money_flow['main_net_inflow'] < 0 and money_flow['small_net_inflow'] > 0
                        )
                        
                        return money_flow
            
        except Exception as e:
            logger.error(f"[ERROR] 资金流向分析失败 {symbol}: {e}")
        
        return {}
    
    def _calculate_anomaly_score(self, volume_data: Dict, turnover_data: Dict, flow_data: Dict) -> float:
        """计算综合异动得分"""
        try:
            score = 0
            
            # 成交量异动得分
            if volume_data:
                volume_score = min(
                    max(volume_data.get('anomaly_strength', 0) * 20, 0),
                    40
                )
                score += volume_score
            
            # 换手率异动得分
            if turnover_data:
                z_score = abs(turnover_data.get('turnover_z_score', 0))
                turnover_score = min(z_score * 15, 30)
                score += turnover_score
            
            # 资金流向得分
            if flow_data:
                # 大单流入强度
                main_ratio = abs(flow_data.get('main_net_ratio', 0))
                flow_score = min(main_ratio * 2, 20)
                score += flow_score
                
                # 散户-机构背离
                if flow_data.get('is_divergence', False):
                    score += 10
            
            return min(score, 100)
            
        except Exception as e:
            logger.error(f"[ERROR] 异动得分计算失败: {e}")
            return 0
    
    def _get_anomaly_level(self, score: float) -> str:
        """根据得分返回异动等级"""
        if score >= 80:
            return "[CRITICAL] 极高异动"
        elif score >= 60:
            return "[WARN] 高度异动"
        elif score >= 40:
            return "[ANALYZE] 中度异动"
        elif score >= 20:
            return "[DATA] 轻度异动"
        else:
            return "[OK] 正常"
    
    def _generate_alerts(self, volume_data: Dict, turnover_data: Dict, flow_data: Dict) -> List[Dict]:
        """生成异动预警"""
        alerts = []
        
        try:
            # 成交量预警
            if volume_data.get('is_anomaly_5', False):
                alerts.append({
                    'type': 'volume_spike',
                    'level': 'high',
                    'message': f"成交量突增{volume_data.get('volume_ratio_5', 0):.1f}倍",
                    'data': volume_data
                })
            
            # 换手率预警
            if turnover_data.get('is_turnover_anomaly', False):
                z_score = turnover_data.get('turnover_z_score', 0)
                direction = "异常高" if z_score > 0 else "异常低"
                alerts.append({
                    'type': 'turnover_anomaly',
                    'level': 'medium',
                    'message': f"换手率{direction}(Z值{z_score:.1f})",
                    'data': turnover_data
                })
            
            # 资金流向预警
            if flow_data.get('is_divergence', False):
                main_flow = flow_data.get('main_net_inflow', 0)
                retail_flow = flow_data.get('small_net_inflow', 0)
                alerts.append({
                    'type': 'flow_divergence',
                    'level': 'medium',
                    'message': f"散户-机构资金流向背离: 主力{main_flow:+.0f}万, 散户{retail_flow:+.0f}万",
                    'data': flow_data
                })
                
        except Exception as e:
            logger.error(f"[ERROR] 预警生成失败: {e}")
        
        return alerts
    
    def _get_empty_result(self, symbol: str) -> Dict:
        """获取空结果"""
        return {
            'symbol': symbol,
            'anomaly_score': 0,
            'anomaly_level': '数据不足',
            'volume_analysis': {},
            'turnover_analysis': {},
            'money_flow': {},
            'alerts': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_error_result(self, symbol: str, error: str) -> Dict:
        """获取错误结果"""
        return {
            'symbol': symbol,
            'error': error,
            'timestamp': datetime.now().isoformat(),
            'status': 'error'
        }
    
    def get_volume_ranking(self, symbols: List[str]) -> List[Dict]:
        """获取成交量异动排行榜"""
        results = []
        
        for symbol in symbols:
            try:
                result = self.detect_anomaly(symbol)
                if result.get('anomaly_score', 0) > 0:
                    results.append({
                        'symbol': symbol,
                        'anomaly_score': result['anomaly_score'],
                        'anomaly_level': result['anomaly_level'],
                        'volume_ratio': result['volume_analysis'].get('volume_ratio_5', 0),
                        'turnover_rate': result['turnover_analysis'].get('latest_turnover', 0)
                    })
            except Exception as e:
                logger.error(f"[ERROR] 排行榜生成失败 {symbol}: {e}")
        
        # 按异动得分排序
        results.sort(key=lambda x: x['anomaly_score'], reverse=True)
        return results