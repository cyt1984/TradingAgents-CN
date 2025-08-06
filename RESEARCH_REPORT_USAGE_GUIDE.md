# 研报数据源使用指南

## 📊 概述

TradingAgents-CN 现已支持多个研报数据源，提供更全面的券商研报分析。当前可用数据源：

1. **AKShare** ✅ - 免费，已优化，无需配置
2. **同花顺iFinD** ✅ - 免费版可用，需要申请账户  
3. **东方财富** ✅ - 免费HTTP API，无需配置

## 🚀 快速开始

### 方法1：使用默认配置（推荐初学者）
无需任何配置，系统会自动使用AKShare获取研报数据。

```python
from tradingagents.dataflows.research_report_utils import get_stock_research_reports

# 获取股票研报
reports = get_stock_research_reports("000001", limit=10)
print(f"获取到 {len(reports)} 条研报")
```

### 方法2：启用同花顺iFinD（推荐专业用户）
配置后可获得更高质量的研报数据。

## 📋 同花顺iFinD配置指南

### 步骤1：申请免费账户
1. 访问 [同花顺数据接口](http://quantapi.10jqka.com.cn/) 或 [iFinD官网](https://www.51ifind.com/)
2. 点击"申请试用"填写资料
3. 等待1-3天，客服会电话联系
4. 获取用户名和密码

### 步骤2：安装Python SDK
1. 下载SDK安装包（客服会提供链接）
2. 解压并安装：
   ```bash
   # 解压SDK到项目目录
   # 运行安装程序或复制iFinDPy模块
   ```

### 步骤3：配置环境变量
编辑项目根目录的 `.env` 文件（如无则从 `.env.example` 复制）：

```bash
# 启用同花顺iFinD
TONGHUASHUN_API_ENABLED=true
TONGHUASHUN_USERNAME=your_username
TONGHUASHUN_PASSWORD=your_password

# 可选：调整配额限制
TONGHUASHUN_MAX_REQUESTS_MONTH=1000
TONGHUASHUN_MAX_REQUESTS_DAY=100
TONGHUASHUN_REQUEST_INTERVAL=1.0
```

### 步骤4：验证配置
```python
from tradingagents.dataflows.research_report_utils import get_research_report_manager

manager = get_research_report_manager()
# 如果配置正确，应该看到同花顺已启用的日志信息
```

## 📈 使用示例

### 基础使用
```python
from tradingagents.dataflows.research_report_utils import (
    get_stock_research_reports, 
    get_institutional_consensus
)

# 获取研报数据
ticker = "000001"
reports = get_stock_research_reports(ticker, limit=15)

print(f"获取到 {len(reports)} 条研报")
for report in reports[:3]:
    print(f"机构: {report.institution}")
    print(f"标题: {report.title}")
    print(f"评级: {report.rating}")
    print(f"目标价: {report.target_price}")
    print(f"可信度: {report.confidence_level:.2f}")
    print("---")

# 获取机构一致预期
consensus = get_institutional_consensus(ticker)
if consensus:
    print(f"机构数量: {consensus['institution_count']}")
    print(f"平均目标价: {consensus['average_target_price']}")
    print(f"评级分布: {consensus['rating_distribution']}")
```

### 高级使用 - 集成到分析流程
```python
# 在基本面分析师中使用
from tradingagents.agents.analysts.fundamentals_analyst import create_fundamentals_analyst

# 在看涨/看跌研究员中使用
from tradingagents.agents.researchers.bull_researcher import create_bull_researcher
from tradingagents.agents.researchers.bear_researcher import create_bear_researcher

# 研报数据会自动集成到分析流程中
```

## ⚙️ 配置选项说明

### 同花顺iFinD配置
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `TONGHUASHUN_API_ENABLED` | false | 是否启用同花顺接口 |
| `TONGHUASHUN_USERNAME` | "" | 用户名 |
| `TONGHUASHUN_PASSWORD` | "" | 密码 |
| `TONGHUASHUN_MAX_REQUESTS_MONTH` | 1000 | 月度请求限制 |
| `TONGHUASHUN_MAX_REQUESTS_DAY` | 100 | 日度请求限制 |
| `TONGHUASHUN_REQUEST_INTERVAL` | 1.0 | 请求间隔(秒) |

### 配额管理
系统会自动管理API调用配额，包括：
- 月度和日度请求次数限制
- 自动请求间隔控制
- 配额状态持久化存储

查看配额状态：
```python
from tradingagents.utils.quota_manager import QuotaManager
from tradingagents.config.tonghuashun_config import tonghuashun_config

quota_manager = QuotaManager('tonghuashun', tonghuashun_config.get_quota_config())
status = quota_manager.get_quota_status()
print(f"月度已用: {status['monthly']['used']}/{status['monthly']['limit']}")
print(f"日度已用: {status['daily']['used']}/{status['daily']['limit']}")
```

## 🔧 故障排除

### 常见问题

**1. 同花顺iFinD导入失败**
```
ImportError: No module named 'iFinDPy'
```
**解决方案**：
- 确认已下载并安装同花顺Python SDK
- 检查SDK是否在Python路径中

**2. 登录失败**
```
同花顺iFinD登录失败: 用户名或密码错误
```
**解决方案**：
- 检查`.env`文件中的用户名和密码
- 确认账户状态正常（联系同花顺客服）

**3. 配额超限**
```
同花顺配额不足，跳过该数据源
```
**解决方案**：
- 等待配额重置（每日/每月）
- 调整`REQUEST_INTERVAL`增加间隔
- 升级到付费版本

**4. 数据获取失败**
```
AKShare数据验证失败: infoCode错误
```
**解决方案**：
- 这是正常情况，特别是科创板等特殊板块
- 系统会自动跳过无效数据
- 不影响其他数据源的使用

### 日志调试

启用详细日志：
```python
import logging
logging.getLogger('agents').setLevel(logging.DEBUG)
logging.getLogger('quota_manager').setLevel(logging.DEBUG)
```

查看详细的API调用和数据处理过程。

## 📊 数据质量说明

### AKShare数据源
- **优点**：免费、无需配置、覆盖面广
- **限制**：部分股票可能无研报数据、数据更新频率有限
- **适用**：入门用户、快速测试

### 同花顺iFinD数据源  
- **优点**：专业级数据、更新及时、字段丰富
- **限制**：需要申请账户、有配额限制
- **适用**：专业用户、生产环境

### 东方财富数据源
- **优点**：免费HTTP API、无需配置、机构评级数据
- **限制**：主要提供评级变化数据、覆盖面有限
- **适用**：补充数据源、机构评级分析

### 数据融合策略
系统会自动：
1. 从多个数据源获取研报
2. 去重和数据清洗
3. 按发布时间排序
4. 计算综合可信度评分

## 🔄 升级和维护

### 检查更新
定期查看 `RESEARCH_REPORT_ENHANCEMENT_PLAN.md` 了解最新功能。

### 数据缓存清理
```python
# 清理配额记录文件
import os
for file in ['quota_tonghuashun.json']:
    if os.path.exists(file):
        os.remove(file)
```

### 性能优化建议
1. 合理设置请求间隔，避免频繁调用
2. 使用适当的limit参数，避免获取过多数据
3. 定期清理缓存文件
4. 监控配额使用情况

## 📞 技术支持

如遇到问题：
1. 查看日志输出中的详细错误信息
2. 检查配置文件是否正确
3. 参考 `RESEARCH_REPORT_ENHANCEMENT_PLAN.md` 开发文档
4. 提交Issue到项目仓库

---

**更新时间**: 2025-08-05  
**版本**: v1.1.0  
**支持的数据源**: AKShare ✅, 同花顺iFinD ✅, 东方财富 ✅