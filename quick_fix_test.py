#!/usr/bin/env python3
"""
快速修复测试脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_validation_fix():
    """测试参数验证修复"""
    print("测试股票代码验证修复")
    print("=" * 40)
    
    try:
        from web.utils.analysis_runner import validate_analysis_params
        
        # 测试A股代码
        print("测试A股代码 000001...")
        is_valid, errors = validate_analysis_params(
            stock_symbol="000001",
            analysis_date="2025-08-02",
            analysts=["market"],
            research_depth=1,
            market_type="A股"  # 关键：使用正确的市场类型
        )
        
        print(f"验证结果: {is_valid}")
        if errors:
            print(f"错误信息: {errors}")
        else:
            print("验证通过！")
            
        # 测试美股代码
        print("\n测试美股代码 AAPL...")
        is_valid2, errors2 = validate_analysis_params(
            stock_symbol="AAPL",
            analysis_date="2025-08-02",
            analysts=["market"],
            research_depth=1,
            market_type="美股"
        )
        
        print(f"验证结果: {is_valid2}")
        if errors2:
            print(f"错误信息: {errors2}")
        else:
            print("验证通过！")
            
        return is_valid and is_valid2
        
    except Exception as e:
        print(f"测试失败: {e}")
        return False

def test_basic_analysis():
    """测试基本分析功能"""
    print("\n测试基本分析功能")
    print("=" * 40)
    
    try:
        from web.utils.analysis_runner import run_stock_analysis
        
        print("尝试运行简单的A股分析...")
        
        # 设置基本参数
        stock_symbol = "000001"
        analysis_date = "2025-08-02"
        analysts = ["market"]  # 只使用市场分析师
        research_depth = 1     # 最低复杂度
        llm_provider = "dashscope"  # 使用已配置的阿里百炼
        llm_model = "qwen-turbo"    # 最快的模型
        market_type = "A股"
        
        print(f"参数: {stock_symbol}, {market_type}, {llm_provider}, {llm_model}")
        
        # 运行分析（超时5分钟）
        results = run_stock_analysis(
            stock_symbol=stock_symbol,
            analysis_date=analysis_date,
            analysts=analysts,
            research_depth=research_depth,
            llm_provider=llm_provider,
            llm_model=llm_model,
            market_type=market_type
        )
        
        print("分析完成！")
        print(f"结果类型: {type(results)}")
        
        if isinstance(results, dict):
            print(f"有分析结果: {bool(results.get('analysis_summary'))}")
            if results.get('error'):
                print(f"分析错误: {results['error']}")
        
        return True
        
    except Exception as e:
        print(f"分析测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("TradingAgents-CN 快速修复测试")
    print("=" * 50)
    
    success1 = test_validation_fix()
    if success1:
        print("\n✅ 参数验证已修复！")
        
        # 如果验证通过，尝试实际分析
        success2 = test_basic_analysis()
        if success2:
            print("\n✅ 基本分析功能正常！")
        else:
            print("\n❌ 分析功能仍有问题")
            
        return success2
    else:
        print("\n❌ 参数验证仍有问题")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)