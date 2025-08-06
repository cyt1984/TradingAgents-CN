#!/usr/bin/env python3
"""
研究所分析师报告数据适配器
集成多个券商研报数据源，提供标准化的研报数据接口
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import re
from dataclasses import dataclass

# 导入日志模块
from tradingagents.utils.logging_manager import get_logger
logger = get_logger('agents')

# 导入股票工具类
from tradingagents.utils.stock_utils import StockUtils


@dataclass
class ResearchReport:
    """研报数据结构"""
    title: str                    # 研报标题
    analyst: str                  # 分析师
    institution: str              # 券商机构
    publish_date: str             # 发布日期
    rating: str                   # 评级 (买入/卖出/持有等)
    target_price: Optional[float] # 目标价
    current_price: Optional[float] # 当前价
    summary: str                  # 摘要
    key_points: List[str]         # 关键观点
    pe_forecast: Optional[float]  # 预测PE
    revenue_growth: Optional[float] # 收入增长预测
    profit_growth: Optional[float]  # 利润增长预测
    source: str                   # 数据源
    confidence_level: float       # 可信度评分 (0-1)


class ResearchReportProvider:
    """研报数据提供器基类"""
    
    def __init__(self):
        self.name = "BaseProvider"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def get_reports(self, ticker: str, limit: int = 10) -> List[ResearchReport]:
        """获取研报数据"""
        raise NotImplementedError
    
    def _parse_rating(self, rating_text: str) -> str:
        """标准化评级"""
        rating_text = rating_text.upper()
        
        # 买入类
        if any(keyword in rating_text for keyword in ['买入', 'BUY', '推荐', '增持', '强推']):
            return '买入'
        # 卖出类
        elif any(keyword in rating_text for keyword in ['卖出', 'SELL', '减持']):
            return '卖出'
        # 持有类
        elif any(keyword in rating_text for keyword in ['持有', 'HOLD', '中性']):
            return '持有'
        else:
            return '未知'
    
    def _extract_price(self, text: str) -> Optional[float]:
        """从文本中提取价格"""
        try:
            # 匹配价格模式：XX元、XX.XX元、$XX.XX等
            price_patterns = [
                r'(\d+\.?\d*)\s*元',
                r'目标价[：:]\s*(\d+\.?\d*)',
                r'\$(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*[美港]?元'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, text)
                if match:
                    return float(match.group(1))
            return None
        except:
            return None


class EastMoneyResearchProvider(ResearchReportProvider):
    """东方财富研报数据提供器 - 使用真实HTTP API"""
    
    def __init__(self):
        super().__init__()
        self.name = "东方财富"
        self.api_base_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
        
        # API请求配置
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://data.eastmoney.com/',
            'Accept': 'text/javascript, application/javascript, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        self.timeout = 30
        
    def get_reports(self, ticker: str, limit: int = 10) -> List[ResearchReport]:
        """获取东方财富研报数据 - 支持多种API"""
        try:
            logger.info(f"🔍 开始从东方财富获取研报: {ticker}")
            
            # 格式化股票代码
            formatted_ticker = self._format_ticker(ticker)
            if not formatted_ticker:
                logger.warning(f"⚠️ 股票代码格式化失败: {ticker}")
                return []
            
            all_reports = []
            
            # 1. 尝试获取机构调研数据 (主要数据源)
            survey_reports = self._get_survey_reports(formatted_ticker, limit)
            if survey_reports:
                all_reports.extend(survey_reports)
                logger.info(f"✅ 东方财富机构调研数据获取成功: {len(survey_reports)} 条")
            
            # 2. 如果调研数据不足，尝试获取价值分析数据
            if len(all_reports) < limit:
                value_reports = self._get_value_analysis_reports(formatted_ticker, limit - len(all_reports))
                if value_reports:
                    all_reports.extend(value_reports)
                    logger.info(f"✅ 东方财富价值分析数据获取成功: {len(value_reports)} 条")
            
            # 3. 限制返回数量
            reports = all_reports[:limit]
            
            if reports:
                logger.info(f"✅ 从东方财富获取到 {len(reports)} 条综合数据: {ticker}")
            else:
                logger.info(f"ℹ️ 东方财富未获取到研报数据: {ticker}")
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ 东方财富API调用失败: {ticker}, 错误: {str(e)}")
            return []
    
    def _format_ticker(self, ticker: str) -> Optional[str]:
        """格式化股票代码为东方财富API格式"""
        try:
            # 清理股票代码
            clean_ticker = ticker.upper().replace('.SZ', '').replace('.SH', '').replace('.BJ', '').strip()
            
            if not clean_ticker.isdigit():
                return None
            
            # 根据股票代码前缀判断交易所
            if clean_ticker.startswith(('000', '002', '003', '300', '301')):
                return f"{clean_ticker}.SZ"  # 深交所
            elif clean_ticker.startswith(('600', '601', '603', '605', '688', '689')):
                return f"{clean_ticker}.SH"  # 上交所
            elif len(clean_ticker) == 8:  # 北交所
                return f"{clean_ticker}.BJ"
            else:
                return f"{clean_ticker}.SH"  # 默认上交所
                
        except Exception as e:
            logger.debug(f"股票代码格式化异常: {ticker}, {e}")
            return None
    
    def _build_api_params(self, ticker: str, limit: int) -> Dict[str, str]:
        """构建API请求参数 - 使用正确的研报API"""
        import time
        import random
        
        # 提取纯数字股票代码
        stock_code = ticker.split('.')[0]
        
        return {
            'sortColumns': 'NOTICE_DATE',  # 按公告日期排序
            'sortTypes': '-1',  # 降序
            'pageSize': str(min(limit, 20)),  # 限制页面大小
            'pageNumber': '1',
            'reportName': 'RPT_ORG_SURVEY',  # 机构调研数据 - 包含研报信息
            'columns': 'ALL',  # 返回所有字段
            'filter': f'(SECURITY_CODE="{stock_code}")',  # 过滤条件
            'client': 'WEB'
        }
    
    def _make_api_request(self, params: Dict[str, str]) -> Optional[Dict]:
        """发送API请求 - 直接使用JSON响应"""
        try:
            import requests
            import json
            
            response = requests.get(
                self.api_base_url,
                params=params,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ 东方财富API请求失败: HTTP {response.status_code}")
                return None
            
            # 直接解析JSON响应
            try:
                data = response.json()
            except json.JSONDecodeError:
                logger.warning(f"⚠️ 东方财富API响应格式异常，尝试JSONP解析...")
                # 尝试JSONP格式
                import re
                text = response.text.strip()
                match = re.search(r'\((.*)\);?$', text)
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                else:
                    logger.warning(f"⚠️ 无法解析东方财富API响应")
                    return None
            
            if not data.get('success', False):
                logger.warning(f"⚠️ 东方财富API返回失败: {data.get('message', '未知错误')}")
                return None
            
            return data
            
        except Exception as e:
            logger.error(f"❌ 东方财富API请求异常: {str(e)}")
            return None
    
    def _parse_api_response(self, response_data: Dict, ticker: str, limit: int) -> List[ResearchReport]:
        """解析API响应数据"""
        try:
            reports = []
            
            result = response_data.get('result', {})
            if not result:
                return reports
            
            data_list = result.get('data', [])
            if not data_list:
                return reports
            
            for item in data_list[:limit]:
                try:
                    # 解析研报数据
                    report = self._parse_single_report(item, ticker)
                    if report:
                        reports.append(report)
                except Exception as e:
                    logger.debug(f"解析单条研报数据失败: {e}")
                    continue
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ 解析东方财富API响应失败: {str(e)}")
            return []
    
    def _parse_single_report(self, item: Dict, ticker: str) -> Optional[ResearchReport]:
        """解析单条研报数据 - 适配RPT_ORG_SURVEY格式"""
        try:
            # 提取基础字段
            stock_name = item.get('SECURITY_NAME_ABBR', ticker)
            stock_code = item.get('SECURITY_CODE', ticker)
            institution = item.get('ORG_NAME', '未知机构')
            
            # 构建标题
            notice_date = item.get('NOTICE_DATE', '')
            receive_time = item.get('RECEIVE_TIME_EXPLAIN', '')
            receive_object = item.get('RECEIVE_OBJECT', '')
            
            title = f"{stock_name}({stock_code}) 机构调研报告"
            if receive_time:
                title += f" - {receive_time}"
            
            # 分析师信息
            analyst = "机构分析师"  # 调研报告通常不指定具体分析师
            publish_date = self._format_date(notice_date)
            
            # 评级相关 - 调研报告通常不包含评级
            rating = "未知"
            target_price = None
            
            # 构建摘要
            summary = self._build_summary_from_survey(item)
            
            # 提取关键观点
            key_points = self._extract_key_points_from_survey(item)
            
            # 计算可信度
            confidence_level = self._calculate_confidence_for_survey(item, institution)
            
            # 数据质量验证
            if not self._validate_report_data(title, institution, publish_date):
                return None
            
            return ResearchReport(
                title=title,
                analyst=analyst,
                institution=institution,
                publish_date=publish_date,
                rating=rating,
                target_price=target_price,
                current_price=None,
                summary=summary,
                key_points=key_points,
                pe_forecast=None,
                revenue_growth=None,
                profit_growth=None,
                source=self.name,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.debug(f"解析单条调研报告失败: {e}")
            return None
    
    def _format_date(self, date_str: str) -> str:
        """格式化日期"""
        try:
            if not date_str:
                return datetime.now().strftime('%Y-%m-%d')
            
            # 处理不同的日期格式
            if 'T' in str(date_str):
                # ISO格式: 2024-01-01T00:00:00
                return str(date_str).split('T')[0]
            elif len(str(date_str)) >= 10:
                # 已经是 YYYY-MM-DD 格式
                return str(date_str)[:10]
            else:
                return datetime.now().strftime('%Y-%m-%d')
                
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _parse_target_price(self, price_data) -> Optional[float]:
        """解析目标价"""
        try:
            if price_data is None:
                return None
            
            if isinstance(price_data, (int, float)):
                return float(price_data) if price_data > 0 else None
            
            if isinstance(price_data, str):
                return self._extract_price(price_data)
            
            return None
        except:
            return None
    
    def _safe_float(self, value) -> Optional[float]:
        """安全转换为浮点数"""
        try:
            if value is None or value == '':
                return None
            return float(value)
        except:
            return None
    
    def _build_summary_from_rating(self, item: Dict) -> str:
        """从评级数据构建研报摘要"""
        summary_parts = []
        
        # 评级变化信息
        rating_change = item.get('RATING_CHANGE_TYPE', '')
        new_rating = item.get('NEW_RATING', '')
        old_rating = item.get('OLD_RATING', '')
        
        if rating_change and old_rating and new_rating:
            summary_parts.append(f"评级{rating_change}: {old_rating} -> {new_rating}")
        elif new_rating:
            summary_parts.append(f"评级: {new_rating}")
        
        # 目标价信息
        target_new = item.get('TARGET_PRICE_NEW')
        target_old = item.get('TARGET_PRICE_OLD')
        if target_new and target_old:
            summary_parts.append(f"目标价调整: {target_old}元 -> {target_new}元")
        elif target_new:
            summary_parts.append(f"目标价: {target_new}元")
        
        # 评级原因
        reason = item.get('RATING_CHANGE_REASON', '')
        if reason:
            summary_parts.append(f"调整原因: {reason}")
        
        # 机构观点
        if item.get('ORG_NAME'):
            summary_parts.append(f"机构: {item['ORG_NAME']}")
        
        return "; ".join(summary_parts) if summary_parts else "暂无摘要"
    
    def _extract_key_points_from_rating(self, item: Dict) -> List[str]:
        """从评级数据提取关键观点"""
        key_points = []
        
        # 评级变化
        rating_change = item.get('RATING_CHANGE_TYPE', '')
        new_rating = item.get('NEW_RATING', '')
        if rating_change and new_rating:
            key_points.append(f"评级{rating_change}: {new_rating}")
        elif new_rating:
            key_points.append(f"投资评级: {new_rating}")
        
        # 目标价
        target_price = item.get('TARGET_PRICE_NEW') or item.get('TARGET_PRICE_OLD')
        if target_price:
            key_points.append(f"目标价位: {target_price}元")
        
        # 调整原因
        reason = item.get('RATING_CHANGE_REASON', '')
        if reason and len(reason) < 50:  # 只取较短的原因作为关键点
            key_points.append(f"原因: {reason}")
        
        return key_points[:3]  # 最多3个关键观点
    
    def _calculate_confidence_for_rating(self, item: Dict, institution: str) -> float:
        """计算评级数据的可信度评分"""
        base_score = 0.75  # 东方财富基础可信度
        
        # 知名机构加分
        prestigious_orgs = ['中信证券', '华泰证券', '国泰君安', '海通证券', '广发证券', '招商证券', '中金公司', 
                           '申万宏源', '兴业证券', '东方证券', '方正证券', '国信证券', '光大证券']
        if any(org in institution for org in prestigious_orgs):
            base_score += 0.1
        
        # 有目标价加分
        if item.get('TARGET_PRICE_NEW') or item.get('TARGET_PRICE_OLD'):
            base_score += 0.05
        
        # 有分析师信息加分
        if item.get('RESEARCHER_NAME') and item['RESEARCHER_NAME'] != '未知分析师':
            base_score += 0.05
        
        # 有评级变化原因加分
        if item.get('RATING_CHANGE_REASON'):
            base_score += 0.05
        
        return min(base_score, 1.0)

    def _build_summary_from_survey(self, item: Dict) -> str:
        """从调研数据构建摘要"""
        summary_parts = []
        
        # 调研基本信息
        notice_date = item.get('NOTICE_DATE', '')
        receive_time = item.get('RECEIVE_TIME_EXPLAIN', '')
        receive_object = item.get('RECEIVE_OBJECT', '')
        org_name = item.get('ORG_NAME', '')
        
        if org_name:
            summary_parts.append(f"机构: {org_name}")
        if notice_date:
            summary_parts.append(f"调研日期: {notice_date}")
        if receive_time:
            summary_parts.append(f"调研时间: {receive_time}")
        if receive_object:
            summary_parts.append(f"调研对象: {receive_object}")
        
        # 调研内容
        content = item.get('CONTENT', '')
        if content:
            summary_parts.append(f"调研内容: {content[:200]}...")
        
        # 调研地点和方式
        receive_place = item.get('RECEIVE_PLACE', '')
        receive_way = item.get('RECEIVE_WAY_EXPLAIN', '')
        if receive_place:
            summary_parts.append(f"调研地点: {receive_place}")
        if receive_way:
            summary_parts.append(f"调研方式: {receive_way}")
        
        return "; ".join(summary_parts) if summary_parts else "机构调研报告"

    def _extract_key_points_from_survey(self, item: Dict) -> List[str]:
        """从调研数据提取关键观点"""
        key_points = []
        
        # 调研对象
        receive_object = item.get('RECEIVE_OBJECT', '')
        if receive_object:
            key_points.append(f"调研对象: {receive_object}")
        
        # 调研时间
        receive_time = item.get('RECEIVE_TIME_EXPLAIN', '')
        if receive_time:
            key_points.append(f"调研时间: {receive_time}")
        
        # 调研内容要点
        content = item.get('CONTENT', '')
        if content:
            # 提取内容中的关键信息
            sentences = content.replace('。', '\n').replace('；', '\n').split('\n')
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10 and len(sentence) < 100:
                    key_points.append(sentence)
        
        # 机构信息
        org_name = item.get('ORG_NAME', '')
        if org_name:
            key_points.append(f"调研机构: {org_name}")
        
        return key_points[:3]  # 最多3个关键观点

    def _get_survey_reports(self, ticker: str, limit: int) -> List[ResearchReport]:
        """获取机构调研报告"""
        try:
            params = {
                'reportName': 'RPT_ORG_SURVEY',
                'columns': 'ALL',
                'filter': f'(SECURITY_CODE="{ticker.split(".")[0]}")',
                'pageNumber': 1,
                'pageSize': str(limit),
                'sortTypes': -1,
                'sortColumns': 'NOTICE_DATE',
                'client': 'WEB',
            }
            
            response = self._make_api_request(params)
            if not response:
                return []
            
            return self._parse_survey_response(response, ticker, limit)
            
        except Exception as e:
            logger.warning(f"⚠️ 获取机构调研数据失败: {e}")
            return []
    
    def _get_value_analysis_reports(self, ticker: str, limit: int) -> List[ResearchReport]:
        """获取价值分析数据作为补充"""
        try:
            params = {
                'reportName': 'RPT_VALUEANALYSIS_DET',
                'columns': 'ALL',
                'filter': f'(SECURITY_CODE="{ticker.split(".")[0]}")',
                'pageNumber': 1,
                'pageSize': str(limit),
                'sortTypes': -1,
                'sortColumns': 'TRADE_DATE',
                'client': 'WEB',
            }
            
            response = self._make_api_request(params)
            if not response:
                return []
            
            return self._parse_value_response(response, ticker, limit)
            
        except Exception as e:
            logger.warning(f"⚠️ 获取价值分析数据失败: {e}")
            return []
    
    def _parse_survey_response(self, response_data: Dict, ticker: str, limit: int) -> List[ResearchReport]:
        """解析机构调研响应数据"""
        try:
            reports = []
            
            result = response_data.get('result', {})
            if not result:
                return reports
            
            data_list = result.get('data', [])
            if not data_list:
                return reports
            
            for item in data_list[:limit]:
                try:
                    report = self._parse_survey_report(item, ticker)
                    if report:
                        reports.append(report)
                except Exception as e:
                    logger.debug(f"解析单条调研报告失败: {e}")
                    continue
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ 解析机构调研响应失败: {str(e)}")
            return []
    
    def _parse_value_response(self, response_data: Dict, ticker: str, limit: int) -> List[ResearchReport]:
        """解析价值分析响应数据"""
        try:
            reports = []
            
            result = response_data.get('result', {})
            if not result:
                return reports
            
            data_list = result.get('data', [])
            if not data_list:
                return reports
            
            for item in data_list[:limit]:
                try:
                    report = self._parse_value_report(item, ticker)
                    if report:
                        reports.append(report)
                except Exception as e:
                    logger.debug(f"解析单条价值分析报告失败: {e}")
                    continue
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ 解析价值分析响应失败: {str(e)}")
            return []
    
    def _parse_survey_report(self, item: Dict, ticker: str) -> Optional[ResearchReport]:
        """解析单条机构调研报告"""
        try:
            stock_name = item.get('SECURITY_NAME_ABBR', ticker)
            stock_code = item.get('SECURITY_CODE', ticker)
            institution = item.get('ORG_NAME', '未知机构')
            
            # 构建标题
            notice_date = item.get('NOTICE_DATE', '')
            receive_time = item.get('RECEIVE_TIME_EXPLAIN', '')
            
            title = f"{stock_name}({stock_code}) 机构调研报告"
            if receive_time:
                title += f" - {receive_time}"
            
            publish_date = self._format_date(notice_date)
            
            # 构建摘要
            summary = self._build_summary_from_survey(item)
            key_points = self._extract_key_points_from_survey(item)
            
            confidence_level = self._calculate_confidence_for_survey(item, institution)
            
            if not self._validate_report_data(title, institution, publish_date):
                return None
            
            return ResearchReport(
                title=title,
                analyst="机构分析师",
                institution=institution,
                publish_date=publish_date,
                rating="机构调研",
                target_price=None,
                current_price=item.get('CLOSE_PRICE'),
                summary=summary,
                key_points=key_points,
                pe_forecast=item.get('PE_TTM'),
                revenue_growth=None,
                profit_growth=None,
                source=self.name,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.debug(f"解析单条调研报告失败: {e}")
            return None
    
    def _parse_value_report(self, item: Dict, ticker: str) -> Optional[ResearchReport]:
        """解析单条价值分析报告"""
        try:
            stock_name = item.get('SECURITY_NAME_ABBR', ticker)
            stock_code = item.get('SECURITY_CODE', ticker)
            
            trade_date = item.get('TRADE_DATE', '')
            close_price = item.get('CLOSE_PRICE')
            pe_ttm = item.get('PE_TTM')
            pb_mrq = item.get('PB_MRQ')
            market_cap = item.get('TOTAL_MARKET_CAP')
            
            title = f"{stock_name}({stock_code}) 价值分析报告 - {trade_date}"
            
            # 构建摘要
            summary_parts = []
            if close_price:
                summary_parts.append(f"收盘价: {close_price}元")
            if pe_ttm:
                summary_parts.append(f"市盈率(TTM): {pe_ttm}")
            if pb_mrq:
                summary_parts.append(f"市净率: {pb_mrq}")
            if market_cap:
                summary_parts.append(f"总市值: {market_cap:,.0f}元")
            
            summary = "; ".join(summary_parts)
            
            key_points = []
            if pe_ttm:
                key_points.append(f"当前PE: {pe_ttm}")
            if pb_mrq:
                key_points.append(f"当前PB: {pb_mrq}")
            
            confidence_level = 0.7  # 价值分析数据可信度
            
            publish_date = self._format_date(trade_date)
            
            if not self._validate_report_data(title, "东方财富数据中心", publish_date):
                return None
            
            return ResearchReport(
                title=title,
                analyst="东方财富",
                institution="东方财富数据中心",
                publish_date=publish_date,
                rating="价值分析",
                target_price=None,
                current_price=close_price,
                summary=summary,
                key_points=key_points,
                pe_forecast=pe_ttm,
                revenue_growth=None,
                profit_growth=None,
                source=self.name,
                confidence_level=confidence_level
            )
            
        except Exception as e:
            logger.debug(f"解析单条价值分析报告失败: {e}")
            return None

    def _calculate_confidence_for_survey(self, item: Dict, institution: str) -> float:
        """计算调研数据的可信度评分"""
        base_score = 0.8  # 机构调研基础可信度较高
        
        # 知名机构加分
        prestigious_orgs = ['中信证券', '华泰证券', '国泰君安', '海通证券', '广发证券', '招商证券', '中金公司', 
                           '申万宏源', '兴业证券', '东方证券', '方正证券', '国信证券', '光大证券']
        if any(org in institution for org in prestigious_orgs):
            base_score += 0.1
        
        # 有调研内容加分
        content = item.get('CONTENT', '')
        if content and len(content) > 50:
            base_score += 0.05
        
        # 有调研对象加分
        receive_object = item.get('RECEIVE_OBJECT', '')
        if receive_object:
            base_score += 0.05
        
        return min(base_score, 1.0)
    
    def _validate_report_data(self, title: str, institution: str, publish_date: str) -> bool:
        """验证研报数据质量"""
        # 标题长度检查
        if not title or len(title) < 3:
            return False
        
        # 机构名称检查
        if not institution or institution == '未知机构':
            return False
        
        # 日期检查
        if not publish_date:
            return False
        
        return True


class TongHuaShunResearchProvider(ResearchReportProvider):
    """同花顺iFinD研报数据提供器"""
    
    def __init__(self):
        super().__init__()
        self.name = "同花顺"
        self.base_url = "http://data.10jqka.com.cn"
        
        # 导入配置和配额管理器
        from tradingagents.config.tonghuashun_config import tonghuashun_config
        from tradingagents.utils.quota_manager import QuotaManager
        
        self.config = tonghuashun_config
        self.quota_manager = QuotaManager('tonghuashun', self.config.get_quota_config())
        self.is_logged_in = False
        self.ifind_available = False
        
        # 尝试初始化iFinD连接
        self._initialize_ifind()
    
    def _initialize_ifind(self):
        """初始化iFinD连接"""
        try:
            if not self.config.is_enabled():
                logger.info(f"🔧 同花顺iFinD未配置或未启用，使用备用模式")
                return False
            
            # 尝试导入iFinD Python库
            try:
                global THS_iFinDLogin, THS_BasicData, THS_Trans2DataFrame
                from iFinDPy import THS_iFinDLogin, THS_BasicData, THS_Trans2DataFrame
                logger.info(f"✅ 成功导入iFinD Python库")
                self.ifind_available = True
            except ImportError as e:
                logger.warning(f"⚠️ iFinD Python库未安装: {e}")
                logger.info(f"💡 请下载并安装同花顺iFinD Python SDK: http://quantapi.10jqka.com.cn/")
                return False
            
            # 尝试登录
            api_config = self.config.get_api_config()
            login_result = THS_iFinDLogin(api_config['username'], api_config['password'])
            
            if login_result.errorcode == 0:
                logger.info(f"✅ 同花顺iFinD登录成功")
                self.is_logged_in = True
                return True
            else:
                logger.warning(f"⚠️ 同花顺iFinD登录失败: {login_result.errmsg}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 初始化同花顺iFinD失败: {e}")
            return False
    
    def get_reports(self, ticker: str, limit: int = 10) -> List[ResearchReport]:
        """获取同花顺研报数据"""
        try:
            logger.info(f"🔍 开始从同花顺获取研报: {ticker}")
            
            # 检查是否可用
            if not self.ifind_available or not self.is_logged_in:
                logger.warning(f"⚠️ 同花顺iFinD不可用，跳过该数据源: {ticker}")
                return []
            
            # 检查配额
            if not self.quota_manager.wait_if_needed():
                logger.warning(f"⚠️ 同花顺配额不足，跳过该数据源: {ticker}")
                return []
            
            # 调用真实API获取研报数据
            reports = self._fetch_research_reports_from_ifind(ticker, limit)
            
            # 记录请求
            self.quota_manager.record_request()
            
            if reports:
                logger.info(f"✅ 从同花顺获取到 {len(reports)} 条研报: {ticker}")
            else:
                logger.info(f"ℹ️ 同花顺未获取到研报数据: {ticker}")
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ 从同花顺获取研报失败: {ticker}, 错误: {str(e)}")
            return []
    
    def _fetch_research_reports_from_ifind(self, ticker: str, limit: int = 10) -> List[ResearchReport]:
        """从iFinD API获取研报数据"""
        try:
            # 格式化股票代码用于iFinD
            formatted_ticker = self._format_ticker_for_ifind(ticker)
            if not formatted_ticker:
                logger.warning(f"⚠️ 股票代码格式化失败: {ticker}")
                return []
            
            # 构建iFinD查询参数
            indicators = ';'.join(self.config.research_report_fields)
            
            # 调用iFinD接口获取研报数据
            result = THS_BasicData(formatted_ticker, indicators, 'unit:1')
            
            if result.errorcode != 0:
                logger.warning(f"⚠️ iFinD API调用失败: {result.errmsg}")
                return []
            
            # 转换为DataFrame
            df = THS_Trans2DataFrame(result)
            
            if df is None or df.empty:
                logger.warning(f"⚠️ iFinD返回空数据: {ticker}")
                return []
            
            # 解析研报数据
            reports = self._parse_ifind_research_data(df, ticker, limit)
            
            return reports
            
        except Exception as e:
            logger.error(f"❌ iFinD API调用异常: {ticker}, 错误: {str(e)}")
            return []
    
    def _format_ticker_for_ifind(self, ticker: str) -> Optional[str]:
        """为iFinD格式化股票代码"""
        try:
            # 清理股票代码
            clean_ticker = ticker.upper().replace('.SZ', '').replace('.SH', '').replace('.BJ', '').strip()
            
            if not clean_ticker.isdigit():
                return None
            
            # iFinD格式：股票代码 + 交易所后缀
            if clean_ticker.startswith(('000', '002', '003', '300', '301')):
                return f"{clean_ticker}.SZ"  # 深交所
            elif clean_ticker.startswith(('600', '601', '603', '605', '688', '689')):
                return f"{clean_ticker}.SH"  # 上交所
            elif len(clean_ticker) == 8:  # 北交所
                return f"{clean_ticker}.BJ"
            else:
                return f"{clean_ticker}.SH"  # 默认上交所
                
        except Exception as e:
            logger.warning(f"⚠️ 股票代码格式化异常: {ticker}, {e}")
            return None
    
    def _parse_ifind_research_data(self, df, ticker: str, limit: int) -> List[ResearchReport]:
        """解析iFinD研报数据"""
        try:
            reports = []
            
            # 获取字段映射
            field_mapping = {
                'ths_report_title_research': 'title',
                'ths_report_institution_research': 'institution', 
                'ths_report_analyst_research': 'analyst',
                'ths_report_publish_date_research': 'publish_date',
                'ths_rating_latest_research': 'rating',
                'ths_target_price_research': 'target_price',
                'ths_report_abstract_research': 'summary'
            }
            
            # 处理数据行
            for idx, row in df.head(limit).iterrows():
                try:
                    # 提取基础字段
                    report_data = {}
                    for ifind_field, standard_field in field_mapping.items():
                        if ifind_field in df.columns:
                            report_data[standard_field] = self._safe_get_ifind_value(row[ifind_field])
                    
                    # 数据质量检查
                    if not self._validate_report_data(report_data):
                        continue
                    
                    # 创建研报对象
                    report = ResearchReport(
                        title=report_data.get('title', f'{ticker}研报'),
                        analyst=report_data.get('analyst', '未知分析师'),
                        institution=report_data.get('institution', '未知机构'),
                        publish_date=self._standardize_date(report_data.get('publish_date', '')),
                        rating=self._parse_rating(report_data.get('rating', '')),
                        target_price=self._extract_price(report_data.get('target_price', '')),
                        current_price=None,
                        summary=self._clean_summary(report_data.get('summary', '')),
                        key_points=self._extract_key_points_from_summary(report_data.get('summary', '')),
                        pe_forecast=None,
                        revenue_growth=None,
                        profit_growth=None,
                        source=self.name,
                        confidence_level=self.config.confidence_base_score
                    )
                    
                    reports.append(report)
                    
                except Exception as row_error:
                    logger.warning(f"⚠️ 解析iFinD研报行数据失败: {row_error}")
                    continue
            
            logger.debug(f"📊 iFinD研报数据解析完成: {ticker}, 有效数据 {len(reports)} 条")
            return reports
            
        except Exception as e:
            logger.error(f"❌ 解析iFinD研报数据失败: {ticker}, 错误: {str(e)}")
            return []
    
    def _safe_get_ifind_value(self, value) -> str:
        """安全获取iFinD字段值"""
        if value is None or str(value).lower() in ['nan', 'none', 'null', '']:
            return ''
        return str(value).strip()
    
    def _validate_report_data(self, report_data: Dict[str, str]) -> bool:
        """验证研报数据质量"""
        # 检查标题长度
        title = report_data.get('title', '')
        if len(title) < self.config.min_report_title_length:
            return False
        
        # 检查机构信息
        institution = report_data.get('institution', '')
        if not institution or institution == '未知机构':
            return False
        
        return True
    
    def _standardize_date(self, date_str: str) -> str:
        """标准化日期格式"""
        try:
            if not date_str:
                return '2024-08-04'
            
            from datetime import datetime
            # 尝试多种日期格式
            date_formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']
            
            for fmt in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue
            
            return date_str if len(date_str) >= 8 else '2024-08-04'
            
        except Exception:
            return '2024-08-04'
    
    def _clean_summary(self, summary: str) -> str:
        """清理研报摘要"""
        if not summary:
            return '暂无摘要'
        
        # 限制长度
        if len(summary) > self.config.max_report_summary_length:
            summary = summary[:self.config.max_report_summary_length] + "..."
        
        return summary.strip()
    
    def _extract_key_points_from_summary(self, summary: str) -> List[str]:
        """从摘要提取关键观点"""
        if not summary or summary == '暂无摘要':
            return []
        
        # 简单的关键词提取
        key_phrases = []
        keywords = ['推荐', '买入', '增持', '减持', '卖出', '维持', '上调', '下调', '目标价']
        
        sentences = summary.replace('。', '\n').replace('；', '\n').split('\n')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10 and any(keyword in sentence for keyword in keywords):
                key_phrases.append(sentence)
        
        return key_phrases[:3]  # 最多3个关键观点
    
    def _get_sample_tonghuashun_reports(self, ticker: str) -> List[Dict]:
        """获取示例数据"""
        return [
            {
                'title': f'{ticker} 投资策略报告',
                'analyst': '王五',
                'institution': '国泰君安',
                'publish_date': '2024-07-28',
                'rating': '强推',
                'target_price_text': '48元',
                'current_price': 38.5,
                'summary': '公司业务模式优秀，强烈推荐',
                'key_points': ['业务模式创新', '市场份额扩大', '盈利能力强'],
                'pe_forecast': 14.8,
                'revenue_growth': 0.18,
                'profit_growth': 0.25
            }
        ]


class AKShareResearchProvider(ResearchReportProvider):
    """AKShare研报数据提供器"""
    
    def __init__(self):
        super().__init__()
        self.name = "AKShare"
    
    def get_reports(self, ticker: str, limit: int = 10) -> List[ResearchReport]:
        """使用AKShare获取研报数据"""
        try:
            logger.info(f"🔍 开始从AKShare获取研报: {ticker}")
            
            # 尝试导入AKShare
            try:
                import akshare as ak
                
                # 股票代码格式检查和转换
                formatted_ticker = self._format_ticker_for_akshare(ticker)
                if not formatted_ticker:
                    logger.warning(f"⚠️ 股票代码格式验证失败: {ticker}")
                    return []
                logger.debug(f"🔧 AKShare格式转换: {ticker} -> {formatted_ticker}")
                
                # 获取个股研报数据，使用智能重试机制
                try:
                    research_df = self._call_akshare_with_retry(formatted_ticker)
                    
                    # 检查返回数据是否有效
                    if research_df is None or research_df.empty:
                        logger.warning(f"⚠️ AKShare返回空数据: {ticker}")
                        return []
                    
                    # 数据质量验证
                    validation_result = self._validate_research_data(research_df, ticker)
                    if not validation_result['is_valid']:
                        logger.warning(f"⚠️ AKShare数据验证失败: {ticker}, 原因: {validation_result['reason']}")
                        return []
                    
                    logger.info(f"✅ AKShare数据验证通过: {ticker}, 行数: {len(research_df)}, 列数: {len(research_df.columns)}")
                    
                    # 数据清洗
                    research_df = self._clean_research_data(research_df)
                    logger.debug(f"📋 AKShare数据清洗完成: {ticker}, 最终行数: {len(research_df)}")
                    
                    reports = []
                    
                    # 安全地遍历数据，增强字段提取
                    for idx, row in research_df.head(limit).iterrows():
                        try:
                            # 基础字段提取
                            title = self._safe_get_value(row, ['标题', 'title', '研报标题', '报告标题'], f'{ticker}研报')
                            analyst = self._safe_get_value(row, ['分析师', 'analyst', '研究员'], '未知分析师')
                            institution = self._safe_get_value(row, ['机构', 'institution', '券商', '研究机构'], '未知机构')
                            publish_date = self._safe_get_value(row, ['发布日期', 'date', '日期', '发布时间'], '2024-08-04')
                            rating_text = self._safe_get_value(row, ['评级', 'rating', '投资评级', '研报评级'], '未知')
                            target_price_text = self._safe_get_value(row, ['目标价', 'target_price', '目标价格'], '')
                            summary = self._safe_get_value(row, ['摘要', 'summary', '内容', '研报摘要', '核心观点'], '暂无摘要')
                            
                            # 增强字段提取
                            report_type = self._safe_get_value(row, ['报告类型', 'report_type', '研报类型'], '深度研究')
                            page_count = self._safe_get_value(row, ['页数', 'pages', '报告页数'], '')
                            report_url = self._safe_get_value(row, ['链接', 'url', 'link', 'pdfUrl'], '')
                            
                            # 财务预测字段提取
                            pe_ratio = self._extract_number(self._safe_get_value(row, ['PE', 'pe', '市盈率'], ''))
                            pb_ratio = self._extract_number(self._safe_get_value(row, ['PB', 'pb', '市净率'], ''))
                            revenue_forecast = self._extract_number(self._safe_get_value(row, ['营收预测', 'revenue_forecast'], ''))
                            profit_forecast = self._extract_number(self._safe_get_value(row, ['利润预测', 'profit_forecast'], ''))
                            
                            # 关键观点提取
                            key_points = self._extract_key_points(summary, title)
                            
                            # 摘要优化处理
                            if len(summary) > 300:
                                summary = summary[:300] + "..."
                            
                            report = ResearchReport(
                                title=title,  
                                analyst=analyst,
                                institution=institution,
                                publish_date=publish_date,
                                rating=self._parse_rating(rating_text),
                                target_price=self._extract_price(target_price_text),
                                current_price=None,
                                summary=summary,
                                key_points=key_points,
                                pe_forecast=pe_ratio,
                                revenue_growth=revenue_forecast,
                                profit_growth=profit_forecast,
                                source=self.name,
                                confidence_level=self._calculate_confidence_level(institution, analyst, publish_date)
                            )
                            reports.append(report)
                            
                        except Exception as row_error:
                            logger.warning(f"⚠️ 处理单行数据失败: {row_error}, 跳过该行")
                            continue
                    
                    if reports:
                        logger.info(f"✅ 从AKShare获取到 {len(reports)} 条研报: {ticker}")
                        return reports
                    else:
                        logger.warning(f"⚠️ AKShare数据处理后为空: {ticker}")
                        return []
                
                except Exception as api_error:
                    # AKShare API调用失败的详细错误处理
                    error_msg = str(api_error)
                    if 'infoCode' in error_msg:
                        logger.warning(f"⚠️ AKShare API返回错误代码: {ticker}, 尝试替代方案")
                    elif 'timeout' in error_msg.lower():
                        logger.warning(f"⚠️ AKShare API超时: {ticker}, 尝试替代方案")
                    elif 'connection' in error_msg.lower():
                        logger.warning(f"⚠️ AKShare网络连接失败: {ticker}, 尝试替代方案")
                    else:
                        logger.warning(f"⚠️ AKShare API调用失败: {ticker}, 错误: {error_msg}, 尝试替代方案")
                    
                    # 对于研报数据，不使用替代方案，直接返回空列表
                    # 这确保了数据的真实性和准确性
                    logger.warning(f"⚠️ AKShare研报API失败，不使用替代数据: {ticker}")
                    return []
                
            except ImportError:
                logger.warning("⚠️ AKShare未安装，跳过AKShare数据源")
                return []
                
        except Exception as e:
            logger.error(f"❌ 从AKShare获取研报失败: {ticker}, 错误: {str(e)}")
            # 出错时返回空列表，不使用示例数据
            return []
    
    def _format_ticker_for_akshare(self, ticker: str) -> Optional[str]:
        """为AKShare格式化和验证股票代码，支持所有中国股票市场"""
        if not ticker:
            return None
            
        # 清理股票代码，支持更多后缀格式
        clean_ticker = ticker.upper().replace('.SZ', '').replace('.SH', '').replace('.BJ', '').replace('.sz', '').replace('.sh', '').replace('.bj', '').strip()
        
        # 确保是纯数字
        if not clean_ticker.isdigit():
            logger.warning(f"⚠️ 股票代码包含非数字字符: {ticker}")
            return None
        
        # 长度检查和标准化 - 支持6位A股和8位北交所
        if len(clean_ticker) > 8:
            logger.warning(f"⚠️ 股票代码长度超过8位: {ticker}")
            return None
        elif len(clean_ticker) == 6:
            # 标准6位A股代码
            pass
        elif len(clean_ticker) == 8:
            # 8位北交所代码
            pass
        elif len(clean_ticker) < 6:
            # 补齐到6位
            clean_ticker = clean_ticker.zfill(6)
        else:
            logger.warning(f"⚠️ 不支持的股票代码长度: {ticker} (长度: {len(clean_ticker)})")
            return None
        
        # 市场分类验证
        board_info = self._classify_stock_board(clean_ticker)
        if not board_info['is_valid']:
            logger.warning(f"⚠️ 无法识别的股票代码格式: {ticker} -> {clean_ticker}")
            return None
        
        logger.info(f"✅ 股票代码格式化成功: {ticker} -> {clean_ticker} ({board_info['board_name']})")
        return clean_ticker
    
    def _classify_stock_board(self, ticker: str) -> Dict[str, Any]:
        """综合分类识别中国股票市场板块，支持所有交易所"""
        ticker_len = len(ticker)
        
        # 处理6位标准A股代码
        if ticker_len == 6:
            first_char = ticker[0]
            first_three = ticker[:3]
            
            # 上海交易所
            if first_char == '6':
                if first_three in ['600', '601', '603', '605']:
                    return {
                        'is_valid': True, 
                        'board_name': '上海主板', 
                        'exchange': 'SH',
                        'board_code': 'SH_MAIN',
                        'special_handling': False
                    }
                elif first_three == '688':
                    return {
                        'is_valid': True, 
                        'board_name': '科创板', 
                        'exchange': 'SH',
                        'board_code': 'SH_STAR',
                        'special_handling': True,  # 科创板需要特殊处理
                        'notes': '科创板股票，注册制，风险较高'
                    }
                elif first_three in ['689']:
                    return {
                        'is_valid': True, 
                        'board_name': '科创板', 
                        'exchange': 'SH',
                        'board_code': 'SH_STAR',
                        'special_handling': True,
                        'notes': '科创板预留号段'
                    }
                else:
                    return {
                        'is_valid': True, 
                        'board_name': '上海其他', 
                        'exchange': 'SH',
                        'board_code': 'SH_OTHER',
                        'special_handling': False
                    }
            
            # 深圳交易所  
            elif first_char == '0':
                if first_three in ['000', '001']:
                    return {
                        'is_valid': True, 
                        'board_name': '深圳主板', 
                        'exchange': 'SZ',
                        'board_code': 'SZ_MAIN',
                        'special_handling': False
                    }
                elif first_three in ['002', '003']:
                    return {
                        'is_valid': True, 
                        'board_name': '中小板', 
                        'exchange': 'SZ',
                        'board_code': 'SZ_SME',
                        'special_handling': False,
                        'notes': '中小板已并入主板'
                    }
                else:
                    return {
                        'is_valid': True, 
                        'board_name': '深圳其他', 
                        'exchange': 'SZ',
                        'board_code': 'SZ_OTHER',
                        'special_handling': False
                    }
            
            # 创业板
            elif first_char == '3':
                if first_three == '300':
                    return {
                        'is_valid': True, 
                        'board_name': '创业板', 
                        'exchange': 'SZ',
                        'board_code': 'SZ_GEM',
                        'special_handling': True,  # 创业板需要特殊权限
                        'notes': '创业板，需要投资者适当性管理'
                    }
                elif first_three == '301':
                    return {
                        'is_valid': True, 
                        'board_name': '创业板', 
                        'exchange': 'SZ',
                        'board_code': 'SZ_GEM',
                        'special_handling': True,
                        'notes': '创业板注册制新股'
                    }
                else:
                    return {
                        'is_valid': True, 
                        'board_name': '深圳其他', 
                        'exchange': 'SZ',
                        'board_code': 'SZ_OTHER',
                        'special_handling': False
                    }
            
            # 北京交易所相关（部分6位代码）
            elif first_char in ['4', '8', '9']:
                if first_three in ['430', '831', '832', '833', '834', '835', '836', '837', '838', '839']:
                    return {
                        'is_valid': True, 
                        'board_name': '北交所/新三板', 
                        'exchange': 'BJ',
                        'board_code': 'BJ_NEEQ',
                        'special_handling': True,
                        'notes': '北交所或新三板，流动性相对较低'
                    }
                else:
                    return {
                        'is_valid': True, 
                        'board_name': '其他市场', 
                        'exchange': 'OTHER',
                        'board_code': 'OTHER',
                        'special_handling': True
                    }
                    
            # 港股通代码（部分以9开头）
            elif first_char == '9':
                if first_three in ['900', '901', '902']:
                    return {
                        'is_valid': True, 
                        'board_name': 'B股', 
                        'exchange': 'SH',
                        'board_code': 'SH_B',
                        'special_handling': True,
                        'notes': 'B股，外币交易'
                    }
                else:
                    return {
                        'is_valid': True, 
                        'board_name': '其他', 
                        'exchange': 'OTHER',
                        'board_code': 'OTHER',
                        'special_handling': True
                    }
            
            else:
                # 其他未识别的6位代码
                return {
                    'is_valid': False, 
                    'board_name': '未知', 
                    'error': f'无法识别的6位股票代码: {ticker}'
                }
        
        # 处理8位北交所代码
        elif ticker_len == 8:
            first_two = ticker[:2]
            
            if first_two in ['43', '83', '87', '88']:
                return {
                    'is_valid': True, 
                    'board_name': '北交所', 
                    'exchange': 'BJ',
                    'board_code': 'BJ_MAIN',
                    'special_handling': True,
                    'notes': '北交所主板，8位代码，注册制'
                }
            else:
                return {
                    'is_valid': True, 
                    'board_name': '北交所其他', 
                    'exchange': 'BJ',
                    'board_code': 'BJ_OTHER',
                    'special_handling': True,
                    'notes': '北交所相关8位代码'
                }
                
        # 处理其他长度代码
        else:
            return {
                'is_valid': False, 
                'board_name': '无效长度', 
                'error': f'不支持的股票代码长度: {ticker_len} 位'
            }
    
    def _call_akshare_with_retry(self, ticker: str, max_retries: int = 3) -> Optional[Any]:
        """带智能重试的AKShare调用，支持特殊板块处理"""
        import time
        import akshare as ak
        
        # 获取股票板块信息用于特殊处理
        board_info = self._classify_stock_board(ticker)
        
        # 针对特殊板块调整重试策略
        if board_info.get('special_handling'):
            max_retries = max_retries + 1  # 特殊板块多重试一次
            logger.info(f"🎯 特殊板块股票，使用增强重试策略: {ticker} ({board_info['board_name']})")
        
        for attempt in range(max_retries):
            try:
                # 递增延时策略，特殊板块使用更长延时
                if attempt > 0:
                    base_delay = 0.5 * (2 ** (attempt - 1))  # 指数退避
                    if board_info.get('special_handling'):
                        delay = base_delay * 1.5  # 特殊板块延时更长
                    else:
                        delay = base_delay
                    
                    logger.debug(f"🔄 重试前等待 {delay:.1f} 秒: {ticker}")
                    time.sleep(delay)
                
                logger.debug(f"🔍 尝试调用AKShare (第{attempt + 1}次): {ticker}")
                
                # 针对特殊板块的API调用适配
                if board_info.get('board_code') == 'SH_STAR':
                    # 科创板特殊处理
                    logger.debug(f"🚀 科创板股票特殊处理: {ticker}")
                elif board_info.get('board_code') in ['BJ_MAIN', 'BJ_NEEQ', 'BJ_OTHER']:
                    # 北交所特殊处理
                    logger.debug(f"🏢 北交所股票特殊处理: {ticker}")
                elif board_info.get('board_code') == 'SZ_GEM':
                    # 创业板特殊处理
                    logger.debug(f"💎 创业板股票特殊处理: {ticker}")
                
                # 统一API调用
                result = ak.stock_research_report_em(symbol=ticker)
                
                # 成功获取数据
                if result is not None:
                    logger.debug(f"✅ AKShare调用成功 (第{attempt + 1}次): {ticker}")
                    return result
                else:
                    logger.warning(f"⚠️ AKShare返回None (第{attempt + 1}次): {ticker}")
                    
            except Exception as e:
                error_msg = str(e).lower()
                
                # 分析错误类型，考虑特殊板块
                error_type = self._classify_akshare_error_enhanced(error_msg, board_info)
                
                if error_type == 'permanent':
                    # 永久性错误，不重试
                    logger.warning(f"⚠️ 永久性错误，停止重试: {ticker}, 错误: {e}")
                    return None
                elif error_type == 'board_specific':
                    # 板块特定错误，给出具体建议
                    logger.warning(f"⚠️ {board_info['board_name']}特定错误: {ticker}, {e}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        return None
                elif error_type == 'temporary' and attempt < max_retries - 1:
                    # 临时性错误，继续重试
                    logger.warning(f"⚠️ 临时性错误，准备重试 (第{attempt + 1}次): {ticker}, 错误: {e}")
                    continue
                else:
                    # 达到最大重试次数或其他错误
                    logger.error(f"❌ AKShare调用失败，已达最大重试次数: {ticker}, 错误: {e}")
                    return None
        
        logger.warning(f"⚠️ AKShare重试全部失败: {ticker} ({board_info.get('board_name', '未知板块')})")
        return None
    
    def _classify_akshare_error(self, error_msg: str) -> str:
        """分类AKShare错误类型（基础版本）"""
        # 永久性错误（不需要重试）
        permanent_indicators = [
            'infocode',  # 股票代码不存在或无权限
            'not found', # 数据不存在
            'no data',   # 无数据
            'invalid symbol', # 无效代码
            'invalid parameter' # 无效参数
        ]
        
        # 临时性错误（可以重试）
        temporary_indicators = [
            'timeout',     # 超时
            'connection',  # 连接错误
            'network',     # 网络错误
            'server',      # 服务器错误
            'rate limit',  # 频率限制
            'too many',    # 请求过多
            'busy',        # 服务繁忙
            'temporarily', # 临时错误
            'retry'        # 建议重试
        ]
        
        error_lower = error_msg.lower()
        
        # 检查是否为永久性错误
        if any(indicator in error_lower for indicator in permanent_indicators):
            return 'permanent'
        
        # 检查是否为临时性错误
        if any(indicator in error_lower for indicator in temporary_indicators):
            return 'temporary'
        
        # 默认当作临时性错误，给一次重试机会
        return 'temporary'
    
    def _classify_akshare_error_enhanced(self, error_msg: str, board_info: Dict[str, Any]) -> str:
        """增强版AKShare错误分类，考虑特殊板块特性"""
        error_lower = error_msg.lower()
        board_code = board_info.get('board_code', '')
        board_name = board_info.get('board_name', '未知')
        
        # 科创板特定错误
        if board_code == 'SH_STAR':
            if 'infocode' in error_lower:
                logger.info(f"🚀 科创板股票可能研报覆盖较少，这是正常情况")
                return 'permanent'
            elif any(indicator in error_lower for indicator in ['688', 'kcb', 'star']):
                return 'board_specific'
                
        # 北交所特定错误
        elif board_code in ['BJ_MAIN', 'BJ_NEEQ', 'BJ_OTHER']:
            if 'infocode' in error_lower:
                logger.info(f"🏢 北交所股票研报覆盖有限，这是常见情况")
                return 'permanent'
            elif any(indicator in error_lower for indicator in ['bj', 'neeq', '43', '83']):
                return 'board_specific'
                
        # 创业板特定错误
        elif board_code == 'SZ_GEM':
            if 'infocode' in error_lower:
                logger.info(f"💎 创业板股票，可能需要特殊权限或研报较少")
                return 'permanent'
            elif any(indicator in error_lower for indicator in ['300', '301', 'gem']):
                return 'board_specific'
        
        # 通用错误处理
        # 永久性错误
        permanent_indicators = [
            'infocode',  # 股票代码不存在或无权限
            'not found', # 数据不存在
            'no data',   # 无数据
            'invalid symbol', # 无效代码
            'invalid parameter', # 无效参数
            'access denied', # 访问拒绝
            'unauthorized' # 未授权
        ]
        
        # 临时性错误
        temporary_indicators = [
            'timeout',     # 超时
            'connection',  # 连接错误
            'network',     # 网络错误
            'server',      # 服务器错误
            'rate limit',  # 频率限制
            'too many',    # 请求过多
            'busy',        # 服务繁忙
            'temporarily', # 临时错误
            'retry',       # 建议重试
            'service unavailable', # 服务不可用
            '502', '503', '504'  # HTTP错误码
        ]
        
        # 检查错误类型
        if any(indicator in error_lower for indicator in permanent_indicators):
            return 'permanent'
        elif any(indicator in error_lower for indicator in temporary_indicators):
            return 'temporary'
        else:
            # 对于特殊板块，默认更保守
            if board_info.get('special_handling'):
                return 'board_specific'
            else:
                return 'temporary'
    
    def _log_structured_error(self, ticker: str, error: Exception, context: str, 
                             error_type: str = 'unknown', recoverable: bool = False):
        """结构化错误记录"""
        error_info = {
            'ticker': ticker,
            'context': context,
            'error_type': error_type,
            'error_message': str(error),
            'recoverable': recoverable,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 根据错误严重程度选择日志级别
        if error_type == 'permanent':
            logger.warning(f"🚫 [{context}] 永久性错误: {ticker} - {error}")
        elif error_type == 'temporary':
            logger.info(f"⏳ [{context}] 临时性错误: {ticker} - {error}")
        elif error_type == 'validation':
            logger.warning(f"📋 [{context}] 验证错误: {ticker} - {error}")
        elif error_type == 'network':
            logger.info(f"🌐 [{context}] 网络错误: {ticker} - {error}")
        else:
            logger.error(f"❌ [{context}] 未知错误: {ticker} - {error}")
    
    def _handle_akshare_error(self, ticker: str, error: Exception) -> tuple[bool, str]:
        """统一处理AKShare错误
        
        Returns:
            tuple: (should_retry, error_type)
        """
        error_msg = str(error).lower()
        
        # 分析具体错误类型
        if 'infocode' in error_msg:
            self._log_structured_error(ticker, error, 'AKShare研报API', 'permanent', False)
            return False, 'infoCode错误 - 股票代码可能不存在或无权限'
            
        elif any(indicator in error_msg for indicator in ['timeout', 'timed out']):
            self._log_structured_error(ticker, error, 'AKShare研报API', 'network', True)
            return True, '网络超时 - 可重试'
            
        elif any(indicator in error_msg for indicator in ['connection', 'network']):
            self._log_structured_error(ticker, error, 'AKShare研报API', 'network', True)
            return True, '网络连接失败 - 可重试'
            
        elif any(indicator in error_msg for indicator in ['rate limit', 'too many', 'busy']):
            self._log_structured_error(ticker, error, 'AKShare研报API', 'temporary', True)
            return True, '访问频率限制 - 可重试'
            
        elif 'not found' in error_msg or 'no data' in error_msg:
            self._log_structured_error(ticker, error, 'AKShare研报API', 'permanent', False)
            return False, '数据不存在 - 该股票可能无研报数据'
            
        else:
            self._log_structured_error(ticker, error, 'AKShare研报API', 'unknown', True)
            return True, f'未知错误 - {error_msg[:100]}'
    
    def _get_error_suggestions(self, ticker: str, error_type: str, board_info: Dict[str, Any] = None) -> List[str]:
        """根据错误类型和板块信息提供解决建议"""
        suggestions = []
        board_name = board_info.get('board_name', '未知') if board_info else '未知'
        board_code = board_info.get('board_code', '') if board_info else ''
        
        if error_type.startswith('infoCode'):
            suggestions.extend([
                f"检查股票代码 {ticker} 是否正确",
                "确认该股票是否有研报覆盖"
            ])
            
            # 根据板块提供特定建议
            if board_code == 'SH_STAR':
                suggestions.extend([
                    "科创板股票研报覆盖相对较少，这是正常情况",
                    "科创板公司多为科技创新企业，可关注公司公告和财报",
                    "建议重点分析基本面和行业发展趋势"
                ])
            elif board_code in ['BJ_MAIN', 'BJ_NEEQ', 'BJ_OTHER']:
                suggestions.extend([
                    "北交所股票研报覆盖有限，流动性相对较低",
                    "建议关注公司定期报告和公告信息",
                    "可重点分析公司成长性和业务模式"
                ])
            elif board_code == 'SZ_GEM':
                suggestions.extend([
                    "创业板股票波动较大，研报覆盖存在差异",
                    "建议结合行业分析和公司成长性评估",
                    "关注公司创新能力和市场前景"
                ])
            else:
                suggestions.append("尝试使用其他数据源")
            
        elif '网络' in error_type:
            suggestions.extend([
                "检查网络连接",
                "稍后重试",
                "使用VPN或更换网络"
            ])
            
        elif '频率限制' in error_type:
            suggestions.extend([
                "降低请求频率",
                "添加请求间隔",
                "考虑升级到付费API"
            ])
            
        elif '数据不存在' in error_type:
            base_suggestion = f"该股票 {ticker} ({board_name}) 可能缺乏机构研报覆盖"
            suggestions.append(base_suggestion)
            
            # 根据板块特性提供建议
            if board_info and board_info.get('special_handling'):
                suggestions.extend([
                    f"{board_name}股票通常研报覆盖较少或需要特殊权限",
                    "建议依赖基本面分析和公司公告",
                    "关注行业研究报告和宏观分析"
                ])
            else:
                suggestions.extend([
                    "依赖其他分析方法（基本面、技术面）",
                    "检查是否为新股或冷门股票"
                ])
                
        elif error_type == 'board_specific':
            suggestions.extend([
                f"{board_name}股票存在特殊限制或数据获取困难",
                "建议使用专门针对该板块的数据源",
                "关注官方交易所公告和行业报告"
            ])
            
        return suggestions
    
    def _safe_get_value(self, row, possible_keys: List[str], default: str = '') -> str:
        """安全地从行数据中获取值"""
        for key in possible_keys:
            if key in row and row[key] is not None:
                value = str(row[key]).strip()
                if value and value.lower() not in ['nan', 'none', 'null', '']:
                    return value
        return default
    
    def _extract_number(self, text: str) -> Optional[float]:
        """从文本中提取数字"""
        try:
            if not text or text.lower() in ['nan', 'none', 'null', '']:
                return None
            
            # 移除常见的非数字字符
            cleaned = re.sub(r'[^\d\.\-\+]', '', str(text))
            if cleaned:
                return float(cleaned)
        except:
            pass
        return None
    
    def _extract_key_points(self, summary: str, title: str) -> List[str]:
        """从摘要和标题中提取关键观点"""
        key_points = []
        
        if not summary or summary == '暂无摘要':
            return key_points
        
        # 基于常见分隔符分割关键观点
        delimiters = ['；', ';', '。', '，', ',', '：', ':', '、']
        sentences = [summary]
        
        for delimiter in delimiters:
            new_sentences = []
            for sentence in sentences:
                new_sentences.extend(sentence.split(delimiter))
            sentences = new_sentences
        
        # 过滤和清理关键观点
        for sentence in sentences:
            cleaned = sentence.strip()
            if len(cleaned) > 5 and len(cleaned) < 100:  # 合理的长度范围
                # 识别具有明确观点的句子
                if any(keyword in cleaned for keyword in ['推荐', '建议', '预计', '预期', '维持', '上调', '下调', '目标', '估值']):
                    key_points.append(cleaned)
        
        # 如果没有提取到关键观点，从标题中提取
        if not key_points and title:
            if '推荐' in title or '买入' in title or '增持' in title:
                key_points.append('维持积极投资建议')
        
        return key_points[:5]  # 最多返回5个关键观点
    
    def _calculate_confidence_level(self, institution: str, analyst: str, publish_date: str) -> float:
        """计算研报可信度评分"""
        base_confidence = 0.6
        
        # 知名机构加分
        top_institutions = ['中信证券', '华泰证券', '国泰君安', '招商证券', '中金公司', '海通证券', '申万宏源', '东方证券', '光大证券', '兴业证券']
        if any(inst in institution for inst in top_institutions):
            base_confidence += 0.2
        
        # 分析师信息完整性加分
        if analyst and analyst != '未知分析师':
            base_confidence += 0.1
        
        # 发布日期新鲜度加分
        try:
            from datetime import datetime, timedelta
            pub_date = datetime.strptime(publish_date, '%Y-%m-%d')
            days_ago = (datetime.now() - pub_date).days
            
            if days_ago <= 30:  # 30天内
                base_confidence += 0.1
            elif days_ago <= 90:  # 90天内
                base_confidence += 0.05
        except:
            pass
        
        return min(base_confidence, 1.0)  # 最高1.0
    
    def _validate_research_data(self, df, ticker: str) -> Dict[str, Any]:
        """验证研报数据质量"""
        try:
            # 基础检查
            if df is None or df.empty:
                return {'is_valid': False, 'reason': '数据为空'}
            
            # 检查是否包含错误信息
            if 'infoCode' in df.columns:
                return {'is_valid': False, 'reason': 'infoCode错误，可能股票代码不存在或无研报数据'}
            
            # 检查列数是否合理
            if len(df.columns) < 3:
                return {'is_valid': False, 'reason': f'列数过少: {len(df.columns)}，数据格式异常'}
            
            # 检查数据行数
            if len(df) == 0:
                return {'is_valid': False, 'reason': '数据行数为0'}
            
            # 检查关键字段是否存在
            required_fields = ['标题', '机构', '日期']
            alternative_fields = [
                ['title', '研报标题', '报告标题'],
                ['institution', '券商', '研究机构'], 
                ['date', '发布日期', '发布时间']
            ]
            
            missing_fields = []
            for i, field_group in enumerate([required_fields] + alternative_fields):
                field_found = False
                for field in field_group:
                    if field in df.columns:
                        field_found = True
                        break
                
                if not field_found and i == 0:  # 检查必须字段
                    missing_fields.extend(field_group)
            
            # 检查数据完整性
            completeness_score = self._calculate_data_completeness(df)
            if completeness_score < 0.3:  # 完整性低于30%
                return {'is_valid': False, 'reason': f'数据完整性过低: {completeness_score:.1%}'}
            
            # 通过所有验证
            return {
                'is_valid': True, 
                'completeness_score': completeness_score,
                'row_count': len(df),
                'column_count': len(df.columns)
            }
            
        except Exception as e:
            return {'is_valid': False, 'reason': f'验证过程异常: {str(e)}'}
    
    def _calculate_data_completeness(self, df) -> float:
        """计算数据完整性评分"""
        try:
            total_cells = df.shape[0] * df.shape[1]
            if total_cells == 0:
                return 0.0
            
            # 计算非空值数量
            non_null_count = 0
            for column in df.columns:
                series = df[column]
                non_null_count += series.count()  # pandas count()会忽略NaN值
            
            return non_null_count / total_cells
            
        except Exception:
            return 0.0
    
    def _clean_research_data(self, df) -> Any:
        """清洗研报数据"""
        try:
            if df is None or df.empty:
                return df
            
            # 创建数据副本避免修改原始数据
            cleaned_df = df.copy()
            
            # 移除完全空的行
            cleaned_df = cleaned_df.dropna(how='all')
            
            # 字符串字段清理
            string_columns = cleaned_df.select_dtypes(include=['object']).columns
            for col in string_columns:
                if col in cleaned_df.columns:
                    # 移除前后空格
                    cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
                    # 替换常见的无效值
                    cleaned_df[col] = cleaned_df[col].replace(['nan', 'NaN', 'None', 'null', ''], None)
            
            # 日期字段标准化
            date_columns = ['日期', 'date', '发布日期', '发布时间']
            for col in date_columns:
                if col in cleaned_df.columns:
                    cleaned_df[col] = self._standardize_date_format(cleaned_df[col])
            
            # 去重（基于标题和机构）
            title_cols = ['标题', 'title', '研报标题']
            institution_cols = ['机构', 'institution', '券商']
            
            title_col = None
            institution_col = None
            
            for col in title_cols:
                if col in cleaned_df.columns:
                    title_col = col
                    break
                    
            for col in institution_cols:
                if col in cleaned_df.columns:
                    institution_col = col
                    break
            
            if title_col and institution_col:
                cleaned_df = cleaned_df.drop_duplicates(subset=[title_col, institution_col], keep='first')
            
            logger.debug(f"数据清洗完成: 原始行数 {len(df)} -> 清洗后 {len(cleaned_df)}")
            return cleaned_df
            
        except Exception as e:
            logger.warning(f"数据清洗失败: {e}，返回原始数据")
            return df
    
    def _standardize_date_format(self, date_series) -> Any:
        """标准化日期格式"""
        try:
            import pandas as pd
            # 尝试转换为标准日期格式
            return pd.to_datetime(date_series, errors='coerce').dt.strftime('%Y-%m-%d')
        except Exception:
            return date_series
    
    def _get_sample_akshare_reports(self, ticker: str, limit: int) -> List[ResearchReport]:
        """获取示例数据"""
        sample_data = [
            {
                'title': f'{ticker} 深度研究报告',
                'analyst': '赵六',
                'institution': '华泰证券',
                'publish_date': '2024-07-20',
                'rating': '买入',
                'target_price_text': '目标价：46元',
                'summary': '公司行业领先地位稳固，维持买入评级'
            }
        ]
        
        reports = []
        for data in sample_data[:limit]:
            report = ResearchReport(
                title=data['title'],
                analyst=data['analyst'],
                institution=data['institution'],
                publish_date=data['publish_date'],
                rating=self._parse_rating(data['rating']),
                target_price=self._extract_price(data['target_price_text']),
                current_price=None,
                summary=data['summary'],
                key_points=[],
                pe_forecast=None,
                revenue_growth=None,
                profit_growth=None,
                source=self.name,
                confidence_level=0.7
            )
            reports.append(report)
        
        return reports


class ResearchReportManager:
    """研报数据管理器"""
    
    def __init__(self):
        self.providers = [
            EastMoneyResearchProvider(),
            TongHuaShunResearchProvider(),
            AKShareResearchProvider()
        ]
        logger.info(f"🚀 研报数据管理器初始化完成，可用数据源: {[p.name for p in self.providers]}")
    
    def get_comprehensive_reports(self, ticker: str, limit_per_source: int = 5) -> List[ResearchReport]:
        """获取综合研报数据"""
        try:
            logger.info(f"📊 开始获取 {ticker} 的综合研报数据")
            
            all_reports = []
            successful_sources = []
            failed_sources = []
            
            # 并行获取各数据源的研报
            for provider in self.providers:
                try:
                    reports = provider.get_reports(ticker, limit_per_source)
                    if reports:  # 只有在有数据时才算成功
                        all_reports.extend(reports)
                        successful_sources.append(provider.name)
                        logger.info(f"✅ {provider.name} 获取到 {len(reports)} 条研报")
                    else:
                        failed_sources.append(provider.name)
                        logger.warning(f"⚠️ {provider.name} 返回空数据")
                except Exception as e:
                    failed_sources.append(provider.name)
                    logger.warning(f"⚠️ {provider.name} 获取研报失败: {str(e)}")
                    continue
            
            # 如果所有数据源都失败，返回空列表，不使用备用数据
            if not all_reports:
                logger.warning(f"⚠️ 所有数据源都失败，无研报数据可用: {ticker}")
                logger.info(f"📊 建议检查网络连接或股票代码是否正确: {ticker}")
                return []
            
            # 数据去重和质量优化
            all_reports = self._deduplicate_and_optimize_reports(all_reports, ticker)
            
            # 按发布时间和可信度综合排序
            all_reports = self._sort_reports_by_quality(all_reports)
            
            logger.info(f"📈 综合获取到 {len(all_reports)} 条研报数据: {ticker}")
            logger.info(f"📊 成功数据源: {successful_sources}, 失败数据源: {failed_sources}")
            return all_reports
            
        except Exception as e:
            logger.error(f"❌ 获取综合研报数据失败: {ticker}, 错误: {str(e)}")
            # 出现异常时返回空列表，不使用备用数据
            return []
    
    def _deduplicate_and_optimize_reports(self, reports: List[ResearchReport], ticker: str) -> List[ResearchReport]:
        """数据去重和质量优化"""
        try:
            if not reports:
                return reports
            
            logger.debug(f"🔄 开始数据去重和优化: {ticker}, 原始数据 {len(reports)} 条")
            
            # 1. 基于标题和机构的去重
            unique_reports = {}
            for report in reports:
                # 创建去重键
                dedup_key = self._create_dedup_key(report)
                
                if dedup_key not in unique_reports:
                    unique_reports[dedup_key] = report
                else:
                    # 如果存在重复，保留质量更高的
                    existing_report = unique_reports[dedup_key]
                    if self._compare_report_quality(report, existing_report) > 0:
                        unique_reports[dedup_key] = report
            
            deduplicated_reports = list(unique_reports.values())
            
            # 2. 数据质量过滤
            quality_reports = []
            for report in deduplicated_reports:
                if self._validate_report_quality(report):
                    quality_reports.append(report)
                else:
                    logger.debug(f"🚮 过滤低质量研报: {report.title[:50]}...")
            
            # 3. 可信度重新计算（基于数据源组合）
            for report in quality_reports:
                report.confidence_level = self._recalculate_confidence(report, quality_reports)
            
            logger.debug(f"✅ 数据优化完成: {ticker}, 去重后 {len(deduplicated_reports)} 条, 质量过滤后 {len(quality_reports)} 条")
            
            return quality_reports
            
        except Exception as e:
            logger.warning(f"⚠️ 数据去重优化失败: {ticker}, {e}, 返回原始数据")
            return reports
    
    def _create_dedup_key(self, report: ResearchReport) -> str:
        """创建去重键"""
        # 标准化标题（去除空格、标点）
        title_cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '', report.title.lower())
        
        # 标准化机构名称
        institution_cleaned = re.sub(r'[^\w\u4e00-\u9fff]', '', report.institution.lower())
        
        # 组合键：标题前20字符 + 机构 + 发布日期
        dedup_key = f"{title_cleaned[:20]}_{institution_cleaned}_{report.publish_date}"
        
        return dedup_key
    
    def _compare_report_quality(self, report1: ResearchReport, report2: ResearchReport) -> int:
        """比较两个研报的质量，返回1表示report1更好，-1表示report2更好，0表示相同"""
        score1 = self._calculate_report_quality_score(report1)
        score2 = self._calculate_report_quality_score(report2)
        
        if score1 > score2:
            return 1
        elif score1 < score2:
            return -1
        else:
            return 0
    
    def _calculate_report_quality_score(self, report: ResearchReport) -> float:
        """计算研报质量评分"""
        score = 0.0
        
        # 基础可信度
        score += report.confidence_level * 40
        
        # 标题质量
        if len(report.title) > 10:
            score += 10
        if len(report.title) > 20:
            score += 5
        
        # 分析师信息
        if report.analyst and report.analyst != '未知分析师':
            score += 10
        
        # 机构权威性
        authoritative_institutions = ['中信证券', '华泰证券', '国泰君安', '招商证券', '中金公司']
        if any(inst in report.institution for inst in authoritative_institutions):
            score += 15
        
        # 评级信息
        if report.rating and report.rating != '未知':
            score += 8
        
        # 目标价
        if report.target_price:
            score += 12
        
        # 摘要质量
        if report.summary and len(report.summary) > 50:
            score += 8
        
        # 关键观点
        if report.key_points:
            score += len(report.key_points) * 3
        
        # 时效性
        try:
            from datetime import datetime, timedelta
            pub_date = datetime.strptime(report.publish_date, '%Y-%m-%d')
            days_old = (datetime.now() - pub_date).days
            
            if days_old <= 7:
                score += 10
            elif days_old <= 30:
                score += 5
            elif days_old <= 90:
                score += 2
        except:
            pass
        
        return score
    
    def _validate_report_quality(self, report: ResearchReport) -> bool:
        """验证研报基本质量要求"""
        # 标题长度检查
        if not report.title or len(report.title) < 5:
            return False
        
        # 机构信息检查
        if not report.institution or report.institution in ['未知机构', '']:
            return False
        
        # 可信度检查
        if report.confidence_level < 0.3:
            return False
        
        return True
    
    def _recalculate_confidence(self, report: ResearchReport, all_reports: List[ResearchReport]) -> float:
        """基于整体数据重新计算可信度"""
        base_confidence = report.confidence_level
        
        # 如果同一机构有多份研报，提高可信度
        same_institution_count = sum(1 for r in all_reports if r.institution == report.institution)
        if same_institution_count > 1:
            base_confidence += 0.1
        
        # 如果有目标价且在合理范围内，提高可信度
        if report.target_price:
            base_confidence += 0.05
        
        # 确保可信度在合理范围内
        return min(max(base_confidence, 0.0), 1.0)
    
    def _sort_reports_by_quality(self, reports: List[ResearchReport]) -> List[ResearchReport]:
        """按质量和时效性综合排序"""
        try:
            def sort_key(report):
                # 综合评分：质量分数 + 时效性分数
                quality_score = self._calculate_report_quality_score(report)
                
                # 时效性分数
                recency_score = 0
                try:
                    from datetime import datetime
                    pub_date = datetime.strptime(report.publish_date, '%Y-%m-%d')
                    days_old = (datetime.now() - pub_date).days
                    recency_score = max(0, 100 - days_old)  # 最近的研报分数更高
                except:
                    recency_score = 0
                
                # 综合分数（质量权重70%，时效性权重30%）
                total_score = quality_score * 0.7 + recency_score * 0.3
                
                return total_score
            
            sorted_reports = sorted(reports, key=sort_key, reverse=True)
            logger.debug(f"📊 研报排序完成，按质量和时效性排序")
            
            return sorted_reports
            
        except Exception as e:
            logger.warning(f"⚠️ 研报排序失败: {e}，保持原顺序")
            return reports
    
    
    def analyze_consensus(self, reports: List[ResearchReport]) -> Dict[str, Any]:
        """分析机构一致预期"""
        try:
            if not reports:
                return {}
            
            # 评级统计
            ratings = [r.rating for r in reports if r.rating != '未知']
            rating_counts = {}
            for rating in ratings:
                rating_counts[rating] = rating_counts.get(rating, 0) + 1
            
            # 目标价统计
            target_prices = [r.target_price for r in reports if r.target_price is not None]
            avg_target_price = sum(target_prices) / len(target_prices) if target_prices else None
            
            # PE预测统计
            pe_forecasts = [r.pe_forecast for r in reports if r.pe_forecast is not None]
            avg_pe_forecast = sum(pe_forecasts) / len(pe_forecasts) if pe_forecasts else None
            
            # 增长预测统计
            revenue_growths = [r.revenue_growth for r in reports if r.revenue_growth is not None]
            profit_growths = [r.profit_growth for r in reports if r.profit_growth is not None]
            
            avg_revenue_growth = sum(revenue_growths) / len(revenue_growths) if revenue_growths else None
            avg_profit_growth = sum(profit_growths) / len(profit_growths) if profit_growths else None
            
            # 机构覆盖度
            institutions = list(set([r.institution for r in reports if r.institution]))
            
            consensus = {
                'total_reports': len(reports),
                'rating_distribution': rating_counts,
                'average_target_price': avg_target_price,
                'target_price_range': {
                    'min': min(target_prices) if target_prices else None,
                    'max': max(target_prices) if target_prices else None
                },
                'average_pe_forecast': avg_pe_forecast,
                'average_revenue_growth': avg_revenue_growth,
                'average_profit_growth': avg_profit_growth,
                'covering_institutions': institutions,
                'institution_count': len(institutions),
                'data_sources': list(set([r.source for r in reports])),
                'latest_report_date': max([r.publish_date for r in reports]) if reports else None
            }
            
            return consensus
            
        except Exception as e:
            logger.error(f"❌ 分析机构一致预期失败: {str(e)}")
            return {}


# 全局研报管理器实例
_research_manager = None

def get_research_report_manager() -> ResearchReportManager:
    """获取研报管理器单例"""
    global _research_manager
    if _research_manager is None:
        _research_manager = ResearchReportManager()
    return _research_manager


# 便捷函数
def get_stock_research_reports(ticker: str, limit: int = 15) -> List[ResearchReport]:
    """获取股票研报数据"""
    manager = get_research_report_manager()
    return manager.get_comprehensive_reports(ticker, limit // 3)  # 每个数据源取limit/3条


def get_institutional_consensus(ticker: str) -> Dict[str, Any]:
    """获取机构一致预期"""
    reports = get_stock_research_reports(ticker)
    manager = get_research_report_manager()
    return manager.analyze_consensus(reports)


if __name__ == "__main__":
    # 测试代码
    ticker = "000001"
    
    print(f"🔍 测试获取 {ticker} 的研报数据...")
    reports = get_stock_research_reports(ticker)
    print(f"📊 获取到 {len(reports)} 条研报")
    
    if reports:
        print(f"📈 最新研报: {reports[0].title}")
        print(f"📈 评级: {reports[0].rating}")
        print(f"📈 目标价: {reports[0].target_price}")
    
    print(f"\n🎯 机构一致预期分析:")
    consensus = get_institutional_consensus(ticker)
    for key, value in consensus.items():
        print(f"  {key}: {value}")