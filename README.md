# Mind The Spread

**Mind The Spread** is a comprehensive framework for designing, backtesting, and deploying trading strategies with a focus on **reinforcement learning (RL)**. The framework features a proprietary trading environment that enables smooth transition from backtesting to live trading, making it an all-in-one solution for traders and developers.

---

## Key Features

- **Reinforcement Learning Framework**: Build and test RL-based trading strategies with ease.
- **Proprietary Trading Environment**: A custom environment designed for both backtesting and live trading, ensuring consistency across development stages.
- **Feed Store**: Manage and retrieve various types of financial data, including OHLC, news, and interest rates.
- **Backtesting Capabilities**: Validate strategies with historical data and fine-tune their performance.
- **Pre-built Agents**: Start with parameterized agents or customize your own.
- **Broker Integration**: Interfaces for popular brokers like IG, Alpaca, and Yahoo Finance.
- **Customizable Components**: Extend and adapt the framework for technical analysis, trading signals, and real-time execution.

---

## Installation

To get started, install Mind The Spread directly from the Git repository:

```bash
pip install git+https://github.com/mindthespread/mindthespread
```

## Quickstart
Here's how to quickly set up and test a simple trading strategy using Mind The Spread:
```
from mindthespread.agents.crossover import AgentCrossover
from mindthespread.brokers.yahoo import YahooFinanceBroker
from mindthespread.managers.offline_manager import backtest
from mindthespread.feedstore.engines.pandas import PandasFeedEngine
from mindthespread.feedstore.feeds.ohlc_feed import OHLCFeed

# Define the feed source
base_path = 'feeds/stocks_daily/'
pandas_engine = PandasFeedEngine(base_path=base_path)
feed_broker = YahooFinanceBroker()

# Set up the feed for MSFT
MSFT_feed = OHLCFeed(feed_name="MSFT_1d",
                     feedstore_engine=pandas_engine,
                     feed_broker=feed_broker,
                     feed_format="{symbol}_{freq}")

# Sync data and fetch historical data
MSFT_feed.sync_from_source()
MSFT_feed.fetch_latest(1000)

# Define a crossover agent
agent = AgentCrossover(sma_long=50, sma_short=20)

# Run a backtest
backtest_results = backtest(agent, MSFT_feed.data, pip=1)
```

[//]: # (## Documentation)

[//]: # (Comprehensive documentation is available at Read the Docs.)

## License
This project is licensed under the terms of the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.en.html).

## Roadmap
* Enhanced RL Capabilities: Expand support for multi-agent RL and custom reward functions.
* Signal APIs: Provide trading signals for various markets via APIs.
* Advanced Monitoring: Real-time performance dashboards for strategies in action.
* No-Code Interface: Simplify strategy design with a visual builder.
* Broker Expansion: Add support for more brokers and trading platforms.

## Contributing
We welcome contributions to Mind The Spread! Here's how you can help:

### Fork the repository.
Create a new branch for your feature or bug fix.
Submit a pull request with a clear description of your changes.
License
Mind The Spread is licensed under a proprietary license. Redistribution, modification, and commercial use are restricted. For more details, see the LICENSE file.

### Community and Support
Join our growing community for updates, discussions, and support:
* Website: mindthespread.com
* GitHub Issues: Report bugs or request features here.
Take control of your trading with Mind The Spread – your ultimate reinforcement learning trading framework.






