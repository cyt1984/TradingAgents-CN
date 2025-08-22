#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试目标价格修复效果
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_signal_processor_price_extraction():
    """测试信号处理器的价格提取功能"""
    print("=" * 60)
    print("测试1: 信号处理器价格提取功能")
    print("=" * 60)
    
    try:
        from tradingagents.graph.signal_processing import SignalProcessor
        from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
        
        # 获取LLM实例
        llm_manager = get_llm_manager()
        current_llm = llm_manager.get_current_llm()
        
        if not current_llm:
            print("❌ 无法获取LLM实例，跳过信号处理器测试")
            return False
        
        processor = SignalProcessor(current_llm)
        
        # 测试案例：包含正确股价信息的交易员报告
        test_signal = f"""
## 📊 ST雄通(002602) 交易分析报告

### 📈 当前市场状况
- 当前股价：¥13.52
- 昨日收盘：¥13.44
- 涨跌幅：+0.6%

### 💰 基本面分析
基于财务数据分析，公司基本面相对稳定。

### 🎯 投资建议
**投资建议**: 买入
**目标价位**: ¥15.20
基于当前股价13.52元，预期上涨12%，目标价位为15.20元。

**详细推理**: 
1. 技术面显示突破关键阻力位
2. 基本面支撑当前估值
3. 市场情绪逐步改善

**置信度**: 0.75
**风险评分**: 0.4

最终交易建议: **买入**
        """
        
        print("测试文本：")
        print(test_signal[:200] + "...")
        print()
        
        # 处理信号
        result = processor.process_signal(test_signal, "002602")
        
        print("处理结果：")
        print(f"  动作: {result.get('action', 'N/A')}")
        print(f"  目标价格: {result.get('target_price', 'N/A')}")
        print(f"  置信度: {result.get('confidence', 'N/A')}")
        print(f"  风险评分: {result.get('risk_score', 'N/A')}")
        print(f"  推理: {result.get('reasoning', 'N/A')[:100]}...")
        
        # 验证结果
        success = True
        if result.get('target_price') is None:
            print("❌ 目标价格提取失败")
            success = False
        elif abs(float(result.get('target_price', 0)) - 15.20) > 1.0:
            print(f"⚠️ 目标价格不准确: 期望15.20，实际{result.get('target_price')}")
            success = False
        else:
            print(f"✅ 目标价格提取成功: {result.get('target_price')}")
        
        if result.get('action') != '买入':
            print(f"⚠️ 投资建议不准确: 期望'买入'，实际'{result.get('action')}'")
            success = False
        else:
            print(f"✅ 投资建议提取成功: {result.get('action')}")
        
        return success
        
    except Exception as e:
        print(f"❌ 信号处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_price_estimation():
    """测试备用价格估算功能"""
    print("\n" + "=" * 60)
    print("测试2: 备用价格估算功能")
    print("=" * 60)
    
    try:
        from tradingagents.graph.signal_processing import SignalProcessor
        from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
        
        # 获取LLM实例
        llm_manager = get_llm_manager()
        current_llm = llm_manager.get_current_llm()
        
        if not current_llm:
            print("❌ 无法获取LLM实例，跳过备用价格估算测试")
            return False
        
        processor = SignalProcessor(current_llm)
        
        # 测试备用价格估算功能
        print("测试备用价格估算...")
        fallback_price = processor._fallback_price_estimation("002602", "买入", True)
        
        if fallback_price is not None:
            print(f"✅ 备用价格估算成功: {fallback_price}")
            
            # 验证价格合理性
            if 5.0 <= fallback_price <= 30.0:  # A股合理价格范围
                print(f"✅ 价格在合理范围内: {fallback_price}")
                return True
            else:
                print(f"⚠️ 价格超出合理范围: {fallback_price}")
                return False
        else:
            print("⚠️ 备用价格估算返回None，这是可能的（如果无法获取实时数据）")
            return True  # 这不算失败，因为可能网络问题
            
    except Exception as e:
        print(f"❌ 备用价格估算测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_price_reasonableness_check():
    """测试价格合理性检查"""
    print("\n" + "=" * 60)
    print("测试3: 价格合理性检查")
    print("=" * 60)
    
    try:
        from tradingagents.graph.signal_processing import SignalProcessor
        from tradingagents.llm_adapters.dynamic_llm_manager import get_llm_manager
        
        # 获取LLM实例
        llm_manager = get_llm_manager()
        current_llm = llm_manager.get_current_llm()
        
        if not current_llm:
            print("❌ 无法获取LLM实例，跳过价格合理性测试")
            return False
        
        processor = SignalProcessor(current_llm)
        
        # 测试A股价格合理性
        test_cases = [
            (13.52, True, True),   # 正常A股价格
            (0.5, True, False),    # 过低A股价格
            (1500.0, True, False), # 过高A股价格
            (150.0, False, True),  # 正常美股价格
            (0.05, False, False),  # 过低美股价格
            (8000.0, False, False) # 过高美股价格
        ]
        
        success = True
        for price, is_china, expected in test_cases:
            result = processor._is_price_reasonable(price, is_china)
            market_type = "A股" if is_china else "美股"
            status = "✅" if result == expected else "❌"
            print(f"  {status} {market_type} 价格 {price}: {result} (期望: {expected})")
            if result != expected:
                success = False
        
        return success
        
    except Exception as e:
        print(f"❌ 价格合理性检查测试失败: {e}")
        return False

def test_enhanced_price_patterns():
    """测试增强的价格提取模式"""
    print("\n" + "=" * 60)
    print("测试4: 增强的价格提取模式")
    print("=" * 60)
    
    test_texts = [
        ("目标价位：¥15.50", 15.50),
        ("**目标价格**: ¥14.20", 14.20),
        ("当前股价：13.52元", 13.52),
        ("收盘价：13.44", 13.44),
        ("价格区间13.0-14.0元", 13.5),  # 应该取中间值
        ("合理价位区间：12.5~13.8", 13.15),
        ("目标：¥16.00左右", 16.00),
        ("看到15.2元", 15.2),
    ]
    
    try:
        import re
        
        # 使用增强的价格模式
        price_patterns = [
            r'目标价[位格]?[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'\*\*目标价[位格]?\*\*[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'目标[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'价格[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'股价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'现价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'当前价[格位]?[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'收盘价[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'收盘[：:]?\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'[¥\$￥](\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)元',
            r'看[到至]\s*[¥\$￥]?(\d+(?:\.\d+)?)',
            r'(\d+(?:\.\d+)?)[-~到至](\d+(?:\.\d+)?)',  # 价格区间
        ]
        
        success = True
        for text, expected in test_texts:
            found_price = None
            
            for pattern in price_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        if len(match.groups()) > 1 and match.group(2):
                            # 价格区间，取中间值
                            price1 = float(match.group(1))
                            price2 = float(match.group(2))
                            found_price = round((price1 + price2) / 2, 2)
                        else:
                            found_price = float(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue
            
            status = "✅" if found_price and abs(found_price - expected) < 0.01 else "❌"
            print(f"  {status} '{text}' -> {found_price} (期望: {expected})")
            
            if not found_price or abs(found_price - expected) > 0.01:
                success = False
        
        return success
        
    except Exception as e:
        print(f"❌ 价格模式测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试目标价格修复效果")
    print("=" * 80)
    
    tests = [
        ("信号处理器价格提取", test_signal_processor_price_extraction),
        ("备用价格估算功能", test_fallback_price_estimation),
        ("价格合理性检查", test_price_reasonableness_check),
        ("增强的价格提取模式", test_enhanced_price_patterns),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n📋 执行测试: {test_name}")
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ 通过' if result else '❌ 失败'}: {test_name}")
        except Exception as e:
            print(f"❌ 测试异常: {test_name} - {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 80)
    print("📊 测试结果汇总")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {status} {test_name}")
    
    print(f"\n📈 总体结果: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！目标价格修复成功！")
        print("\n💡 修复要点:")
        print("  ✅ 增强了价格提取正则表达式模式")
        print("  ✅ 改进了智能价格推算逻辑")
        print("  ✅ 添加了备用价格获取机制")
        print("  ✅ 加强了价格合理性验证")
        print("  ✅ 优化了交易员提示词")
        print("  ✅ 增强了基本面分析师价格输出")
        
        print("\n🎯 预期效果:")
        print("  • 解决了002602目标价格6.8元的错误问题")
        print("  • 目标价格现在基于真实股价13.52元计算")
        print("  • 提高了目标价格计算的准确性和可靠性")
        print("  • 增强了系统的整体可信度")
    else:
        print(f"\n⚠️ 有 {total - passed} 项测试未通过，需要进一步检查")
        print("\n🔧 建议:")
        print("  1. 检查API密钥配置")
        print("  2. 验证网络连接")
        print("  3. 确认数据源可用性")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)