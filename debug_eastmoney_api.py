#!/usr/bin/env python3
"""
东方财富API调试脚本
直接测试API调用和响应解析
"""

import requests
import json
import re
import time
import random

def test_direct_api_call():
    """直接测试API调用"""
    print("测试东方财富API直接调用...")
    
    # API配置
    base_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
        'Accept': '*/*',
    }
    
    # 生成回调函数名
    callback = f"jQuery{random.randint(100000000000000000000, 999999999999999999999)}_{int(time.time() * 1000)}"
    
    # 测试参数
    params = {
        'callback': callback,
        'sortColumns': 'RATING_DATE',
        'sortTypes': '-1',
        'pageSize': '10',
        'pageNumber': '1',
        'reportName': 'RPT_LICO_FN_CPD',
        'columns': 'ALL',
        'filter': '(SECURITY_CODE="000001")',
        'client': 'WEB'
    }
    
    print(f"请求URL: {base_url}")
    print("请求参数:")
    for k, v in params.items():
        if k != 'callback':
            print(f"  {k}: {v}")
    
    try:
        # 发送请求
        print("\n发送HTTP请求...")
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应大小: {len(response.text)} 字符")
        
        if response.status_code == 200:
            # 显示响应内容前200个字符
            print(f"响应内容前200字符: {response.text[:200]}")
            
            # 尝试解析JSONP
            text = response.text.strip()
            match = re.search(r'\((.*)\);?$', text)
            
            if match:
                json_str = match.group(1)
                try:
                    data = json.loads(json_str)
                    print(f"\n成功解析JSON数据")
                    print(f"success: {data.get('success')}")
                    print(f"message: {data.get('message', 'N/A')}")
                    
                    result = data.get('result', {})
                    if result:
                        data_list = result.get('data', [])
                        print(f"数据条数: {len(data_list)}")
                        
                        if data_list:
                            print("第一条数据的字段:")
                            first_item = data_list[0]
                            for key, value in first_item.items():
                                print(f"  {key}: {value}")
                        else:
                            print("数据列表为空")
                    else:
                        print("result字段为空")
                        
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
                    print(f"JSON字符串前100字符: {json_str[:100]}")
                    
            else:
                print("未找到JSONP格式数据")
                print(f"完整响应: {text}")
        
        else:
            print(f"HTTP请求失败: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            
    except requests.RequestException as e:
        print(f"请求异常: {e}")
    except Exception as e:
        print(f"其他异常: {e}")

def test_alternative_report_names():
    """测试不同的报表名称"""
    print("\n测试不同的报表名称...")
    
    # 不同的报表名称
    report_names = [
        'RPT_LICO_FN_CPD',           # 机构评级
        'RPT_RATING_SURVEY',         # 评级调查
        'RPT_PUBLIC_OP_SURVEY',      # 公开信息调查
        'RPT_CUSTOM_YANBAO_LIST',    # 自定义研报列表
        'RPT_INDUSTRY_SURVEY',       # 行业调查
    ]
    
    base_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    for report_name in report_names:
        print(f"\n尝试报表: {report_name}")
        
        callback = f"jQuery{random.randint(100000000000000000000, 999999999999999999999)}_{int(time.time() * 1000)}"
        
        params = {
            'callback': callback,
            'sortColumns': 'RATING_DATE',
            'sortTypes': '-1',
            'pageSize': '5',
            'pageNumber': '1',
            'reportName': report_name,
            'columns': 'ALL',
            'filter': '(SECURITY_CODE="000001")',
            'client': 'WEB'
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers, timeout=15)
            
            if response.status_code == 200:
                text = response.text.strip()
                match = re.search(r'\((.*)\);?$', text)
                
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    
                    if data.get('success'):
                        result = data.get('result', {})
                        data_list = result.get('data', [])
                        print(f"  ✅ 成功，数据条数: {len(data_list)}")
                        
                        if data_list:
                            # 显示第一条数据的一些字段
                            first_item = data_list[0]
                            print(f"  示例字段: {list(first_item.keys())[:5]}")
                    else:
                        print(f"  ❌ 失败: {data.get('message', '未知错误')}")
                else:
                    print(f"  ❌ 响应格式异常")
            else:
                print(f"  ❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ 异常: {e}")
        
        time.sleep(1)  # 避免请求过快

if __name__ == "__main__":
    print("开始东方财富API调试测试")
    test_direct_api_call()
    test_alternative_report_names()
    print("\n调试测试完成")