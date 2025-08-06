#!/usr/bin/env python3
"""
Comprehensive East Money API Validation Script
Systematically tests East Money data source across all A-share categories
"""

import sys
import os
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tradingagents.dataflows.eastmoney_utils import EastMoneyProvider
from tradingagents.dataflows.research_report_utils import EastMoneyResearchProvider
from tradingagents.utils.logging_manager import get_logger

logger = get_logger('comprehensive_test')

class EastMoneyAPITester:
    """Comprehensive East Money API testing class"""
    
    def __init__(self):
        self.provider = EastMoneyProvider()
        self.research_provider = EastMoneyResearchProvider()
        self.results = []
        
    def get_test_stocks(self) -> List[Dict[str, Any]]:
        """Get comprehensive test stock list covering all categories"""
        return [
            # 深证主板
            {"code": "000001", "name": "平安银行", "exchange": "SZ", "board": "主板"},
            {"code": "000858", "name": "五粮液", "exchange": "SZ", "board": "主板"},
            {"code": "000002", "name": "万科A", "exchange": "SZ", "board": "主板"},
            
            # 上证主板
            {"code": "600036", "name": "招商银行", "exchange": "SH", "board": "主板"},
            {"code": "600519", "name": "贵州茅台", "exchange": "SH", "board": "主板"},
            {"code": "601398", "name": "工商银行", "exchange": "SH", "board": "主板"},
            
            # 中小板
            {"code": "002602", "name": "世纪华通", "exchange": "SZ", "board": "中小板"},
            {"code": "002027", "name": "分众传媒", "exchange": "SZ", "board": "中小板"},
            {"code": "002594", "name": "比亚迪", "exchange": "SZ", "board": "中小板"},
            
            # 创业板
            {"code": "300750", "name": "宁德时代", "exchange": "SZ", "board": "创业板"},
            {"code": "300059", "name": "东方财富", "exchange": "SZ", "board": "创业板"},
            {"code": "300124", "name": "汇川技术", "exchange": "SZ", "board": "创业板"},
            
            # 科创板
            {"code": "688111", "name": "金山办公", "exchange": "SH", "board": "科创板"},
            {"code": "688981", "name": "中芯国际", "exchange": "SH", "board": "科创板"},
            {"code": "688036", "name": "传音控股", "exchange": "SH", "board": "科创板"},
            
            # 北交所
            {"code": "430047", "name": "诺思兰德", "exchange": "BJ", "board": "北交所"},
            {"code": "830799", "name": "艾融软件", "exchange": "BJ", "board": "北交所"},
        ]
    
    def test_basic_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Test basic stock information retrieval"""
        try:
            start_time = time.time()
            data = self.provider.get_stock_info(symbol)
            elapsed = time.time() - start_time
            
            return {
                "endpoint": "basic_info",
                "symbol": symbol,
                "success": data is not None,
                "data": data,
                "response_time": elapsed,
                "error": None if data else "No data returned"
            }
        except Exception as e:
            return {
                "endpoint": "basic_info",
                "symbol": symbol,
                "success": False,
                "data": None,
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    def test_financial_data(self, symbol: str) -> Dict[str, Any]:
        """Test financial data retrieval"""
        try:
            start_time = time.time()
            data = self.provider.get_financial_data(symbol)
            elapsed = time.time() - start_time
            
            return {
                "endpoint": "financial_data",
                "symbol": symbol,
                "success": data is not None,
                "data": data,
                "response_time": elapsed,
                "error": None if data else "No financial data returned"
            }
        except Exception as e:
            return {
                "endpoint": "financial_data",
                "symbol": symbol,
                "success": False,
                "data": None,
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    def test_research_reports(self, symbol: str) -> Dict[str, Any]:
        """Test research reports retrieval"""
        try:
            start_time = time.time()
            data = self.provider.get_research_reports(symbol)
            elapsed = time.time() - start_time
            
            return {
                "endpoint": "research_reports",
                "symbol": symbol,
                "success": len(data) > 0,
                "data_count": len(data),
                "sample_data": data[:2] if data else [],
                "response_time": elapsed,
                "error": None if data else "No research reports returned"
            }
        except Exception as e:
            return {
                "endpoint": "research_reports",
                "symbol": symbol,
                "success": False,
                "data_count": 0,
                "sample_data": [],
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    def test_stock_news(self, symbol: str) -> Dict[str, Any]:
        """Test stock news retrieval"""
        try:
            start_time = time.time()
            data = self.provider.get_stock_news(symbol)
            elapsed = time.time() - start_time
            
            return {
                "endpoint": "stock_news",
                "symbol": symbol,
                "success": len(data) > 0,
                "data_count": len(data),
                "sample_data": data[:2] if data else [],
                "response_time": elapsed,
                "error": None if data else "No news returned"
            }
        except Exception as e:
            return {
                "endpoint": "stock_news",
                "symbol": symbol,
                "success": False,
                "data_count": 0,
                "sample_data": [],
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    def test_market_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Test market sentiment retrieval"""
        try:
            start_time = time.time()
            data = self.provider.get_market_sentiment(symbol)
            elapsed = time.time() - start_time
            
            return {
                "endpoint": "market_sentiment",
                "symbol": symbol,
                "success": data is not None,
                "data": data,
                "response_time": elapsed,
                "error": None if data else "No sentiment data returned"
            }
        except Exception as e:
            return {
                "endpoint": "market_sentiment",
                "symbol": symbol,
                "success": False,
                "data": None,
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    def test_research_provider(self, symbol: str) -> Dict[str, Any]:
        """Test East Money research provider"""
        try:
            start_time = time.time()
            data = self.research_provider.get_reports(symbol)
            elapsed = time.time() - start_time
            
            return {
                "endpoint": "research_provider",
                "symbol": symbol,
                "success": len(data) > 0,
                "data_count": len(data),
                "sample_data": [
                    {
                        "title": r.title,
                        "institution": r.institution,
                        "rating": r.rating,
                        "target_price": r.target_price
                    } for r in data[:2]
                ] if data else [],
                "response_time": elapsed,
                "error": None if data else "No research data returned"
            }
        except Exception as e:
            return {
                "endpoint": "research_provider",
                "symbol": symbol,
                "success": False,
                "data_count": 0,
                "sample_data": [],
                "response_time": time.time() - start_time,
                "error": str(e)
            }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        logger.info("🚀 Starting comprehensive East Money API validation...")
        
        test_stocks = self.get_test_stocks()
        all_results = []
        
        total_tests = len(test_stocks) * 6  # 6 endpoints per stock
        completed = 0
        
        for stock in test_stocks:
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 Testing {stock['code']} ({stock['name']}) - {stock['board']}")
            
            stock_results = {
                "stock": stock,
                "tests": {}
            }
            
            # Test all endpoints
            endpoints = [
                ("basic_info", self.test_basic_stock_info),
                ("financial_data", self.test_financial_data),
                ("research_reports", self.test_research_reports),
                ("stock_news", self.test_stock_news),
                ("market_sentiment", self.test_market_sentiment),
                ("research_provider", self.test_research_provider)
            ]
            
            for endpoint_name, test_func in endpoints:
                logger.info(f"  📊 Testing {endpoint_name}...")
                result = test_func(stock['code'])
                stock_results["tests"][endpoint_name] = result
                completed += 1
                
                # Rate limiting
                time.sleep(0.5)
            
            all_results.append(stock_results)
            
            # Progress indicator
            progress = (completed / total_tests) * 100
            logger.info(f"📈 Progress: {progress:.1f}% ({completed}/{total_tests})")
        
        return self.generate_report(all_results)
    
    def generate_report(self, results: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        report = {
            "summary": {
                "total_stocks": len(results),
                "test_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "overall_success_rate": 0.0
            },
            "by_exchange": {},
            "by_board": {},
            "by_endpoint": {},
            "failures": [],
            "detailed_results": results
        }
        
        # Calculate statistics
        total_tests = 0
        successful_tests = 0
        
        for stock_result in results:
            exchange = stock_result["stock"]["exchange"]
            board = stock_result["stock"]["board"]
            
            if exchange not in report["by_exchange"]:
                report["by_exchange"][exchange] = {"total": 0, "success": 0, "failed": 0}
            if board not in report["by_board"]:
                report["by_board"][board] = {"total": 0, "success": 0, "failed": 0}
            
            for endpoint, result in stock_result["tests"].items():
                if endpoint not in report["by_endpoint"]:
                    report["by_endpoint"][endpoint] = {"total": 0, "success": 0, "failed": 0}
                
                total_tests += 1
                report["by_exchange"][exchange]["total"] += 1
                report["by_board"][board]["total"] += 1
                report["by_endpoint"][endpoint]["total"] += 1
                
                if result["success"]:
                    successful_tests += 1
                    report["by_exchange"][exchange]["success"] += 1
                    report["by_board"][board]["success"] += 1
                    report["by_endpoint"][endpoint]["success"] += 1
                else:
                    report["by_exchange"][exchange]["failed"] += 1
                    report["by_board"][board]["failed"] += 1
                    report["by_endpoint"][endpoint]["failed"] += 1
                    
                    report["failures"].append({
                        "stock": stock_result["stock"],
                        "endpoint": endpoint,
                        "error": result["error"]
                    })
        
        report["summary"]["overall_success_rate"] = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        report["summary"]["total_tests"] = total_tests
        report["summary"]["successful_tests"] = successful_tests
        report["summary"]["failed_tests"] = total_tests - successful_tests
        
        return report
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save test report to file"""
        if not filename:
            filename = f"eastmoney_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📊 Test report saved to: {filepath}")
        return filepath


def main():
    """Main testing function"""
    logger.info("🚀 Starting comprehensive East Money API validation...")
    
    tester = EastMoneyAPITester()
    
    try:
        # Run comprehensive test
        results = tester.run_comprehensive_test()
        
        # Save detailed report
        report_file = tester.save_report(results)
        
        # Print summary
        logger.info(f"\n{'='*80}")
        logger.info("📊 EAST MONEY API VALIDATION SUMMARY")
        logger.info(f"{'='*80}")
        logger.info(f"✅ Overall Success Rate: {results['summary']['overall_success_rate']:.1f}%")
        logger.info(f"📈 Total Tests: {results['summary']['total_tests']}")
        logger.info(f"✅ Successful: {results['summary']['successful_tests']}")
        logger.info(f"❌ Failed: {results['summary']['failed_tests']}")
        
        # Print by exchange
        logger.info(f"\n📊 Results by Exchange:")
        for exchange, stats in results['by_exchange'].items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"  {exchange}: {success_rate:.1f}% ({stats['success']}/{stats['total']})")
        
        # Print by board
        logger.info(f"\n📊 Results by Board:")
        for board, stats in results['by_board'].items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"  {board}: {success_rate:.1f}% ({stats['success']}/{stats['total']})")
        
        # Print by endpoint
        logger.info(f"\n📊 Results by Endpoint:")
        for endpoint, stats in results['by_endpoint'].items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            logger.info(f"  {endpoint}: {success_rate:.1f}% ({stats['success']}/{stats['total']})")
        
        # Print failures
        if results['failures']:
            logger.info(f"\n❌ Failures:")
            for failure in results['failures'][:10]:  # Show first 10 failures
                logger.info(f"  {failure['stock']['code']} ({failure['stock']['board']}) - {failure['endpoint']}: {failure['error']}")
        
        logger.info(f"\n📋 Full report saved to: {report_file}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return None


if __name__ == "__main__":
    results = main()
    sys.exit(0 if results and results['summary']['overall_success_rate'] > 50 else 1)