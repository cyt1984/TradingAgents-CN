#!/usr/bin/env python3
"""
调试AkShare数据列结构
"""

def check_akshare_data():
    """检查AkShare返回的数据结构"""
    try:
        import akshare as ak
        
        print("📊 获取AkShare股票数据...")
        stock_data = ak.stock_zh_a_spot_em()
        
        print(f"✅ 获取到 {len(stock_data)} 只股票")
        print(f"📋 数据列名: {list(stock_data.columns)}")
        
        print("\n📊 前3行数据:")
        print(stock_data.head(3))
        
        print("\n🔍 检查名称列:")
        if '名称' in stock_data.columns:
            print(f"名称列前5个值: {stock_data['名称'].head().tolist()}")
        
        if '代码' in stock_data.columns:
            print(f"代码列前5个值: {stock_data['代码'].head().tolist()}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")

if __name__ == "__main__":
    check_akshare_data()