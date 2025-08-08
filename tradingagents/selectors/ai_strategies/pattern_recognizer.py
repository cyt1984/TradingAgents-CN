#!/usr/bin/env python3
"""
股票模式识别引擎
基于历史数据识别股票走势模式和特征
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import statistics
import math
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from tradingagents.utils.logging_manager import get_logger

logger = get_logger('agents')


class PatternType(Enum):
    """模式类型"""
    TREND_BULLISH = "trend_bullish"         # 看涨趋势
    TREND_BEARISH = "trend_bearish"         # 看跌趋势
    BREAKOUT_UPWARD = "breakout_upward"     # 向上突破
    BREAKOUT_DOWNWARD = "breakout_downward" # 向下突破
    REVERSAL_BULLISH = "reversal_bullish"   # 看涨反转
    REVERSAL_BEARISH = "reversal_bearish"   # 看跌反转
    CONSOLIDATION = "consolidation"         # 整理横盘
    MOMENTUM_STRONG = "momentum_strong"     # 强势动量
    MOMENTUM_WEAK = "momentum_weak"         # 弱势动量
    VOLUME_SPIKE = "volume_spike"           # 成交量异常
    VOLATILITY_HIGH = "volatility_high"     # 高波动率
    VOLATILITY_LOW = "volatility_low"       # 低波动率


@dataclass
class StockPattern:
    """股票模式"""
    pattern_type: PatternType               # 模式类型
    symbol: str                             # 股票代码
    confidence: float                       # 置信度 (0-1)
    strength: float                         # 强度 (0-100)
    duration_days: int                      # 持续天数
    start_date: datetime                    # 开始日期
    end_date: datetime                      # 结束日期
    key_metrics: Dict[str, float]           # 关键指标
    description: str                        # 模式描述
    prediction_horizon: int                 # 预测时间范围 (天)
    expected_direction: str                 # 预期方向
    risk_level: str                         # 风险级别
    similar_patterns: List[str]             # 相似模式历史


class PatternRecognizer:
    """模式识别引擎"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化模式识别引擎
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 模式识别参数
        self.recognition_params = {
            'trend_min_days': 5,            # 趋势最小天数
            'breakout_threshold': 0.03,     # 突破阈值 (3%)
            'volume_spike_factor': 2.0,     # 成交量异常因子
            'volatility_window': 20,        # 波动率计算窗口
            'momentum_window': 10,          # 动量计算窗口
            'consolidation_range': 0.05     # 整理区间阈值 (5%)
        }
        
        # 模式权重配置
        self.pattern_weights = {
            PatternType.TREND_BULLISH: 0.85,
            PatternType.TREND_BEARISH: 0.75,
            PatternType.BREAKOUT_UPWARD: 0.90,
            PatternType.BREAKOUT_DOWNWARD: 0.80,
            PatternType.REVERSAL_BULLISH: 0.70,
            PatternType.REVERSAL_BEARISH: 0.65,
            PatternType.CONSOLIDATION: 0.50,
            PatternType.MOMENTUM_STRONG: 0.80,
            PatternType.MOMENTUM_WEAK: 0.60
        }
        
        # 历史模式数据库
        self.pattern_database = {}
        
        # 预训练的聚类模型
        self.cluster_models = {}
        
        logger.info("模式识别引擎初始化完成")
        logger.info(f"   支持模式类型: {len(PatternType)} 种")
        logger.info(f"   识别参数: {len(self.recognition_params)} 个")

    def recognize_patterns(self, symbol: str, 
                         price_data: List[Dict[str, Any]],
                         volume_data: List[float] = None) -> List[StockPattern]:
        """
        识别股票模式
        
        Args:
            symbol: 股票代码
            price_data: 价格数据 (包含open, high, low, close)
            volume_data: 成交量数据
            
        Returns:
            识别到的模式列表
        """
        try:
            logger.info(f"🔍 [模式识别] 开始识别股票模式: {symbol}")
            
            if not price_data or len(price_data) < 10:
                logger.warning(f"⚠️ 价格数据不足，无法进行模式识别: {symbol}")
                return []
            
            patterns = []
            
            # 1. 趋势模式识别
            trend_patterns = self._recognize_trend_patterns(symbol, price_data)
            patterns.extend(trend_patterns)
            
            # 2. 突破模式识别
            breakout_patterns = self._recognize_breakout_patterns(symbol, price_data, volume_data)
            patterns.extend(breakout_patterns)
            
            # 3. 反转模式识别
            reversal_patterns = self._recognize_reversal_patterns(symbol, price_data, volume_data)
            patterns.extend(reversal_patterns)
            
            # 4. 整理模式识别
            consolidation_patterns = self._recognize_consolidation_patterns(symbol, price_data)
            patterns.extend(consolidation_patterns)
            
            # 5. 动量模式识别
            momentum_patterns = self._recognize_momentum_patterns(symbol, price_data, volume_data)
            patterns.extend(momentum_patterns)
            
            # 6. 成交量模式识别
            volume_patterns = self._recognize_volume_patterns(symbol, price_data, volume_data)
            patterns.extend(volume_patterns)
            
            # 7. 波动率模式识别
            volatility_patterns = self._recognize_volatility_patterns(symbol, price_data)
            patterns.extend(volatility_patterns)
            
            # 过滤和排序模式
            patterns = self._filter_and_rank_patterns(patterns)
            
            # 更新模式数据库
            self._update_pattern_database(symbol, patterns)
            
            logger.info(f"🔍 [模式识别] 完成模式识别: {symbol} - 发现 {len(patterns)} 个模式")
            return patterns
            
        except Exception as e:
            logger.error(f"❌ [模式识别] 识别失败: {symbol} - {str(e)}")
            return []

    def _recognize_trend_patterns(self, symbol: str, price_data: List[Dict[str, Any]]) -> List[StockPattern]:
        """识别趋势模式"""
        try:
            patterns = []
            closes = [float(p['close']) for p in price_data]
            
            if len(closes) < self.recognition_params['trend_min_days']:
                return patterns
            
            # 计算趋势线斜率
            x = np.arange(len(closes))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, closes)
            
            # 趋势强度
            r_squared = r_value ** 2
            
            # 价格变化幅度
            price_change_pct = (closes[-1] - closes[0]) / closes[0]
            
            # 判断趋势类型
            if slope > 0 and r_squared > 0.5 and price_change_pct > 0.02:
                # 看涨趋势
                pattern = StockPattern(
                    pattern_type=PatternType.TREND_BULLISH,
                    symbol=symbol,
                    confidence=min(0.95, r_squared + 0.1),
                    strength=min(100, abs(slope) * 100 / closes[0] * 1000),
                    duration_days=len(closes),
                    start_date=datetime.now() - timedelta(days=len(closes)-1),
                    end_date=datetime.now(),
                    key_metrics={
                        'slope': slope,
                        'r_squared': r_squared,
                        'price_change_pct': price_change_pct,
                        'p_value': p_value
                    },
                    description=f"看涨趋势，{len(closes)}天内上涨{price_change_pct:.2%}，趋势确定性{r_squared:.2%}",
                    prediction_horizon=5,
                    expected_direction="上涨",
                    risk_level="中等",
                    similar_patterns=[]
                )
                patterns.append(pattern)
                
            elif slope < 0 and r_squared > 0.5 and price_change_pct < -0.02:
                # 看跌趋势
                pattern = StockPattern(
                    pattern_type=PatternType.TREND_BEARISH,
                    symbol=symbol,
                    confidence=min(0.95, r_squared + 0.1),
                    strength=min(100, abs(slope) * 100 / closes[0] * 1000),
                    duration_days=len(closes),
                    start_date=datetime.now() - timedelta(days=len(closes)-1),
                    end_date=datetime.now(),
                    key_metrics={
                        'slope': slope,
                        'r_squared': r_squared,
                        'price_change_pct': price_change_pct,
                        'p_value': p_value
                    },
                    description=f"看跌趋势，{len(closes)}天内下跌{abs(price_change_pct):.2%}，趋势确定性{r_squared:.2%}",
                    prediction_horizon=5,
                    expected_direction="下跌",
                    risk_level="中高",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ 趋势模式识别失败: {e}")
            return []

    def _recognize_breakout_patterns(self, symbol: str, 
                                   price_data: List[Dict[str, Any]],
                                   volume_data: List[float] = None) -> List[StockPattern]:
        """识别突破模式"""
        try:
            patterns = []
            
            if len(price_data) < 20:
                return patterns
            
            closes = [float(p['close']) for p in price_data]
            highs = [float(p['high']) for p in price_data]
            lows = [float(p['low']) for p in price_data]
            
            # 计算近期阻力位和支撑位
            recent_period = min(20, len(closes))
            recent_highs = highs[-recent_period:]
            recent_lows = lows[-recent_period:]
            
            resistance_level = max(recent_highs[:-1])  # 排除最新价格
            support_level = min(recent_lows[:-1])
            
            current_close = closes[-1]
            breakout_threshold = self.recognition_params['breakout_threshold']
            
            # 向上突破
            if current_close > resistance_level * (1 + breakout_threshold):
                # 计算突破强度
                breakout_strength = (current_close - resistance_level) / resistance_level * 100
                
                # 成交量确认
                volume_confirmation = 0.7  # 默认确认度
                if volume_data and len(volume_data) >= recent_period:
                    recent_volumes = volume_data[-recent_period:]
                    avg_volume = statistics.mean(recent_volumes[:-1])
                    current_volume = volume_data[-1]
                    volume_confirmation = min(1.0, current_volume / avg_volume / 1.5)
                
                pattern = StockPattern(
                    pattern_type=PatternType.BREAKOUT_UPWARD,
                    symbol=symbol,
                    confidence=min(0.95, 0.6 + volume_confirmation * 0.3),
                    strength=min(100, breakout_strength * 10),
                    duration_days=1,  # 突破通常是单日事件
                    start_date=datetime.now(),
                    end_date=datetime.now(),
                    key_metrics={
                        'resistance_level': resistance_level,
                        'current_price': current_close,
                        'breakout_percentage': breakout_strength,
                        'volume_confirmation': volume_confirmation
                    },
                    description=f"向上突破阻力位{resistance_level:.2f}，突破幅度{breakout_strength:.2f}%",
                    prediction_horizon=3,
                    expected_direction="继续上涨",
                    risk_level="中等",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            # 向下跌破
            elif current_close < support_level * (1 - breakout_threshold):
                # 计算跌破强度
                breakdown_strength = (support_level - current_close) / support_level * 100
                
                # 成交量确认
                volume_confirmation = 0.7
                if volume_data and len(volume_data) >= recent_period:
                    recent_volumes = volume_data[-recent_period:]
                    avg_volume = statistics.mean(recent_volumes[:-1])
                    current_volume = volume_data[-1]
                    volume_confirmation = min(1.0, current_volume / avg_volume / 1.5)
                
                pattern = StockPattern(
                    pattern_type=PatternType.BREAKOUT_DOWNWARD,
                    symbol=symbol,
                    confidence=min(0.95, 0.6 + volume_confirmation * 0.3),
                    strength=min(100, breakdown_strength * 10),
                    duration_days=1,
                    start_date=datetime.now(),
                    end_date=datetime.now(),
                    key_metrics={
                        'support_level': support_level,
                        'current_price': current_close,
                        'breakdown_percentage': breakdown_strength,
                        'volume_confirmation': volume_confirmation
                    },
                    description=f"向下跌破支撑位{support_level:.2f}，跌破幅度{breakdown_strength:.2f}%",
                    prediction_horizon=3,
                    expected_direction="继续下跌",
                    risk_level="高",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ 突破模式识别失败: {e}")
            return []

    def _recognize_reversal_patterns(self, symbol: str, 
                                   price_data: List[Dict[str, Any]],
                                   volume_data: List[float] = None) -> List[StockPattern]:
        """识别反转模式"""
        try:
            patterns = []
            
            if len(price_data) < 10:
                return patterns
            
            closes = [float(p['close']) for p in price_data]
            
            # 寻找可能的反转点
            # 简化实现：基于价格动量变化
            if len(closes) >= 5:
                # 计算短期和中期动量
                short_momentum = (closes[-1] - closes[-3]) / closes[-3]
                mid_momentum = (closes[-1] - closes[-5]) / closes[-5]
                
                # 反转信号：短期动量与中期动量方向相反
                if short_momentum > 0.01 and mid_momentum < -0.02:
                    # 看涨反转
                    reversal_strength = abs(short_momentum - mid_momentum) * 100
                    
                    pattern = StockPattern(
                        pattern_type=PatternType.REVERSAL_BULLISH,
                        symbol=symbol,
                        confidence=min(0.8, 0.5 + reversal_strength / 10),
                        strength=min(100, reversal_strength * 20),
                        duration_days=5,
                        start_date=datetime.now() - timedelta(days=4),
                        end_date=datetime.now(),
                        key_metrics={
                            'short_momentum': short_momentum,
                            'mid_momentum': mid_momentum,
                            'reversal_strength': reversal_strength
                        },
                        description=f"看涨反转信号，短期动量{short_momentum:.2%}，中期动量{mid_momentum:.2%}",
                        prediction_horizon=5,
                        expected_direction="反转上涨",
                        risk_level="中高",
                        similar_patterns=[]
                    )
                    patterns.append(pattern)
                
                elif short_momentum < -0.01 and mid_momentum > 0.02:
                    # 看跌反转
                    reversal_strength = abs(short_momentum - mid_momentum) * 100
                    
                    pattern = StockPattern(
                        pattern_type=PatternType.REVERSAL_BEARISH,
                        symbol=symbol,
                        confidence=min(0.8, 0.5 + reversal_strength / 10),
                        strength=min(100, reversal_strength * 20),
                        duration_days=5,
                        start_date=datetime.now() - timedelta(days=4),
                        end_date=datetime.now(),
                        key_metrics={
                            'short_momentum': short_momentum,
                            'mid_momentum': mid_momentum,
                            'reversal_strength': reversal_strength
                        },
                        description=f"看跌反转信号，短期动量{short_momentum:.2%}，中期动量{mid_momentum:.2%}",
                        prediction_horizon=5,
                        expected_direction="反转下跌",
                        risk_level="高",
                        similar_patterns=[]
                    )
                    patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ 反转模式识别失败: {e}")
            return []

    def _recognize_consolidation_patterns(self, symbol: str, price_data: List[Dict[str, Any]]) -> List[StockPattern]:
        """识别整理模式"""
        try:
            patterns = []
            
            if len(price_data) < 10:
                return patterns
            
            closes = [float(p['close']) for p in price_data]
            
            # 计算价格波动范围
            max_price = max(closes)
            min_price = min(closes)
            price_range = (max_price - min_price) / statistics.mean(closes)
            
            # 如果波动范围小于阈值，识别为整理模式
            consolidation_threshold = self.recognition_params['consolidation_range']
            
            if price_range < consolidation_threshold:
                # 计算整理强度
                volatility = statistics.stdev(closes) / statistics.mean(closes)
                consolidation_strength = (consolidation_threshold - price_range) / consolidation_threshold * 100
                
                pattern = StockPattern(
                    pattern_type=PatternType.CONSOLIDATION,
                    symbol=symbol,
                    confidence=min(0.9, 0.6 + (1 - volatility) * 0.3),
                    strength=min(100, consolidation_strength),
                    duration_days=len(closes),
                    start_date=datetime.now() - timedelta(days=len(closes)-1),
                    end_date=datetime.now(),
                    key_metrics={
                        'price_range': price_range,
                        'volatility': volatility,
                        'max_price': max_price,
                        'min_price': min_price,
                        'consolidation_strength': consolidation_strength
                    },
                    description=f"横盘整理，{len(closes)}天内波动范围{price_range:.2%}",
                    prediction_horizon=3,
                    expected_direction="待突破",
                    risk_level="低",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ 整理模式识别失败: {e}")
            return []

    def _recognize_momentum_patterns(self, symbol: str, 
                                   price_data: List[Dict[str, Any]],
                                   volume_data: List[float] = None) -> List[StockPattern]:
        """识别动量模式"""
        try:
            patterns = []
            
            momentum_window = self.recognition_params['momentum_window']
            if len(price_data) < momentum_window:
                return patterns
            
            closes = [float(p['close']) for p in price_data]
            
            # 计算动量指标
            momentum = (closes[-1] - closes[-momentum_window]) / closes[-momentum_window]
            
            # 计算动量加速度
            if len(closes) >= momentum_window * 2:
                prev_momentum = (closes[-momentum_window] - closes[-momentum_window*2]) / closes[-momentum_window*2]
                momentum_acceleration = momentum - prev_momentum
            else:
                momentum_acceleration = 0
            
            # 强势动量
            if momentum > 0.05 and momentum_acceleration > 0:
                pattern = StockPattern(
                    pattern_type=PatternType.MOMENTUM_STRONG,
                    symbol=symbol,
                    confidence=min(0.9, 0.6 + abs(momentum) * 2),
                    strength=min(100, abs(momentum) * 100 * 2),
                    duration_days=momentum_window,
                    start_date=datetime.now() - timedelta(days=momentum_window-1),
                    end_date=datetime.now(),
                    key_metrics={
                        'momentum': momentum,
                        'momentum_acceleration': momentum_acceleration,
                        'momentum_window': momentum_window
                    },
                    description=f"强势上涨动量，{momentum_window}天涨幅{momentum:.2%}",
                    prediction_horizon=3,
                    expected_direction="持续上涨",
                    risk_level="中等",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            # 弱势动量
            elif momentum < -0.05 and momentum_acceleration < 0:
                pattern = StockPattern(
                    pattern_type=PatternType.MOMENTUM_WEAK,
                    symbol=symbol,
                    confidence=min(0.9, 0.6 + abs(momentum) * 2),
                    strength=min(100, abs(momentum) * 100 * 2),
                    duration_days=momentum_window,
                    start_date=datetime.now() - timedelta(days=momentum_window-1),
                    end_date=datetime.now(),
                    key_metrics={
                        'momentum': momentum,
                        'momentum_acceleration': momentum_acceleration,
                        'momentum_window': momentum_window
                    },
                    description=f"弱势下跌动量，{momentum_window}天跌幅{abs(momentum):.2%}",
                    prediction_horizon=3,
                    expected_direction="持续下跌",
                    risk_level="高",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ 动量模式识别失败: {e}")
            return []

    def _recognize_volume_patterns(self, symbol: str, 
                                 price_data: List[Dict[str, Any]],
                                 volume_data: List[float] = None) -> List[StockPattern]:
        """识别成交量模式"""
        try:
            patterns = []
            
            if not volume_data or len(volume_data) < 10:
                return patterns
            
            # 计算成交量异常
            recent_volume = volume_data[-1]
            avg_volume = statistics.mean(volume_data[:-1])
            
            volume_spike_factor = self.recognition_params['volume_spike_factor']
            
            if recent_volume > avg_volume * volume_spike_factor:
                # 成交量异常放大
                spike_ratio = recent_volume / avg_volume
                
                pattern = StockPattern(
                    pattern_type=PatternType.VOLUME_SPIKE,
                    symbol=symbol,
                    confidence=min(0.95, 0.7 + min(0.2, (spike_ratio - volume_spike_factor) * 0.1)),
                    strength=min(100, (spike_ratio - 1) * 20),
                    duration_days=1,
                    start_date=datetime.now(),
                    end_date=datetime.now(),
                    key_metrics={
                        'current_volume': recent_volume,
                        'average_volume': avg_volume,
                        'spike_ratio': spike_ratio
                    },
                    description=f"成交量异常放大{spike_ratio:.1f}倍",
                    prediction_horizon=1,
                    expected_direction="关注变盘",
                    risk_level="中等",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ 成交量模式识别失败: {e}")
            return []

    def _recognize_volatility_patterns(self, symbol: str, price_data: List[Dict[str, Any]]) -> List[StockPattern]:
        """识别波动率模式"""
        try:
            patterns = []
            
            volatility_window = self.recognition_params['volatility_window']
            if len(price_data) < volatility_window:
                return patterns
            
            closes = [float(p['close']) for p in price_data]
            
            # 计算波动率
            returns = [(closes[i] - closes[i-1]) / closes[i-1] for i in range(1, len(closes))]
            volatility = statistics.stdev(returns[-volatility_window:]) * math.sqrt(252)  # 年化波动率
            
            # 计算历史平均波动率
            if len(returns) > volatility_window * 2:
                hist_volatility = statistics.stdev(returns[:-volatility_window]) * math.sqrt(252)
                volatility_ratio = volatility / hist_volatility if hist_volatility > 0 else 1
            else:
                volatility_ratio = 1
            
            # 高波动率
            if volatility_ratio > 1.5:
                pattern = StockPattern(
                    pattern_type=PatternType.VOLATILITY_HIGH,
                    symbol=symbol,
                    confidence=min(0.9, 0.6 + min(0.3, (volatility_ratio - 1.5) * 0.2)),
                    strength=min(100, (volatility_ratio - 1) * 30),
                    duration_days=volatility_window,
                    start_date=datetime.now() - timedelta(days=volatility_window-1),
                    end_date=datetime.now(),
                    key_metrics={
                        'current_volatility': volatility,
                        'historical_volatility': hist_volatility,
                        'volatility_ratio': volatility_ratio
                    },
                    description=f"高波动率期，当前年化波动率{volatility:.1%}",
                    prediction_horizon=5,
                    expected_direction="波动加剧",
                    risk_level="高",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            # 低波动率
            elif volatility_ratio < 0.7:
                pattern = StockPattern(
                    pattern_type=PatternType.VOLATILITY_LOW,
                    symbol=symbol,
                    confidence=min(0.9, 0.6 + min(0.3, (0.7 - volatility_ratio) * 0.4)),
                    strength=min(100, (1 - volatility_ratio) * 50),
                    duration_days=volatility_window,
                    start_date=datetime.now() - timedelta(days=volatility_window-1),
                    end_date=datetime.now(),
                    key_metrics={
                        'current_volatility': volatility,
                        'historical_volatility': hist_volatility,
                        'volatility_ratio': volatility_ratio
                    },
                    description=f"低波动率期，当前年化波动率{volatility:.1%}",
                    prediction_horizon=5,
                    expected_direction="待突破",
                    risk_level="低",
                    similar_patterns=[]
                )
                patterns.append(pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"❌ 波动率模式识别失败: {e}")
            return []

    def _filter_and_rank_patterns(self, patterns: List[StockPattern]) -> List[StockPattern]:
        """过滤和排序模式"""
        try:
            if not patterns:
                return patterns
            
            # 按置信度和强度排序
            patterns.sort(key=lambda p: (p.confidence * self.pattern_weights.get(p.pattern_type, 0.5) + 
                                      p.strength / 100) / 2, reverse=True)
            
            # 去重相似模式
            filtered_patterns = []
            seen_types = set()
            
            for pattern in patterns:
                if pattern.pattern_type not in seen_types:
                    filtered_patterns.append(pattern)
                    seen_types.add(pattern.pattern_type)
                elif len(filtered_patterns) < 5:  # 最多保留5个模式
                    filtered_patterns.append(pattern)
            
            return filtered_patterns[:10]  # 最多返回10个模式
            
        except Exception as e:
            logger.error(f"❌ 模式过滤排序失败: {e}")
            return patterns

    def _update_pattern_database(self, symbol: str, patterns: List[StockPattern]):
        """更新模式数据库"""
        try:
            if symbol not in self.pattern_database:
                self.pattern_database[symbol] = []
            
            # 添加新模式
            for pattern in patterns:
                self.pattern_database[symbol].append({
                    'timestamp': pattern.end_date,
                    'pattern_type': pattern.pattern_type.value,
                    'confidence': pattern.confidence,
                    'strength': pattern.strength,
                    'description': pattern.description
                })
            
            # 保持最近50条记录
            if len(self.pattern_database[symbol]) > 50:
                self.pattern_database[symbol] = self.pattern_database[symbol][-50:]
                
        except Exception as e:
            logger.debug(f"更新模式数据库失败: {e}")

    def get_pattern_history(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取模式历史"""
        try:
            if symbol not in self.pattern_database:
                return []
            
            cutoff_time = datetime.now() - timedelta(days=days)
            
            recent_patterns = [
                p for p in self.pattern_database[symbol]
                if p['timestamp'] >= cutoff_time
            ]
            
            return recent_patterns
            
        except Exception as e:
            logger.error(f"获取模式历史失败: {e}")
            return []

    def predict_next_patterns(self, symbol: str, 
                            current_patterns: List[StockPattern]) -> Dict[str, Any]:
        """基于当前模式预测下一步走势"""
        try:
            if not current_patterns:
                return {'prediction': '无法预测', 'confidence': 0.0}
            
            # 简化预测逻辑：基于最强模式
            strongest_pattern = max(current_patterns, 
                                  key=lambda p: p.confidence * p.strength / 100)
            
            # 基于模式类型预测
            predictions = {
                PatternType.TREND_BULLISH: {'direction': '继续上涨', 'probability': 0.75},
                PatternType.TREND_BEARISH: {'direction': '继续下跌', 'probability': 0.70},
                PatternType.BREAKOUT_UPWARD: {'direction': '加速上涨', 'probability': 0.80},
                PatternType.BREAKOUT_DOWNWARD: {'direction': '加速下跌', 'probability': 0.75},
                PatternType.REVERSAL_BULLISH: {'direction': '反转上涨', 'probability': 0.65},
                PatternType.REVERSAL_BEARISH: {'direction': '反转下跌', 'probability': 0.60},
                PatternType.CONSOLIDATION: {'direction': '继续整理', 'probability': 0.70},
                PatternType.MOMENTUM_STRONG: {'direction': '动量延续', 'probability': 0.70}
            }
            
            prediction_info = predictions.get(strongest_pattern.pattern_type, 
                                            {'direction': '不确定', 'probability': 0.5})
            
            return {
                'symbol': symbol,
                'prediction': prediction_info['direction'],
                'confidence': prediction_info['probability'] * strongest_pattern.confidence,
                'based_on_pattern': strongest_pattern.pattern_type.value,
                'time_horizon': strongest_pattern.prediction_horizon,
                'risk_level': strongest_pattern.risk_level
            }
            
        except Exception as e:
            logger.error(f"模式预测失败: {e}")
            return {'prediction': '预测失败', 'confidence': 0.0, 'error': str(e)}