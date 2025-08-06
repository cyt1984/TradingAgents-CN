# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

TradingAgents-CN is a Chinese-enhanced multi-agent trading system based on LangGraph. It provides intelligent stock analysis for A-shares, Hong Kong stocks, and US stocks using various LLM providers.

## Core Architecture

### Multi-Agent System
- **Analysts**: Market analyst, fundamentals analyst, news analyst, social media analyst, heat analyst
- **Researchers**: Bull researcher, bear researcher (structured debate mechanism)
- **Trader**: Final decision maker based on all analysis inputs
- **Risk Management**: Multi-layer risk assessment agents
- **Managers**: Research manager, risk manager for coordination

#### Heat Analyst Enhancement
The system now includes a dedicated heat analyst that provides:
- Multi-dimensional heat analysis (social media, volume anomaly, sentiment)
- Real-time heat alerts and risk warnings
- Free data source integration (Weibo, Xueqiu, EastMoney)
- Batch analysis and heat ranking functionality

### LangGraph Workflow
The system uses LangGraph to orchestrate agent interactions in `tradingagents/graph/trading_graph.py`. The main workflow includes:
1. Data collection from multiple sources
2. Parallel analysis by specialist agents  
3. Structured debate between bull/bear researchers
4. Risk assessment and management
5. Final trading decision by trader agent

### Data Sources
- **A-shares**: Tushare, AkShare, TongDaXin API
- **Hong Kong stocks**: AkShare, Yahoo Finance
- **US stocks**: FinnHub, Yahoo Finance
- **News**: Google News, enhanced news filtering system
- **Heat Analysis**: Weibo, Xueqiu, EastMoney, Baidu Index (free APIs)
- **Caching**: Multi-layer caching with Redis and MongoDB

## Development Commands

### Installation and Setup
```bash
# Install dependencies (use pyproject.toml)
pip install -e .

# Alternative for development
pip install -r requirements.txt  # Note: requirements.txt is deprecated
```

### Running the Application

#### Web Interface (Primary)
```bash
# Start web application
python start_web.py

# Alternative method
python web/run_web.py

# Direct streamlit
streamlit run web/app.py
```

#### CLI Interface
```bash
# Interactive CLI
python -m cli.main

# Direct analysis example
python main.py

# Heat analysis CLI
python heat_cli.py 000001                    # Single stock analysis
python heat_cli.py -b 000001,600519        # Batch analysis
python heat_cli.py -w 000001,600519 -m 60  # Monitor with threshold
```

#### Docker Deployment
```bash
# Smart start (auto-detects if rebuild needed)
./scripts/smart_start.sh    # Linux/Mac
./scripts/smart_start.ps1   # Windows

# Manual Docker commands
docker-compose up -d --build  # First time or after code changes
docker-compose up -d          # Subsequent runs
```

### Testing

There is no unified test runner. Tests are located in the `tests/` directory with individual test files:

```bash
# Run specific test files
python tests/test_analysis.py
python tests/test_config_management.py
python tests/quick_test.py

# Integration tests
python tests/integration/test_dashscope_integration.py
```

### Data Management

#### Cache Management
```bash
# Check system status
python scripts/validation/check_system_status.py

# Clean cache
python scripts/maintenance/cleanup_cache.py --days 7

# Initialize database
python scripts/setup/init_database.py
```

#### Configuration
```bash
# Check API configuration
python scripts/check_api_config.py

# Data directory configuration
python -m cli.main data-config --show
python -m cli.main data-config --set /path/to/data
```

### Development Scripts

#### Docker Operations
```bash
# Build Docker with PDF support
python scripts/build_docker_with_pdf.py

# Start Docker services
./scripts/docker/start_docker_services.sh
./scripts/docker/start_docker_services.bat  # Windows

# Get container logs
python scripts/get_container_logs.py
```

#### Debugging and Logs
```bash
# View logs
python scripts/view_logs.py

# Quick log access
./scripts/quick_get_logs.sh

# Test logging
python scripts/simple_log_test.py
```

