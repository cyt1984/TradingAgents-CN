import sys
import os
import requests
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_tencent_kline():
    """调试腾讯K线API"""
    
    # 腾讯股票代码
    symbol = '000001'
    tencent_code = f"sz{symbol}"
    
    # 腾讯K线API
    api_url = "https://web.ifzq.gtimg.cn/appstock/app/kline/kline"
    params = {
        'param': f'{tencent_code},day,,10',
        '_var': 'kline_day',
        'r': str(int(__import__('time').time() * 1000))
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://finance.qq.com/'
    }
    
    try:
        print("Testing Tencent K-line API...")
        print(f"URL: {api_url}")
        print(f"Params: {params}")
        
        response = requests.get(api_url, params=params, headers=headers, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response length: {len(response.text)}")
        print(f"Response preview: {response.text[:200]}...")
        
        # 尝试解析
        if response.status_code == 200:
            start_idx = response.text.find('{')
            if start_idx != -1:
                json_str = response.text[start_idx:]
                try:
                    data = json.loads(json_str)
                    print("Parsed JSON keys:", list(data.keys()))
                    
                    if 'data' in data and tencent_code in data['data']:
                        kline_data = data['data'][tencent_code].get('day', [])
                        print(f"K-line records: {len(kline_data)}")
                        if kline_data:
                            print("Sample record:", kline_data[0])
                    else:
                        print("No kline data found")
                        print("Available keys:", list(data.get('data', {}).keys()) if 'data' in data else "No data key")
                        
                except Exception as e:
                    print(f"JSON parse error: {e}")
            else:
                print("No JSON found in response")
        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    debug_tencent_kline()