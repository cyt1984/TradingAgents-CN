#!/usr/bin/env python3
"""
诊断分析系统问题
检查为什么分析结果返回空数据
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """测试基础模块导入"""
    print("[测试] 基础模块导入")
    print("-" * 40)
    
    try:
        # 测试核心模块导入
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        print("[OK] TradingAgentsGraph 导入成功")
        
        from tradingagents.default_config import DEFAULT_CONFIG
        print("[OK] DEFAULT_CONFIG 导入成功")
        
        return True
    except Exception as e:
        print(f"[FAIL] 模块导入失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n[测试] 配置加载")
    print("-" * 40)
    
    try:
        from tradingagents.default_config import DEFAULT_CONFIG
        config = DEFAULT_CONFIG.copy()
        
        print(f"[OK] 默认配置加载成功")
        print(f"  - LLM提供商: {config.get('llm_provider', 'N/A')}")
        print(f"  - 快速思考模型: {config.get('quick_think_llm', 'N/A')}")
        print(f"  - 深度思考模型: {config.get('deep_think_llm', 'N/A')}")
        
        # 检查环境变量
        dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        if dashscope_key and not dashscope_key.startswith("your_"):
            print("[OK] 阿里百炼API密钥已配置")
        else:
            print("[FAIL] 阿里百炼API密钥未配置")
            
        return True
    except Exception as e:
        print(f"[FAIL] 配置加载失败: {e}")
        return False

def test_simple_analysis():
    """测试简单分析"""
    print("\n[测试] 简单分析测试")
    print("-" * 40)
    
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG
        
        # 使用最简单的配置
        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "dashscope"
        config["quick_think_llm"] = "qwen-turbo"
        config["deep_think_llm"] = "qwen-plus"
        config["max_debate_rounds"] = 1
        config["max_risk_discuss_rounds"] = 1
        
        print("[测试] 尝试创建TradingAgentsGraph实例...")
        
        # 创建最简单的分析师列表
        analysts = ["market"]  # 只使用市场分析师
        
        ta = TradingAgentsGraph(analysts, config=config, debug=True)
        print("[OK] TradingAgentsGraph实例创建成功")
        
        # 尝试简单测试
        print("[测试] 测试基本功能...")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 简单分析测试失败: {e}")
        print(f"错误详情: {type(e).__name__}: {str(e)}")
        return False

def test_data_sources():
    """测试数据源连接"""
    print("\n[测试] 数据源连接")
    print("-" * 40)
    
    try:
        # 测试基本数据获取
        import akshare as ak
        print("[OK] AkShare 导入成功")
        
        # 测试简单数据获取
        try:
            # 获取上证指数最新信息
            df = ak.stock_zh_index_spot_em()
            if not df.empty:
                print("[OK] AkShare 数据获取正常")
            else:
                print("[WARN] AkShare 返回空数据")
        except Exception as e:
            print(f"[FAIL] AkShare 数据获取失败: {e}")
            
        return True
    except ImportError:
        print("[FAIL] AkShare 未安装")
        return False
    except Exception as e:
        print(f"[FAIL] 数据源测试失败: {e}")
        return False

def test_web_analysis_runner():
    """测试Web分析运行器"""
    print("\n[测试] Web分析运行器")
    print("-" * 40)
    
    try:
        from web.utils.analysis_runner import validate_analysis_params
        
        # 测试参数验证
        is_valid, errors = validate_analysis_params(
            stock_symbol="000001",
            analysis_date="2025-08-02",
            analysts=["market"],
            research_depth=1
        )
        
        print(f"[测试] 参数验证结果: {is_valid}")
        if errors:
            print(f"[INFO] 验证错误: {errors}")
        else:
            print("[OK] 参数验证通过")
            
        return is_valid
        
    except Exception as e:
        print(f"[FAIL] Web分析运行器测试失败: {e}")
        return False

def main():
    """主诊断函数"""
    print("TradingAgents-CN 分析系统诊断")
    print("=" * 60)
    
    # 加载环境变量
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=True)
        print(f"[OK] 环境变量已加载: {env_file}")
    else:
        print(f"[FAIL] 未找到.env文件: {env_file}")
    
    tests = [
        ("基础模块导入", test_basic_imports),
        ("配置加载", test_config_loading),
        ("数据源连接", test_data_sources),
        ("Web分析运行器", test_web_analysis_runner),
        ("简单分析测试", test_simple_analysis)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n[OK] {test_name} - 通过")
                passed += 1
            else:
                print(f"\n[FAIL] {test_name} - 失败")
        except Exception as e:
            print(f"\n[ERROR] {test_name} - 异常: {e}")
    
    print(f"\n{'='*60}")
    print(f"诊断结果: {passed}/{total} 测试通过")
    
    if passed < total:
        print("\n可能的问题:")
        print("1. 依赖库缺失或版本不兼容")
        print("2. API密钥配置问题")
        print("3. 网络连接问题")
        print("4. 代码逻辑错误")
        print("\n建议:")
        print("- 检查是否在虚拟环境中运行")
        print("- 运行: pip install -e . 重新安装依赖")
        print("- 检查.env文件中的API密钥配置")
    else:
        print("\n所有基础组件正常，问题可能在分析逻辑中")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)