#### Setup and Installation
```bash
# Quick installation
python scripts/setup/quick_install.py

# Initialize system
python scripts/setup/initialize_system.py

# Setup databases
python scripts/setup/setup_databases.py
```

## Configuration Management

### Environment Configuration
The system uses `.env` files for configuration. Key variables:
- LLM API keys (DASHSCOPE_API_KEY, DEEPSEEK_API_KEY, GOOGLE_API_KEY, etc.)
- Database configuration (MONGODB_HOST, REDIS_HOST)  
- Data source APIs (TUSHARE_TOKEN, FINNHUB_API_KEY)

### Model Configuration
LLM models are configured in `tradingagents/default_config.py`. The system supports:
- DashScope (Alibaba Qwen models)
- DeepSeek V3
- Google AI (Gemini models)
- OpenRouter (60+ models)
- OpenAI GPT models

### Multi-Environment Support
- **Docker**: Uses service names (mongodb, redis) for database hosts
- **Local**: Uses localhost for database connections
- **Development**: Code mapping for live development in Docker

## Key Files and Directories

### Core Application
- `main.py` - Main entry point for direct usage
- `start_web.py` - Web application launcher
- `tradingagents/graph/trading_graph.py` - Core orchestration logic
- `tradingagents/default_config.py` - Default configuration

### Heat Analysis
- `tradingagents/analytics/heat_analyzer.py` - Core heat analysis engine
- `tradingagents/agents/analysts/heat_analyst.py` - Heat analyst agent
- `heat_cli.py` - Command-line interface for heat analysis
- `tradingagents/analytics/integration.py` - Integration with main system

### Web Interface
- `web/app.py` - Streamlit web application
- `web/components/` - UI components
- `web/utils/` - Web utilities and helpers

### Data Processing
- `tradingagents/dataflows/` - Data source adapters and utilities
- `tradingagents/agents/` - Individual agent implementations
- `tradingagents/llm_adapters/` - LLM provider adapters

### Configuration
- `config/` - Configuration files and database settings
- `.env` - Environment variables (not in repo)
- `pyproject.toml` - Python package configuration

## Development Notes

### Testing Strategy
- Individual test files for specific components
- Integration tests for full workflows
- No pytest or unified test runner configured
- Tests use real API calls in most cases

### Logging System
- Unified logging via `tradingagents.utils.logging_manager`
- Separate user interface and technical logs
- Configurable log levels and output destinations
- Docker-specific logging configuration

### Multi-Language Support
- Primary language: Chinese (Simplified)
- English documentation and code comments
- Chinese UI and analysis outputs
- Localized error messages and user feedback

### Performance Considerations
- Multi-layer caching (Redis, MongoDB, file system)
- Intelligent data source fallback mechanisms  
- Async progress tracking for long-running analyses
- Smart Docker image rebuilding to save time

## Heat Analysis Usage Examples

### Python API
```python
# Basic heat analysis
from tradingagents.analytics import HeatAnalyzer
analyzer = HeatAnalyzer()
result = analyzer.analyze_heat('000001')
print(f"Heat Score: {result['heat_score']}")

# Batch analysis
symbols = ['000001', '600519', '000858']
ranking = analyzer.get_heat_ranking(symbols)
for stock in ranking:
    print(f"{stock['symbol']}: {stock['heat_score']}")

# Integration with main system
from tradingagents.analytics.integration import HeatAnalysisIntegration
integration = HeatAnalysisIntegration()
combined_analysis = integration.analyze_with_heat('000001')
```

### Heat Analyst Agent
```python
from tradingagents.agents.analysts.heat_analyst import HeatAnalystAgent
agent = HeatAnalystAgent()

# Single stock analysis
analysis = agent.analyze_symbol('000001')
print(f"Recommendation: {analysis['trading_recommendation']['action']}")

# Batch analysis
batch_result = agent.batch_analyze(['000001', '600519'])
print(f"Market status: {batch_result['market_heat_summary']['market_heat_status']}")
```

This is a mature, production-ready system with extensive Chinese localization and multiple deployment options.