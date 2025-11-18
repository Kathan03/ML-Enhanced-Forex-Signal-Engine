# ML-Enhanced Forex Signal Engine

A Python-based machine learning system that generates Expert Advisor (EA) style forex trading signals with backtesting capabilities.

## 🎯 Project Overview

This project demonstrates the core "brain" of an Expert Advisor (EA) for forex trading, built entirely in Python without platform-specific dependencies. It showcases:

- **Machine Learning Integration**: Multiple ML models (Logistic Regression, Random Forest, LSTM, KAN)
- **API/Data Integration**: Real-time forex data fetching from multiple providers
- **Feature Engineering**: Technical indicators and price-based features
- **Signal Generation**: EA-style BUY/SELL/FLAT signals with stop-loss and take-profit levels
- **Backtesting**: Comprehensive performance evaluation with standard trading metrics

## 🏗️ Architecture

```
┌─────────────────┐
│   Data API      │  Fetch OHLCV data from API/CSV
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Feature Engineer│  Create ML features (returns, SMA, RSI, ATR)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Model       │  Train/Predict (LR, RF, LSTM, KAN)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Signal Engine   │  Generate BUY/SELL/FLAT with SL/TP
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Backtester     │  Simulate trades & calculate metrics
└─────────────────┘
```

### Directory Structure

```
ML-Enhanced-Forex-Signal-Engine/
├── config.yaml              # Main configuration file
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
│
├── data_api/               # Data fetching & storage
│   ├── data_fetcher.py     # API integration (Twelve Data, Alpha Vantage)
│   └── data_store.py       # Local data caching
│
├── features/               # Feature engineering
│   └── feature_engineering.py  # Technical indicators & features
│
├── model/                  # ML models
│   ├── train_model.py      # Model training
│   └── predict.py          # Inference
│
├── signals/                # Signal generation
│   └── signal_engine.py    # EA-style signals with SL/TP
│
├── backtest/               # Backtesting
│   └── backtester.py       # Trade simulation & metrics
│
├── utils/                  # Utilities
│   ├── config.py           # Configuration loader
│   └── metrics.py          # Performance metrics
│
├── scripts/                # CLI entry points
│   ├── run_train.py        # Train models
│   ├── run_backtest.py     # Run backtests
│   └── run_live_sim.py     # Live simulation
│
├── data/                   # Data storage
├── models/                 # Saved models
├── outputs/                # Signals & reports
└── logs/                   # Log files
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/Kathan03/ML-Enhanced-Forex-Signal-Engine.git
cd ML-Enhanced-Forex-Signal-Engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

### 2. Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env and add your API key
# FOREX_API_KEY=your_api_key_here

# Edit config.yaml to customize settings
# - Symbol (default: EURUSD)
# - Timeframe (default: 1h)
# - Model type
# - Signal thresholds
# - Backtest parameters
```

### 3. Run the Pipeline

#### Step 1: Train a Model

```bash
python scripts/run_train.py --config config.yaml
```

This will:
- Fetch historical EURUSD data
- Engineer features (returns, SMA, RSI, ATR)
- Train a logistic regression model
- Save the model to `models/model.joblib`
- Print training metrics

#### Step 2: Run Backtest

```bash
python scripts/run_backtest.py --config config.yaml --plot
```

This will:
- Load the trained model
- Generate signals on test data
- Simulate trades
- Calculate performance metrics
- Plot equity curve and drawdown

#### Step 3: (Optional) Live Simulation

```bash
python scripts/run_live_sim.py --config config.yaml
```

This simulates real-time signal generation by fetching recent data and generating signals.

## 📊 Features

### Data Ingestion
- **API Support**: Twelve Data, Alpha Vantage
- **CSV Support**: Load historical data from files
- **Normalization**: Standard OHLCV schema
- **Caching**: Local data storage

### Feature Engineering
- **Returns**: Simple and log returns with lags (1, 3, 5 bars)
- **Rolling Statistics**: Mean and standard deviation
- **Technical Indicators**:
  - Simple Moving Averages (SMA 10, 20, 50)
  - Relative Strength Index (RSI)
  - Average True Range (ATR)
- **Target**: Binary classification (price up/down next bar)

### ML Models
- **Logistic Regression**: Fast baseline
- **Random Forest**: Non-linear patterns
- **LSTM**: Sequential patterns (optional)
- **KAN**: Kolmogorov-Arnold Networks (optional)

### Signal Generation
- **Signal Types**: BUY, SELL, FLAT
- **Thresholds**: Configurable probability cutoffs
- **Risk Management**:
  - Stop Loss: Entry ± (ATR × multiplier)
  - Take Profit: Entry ± (ATR × multiplier)
- **Confidence**: Model probability
- **Output Formats**: JSON, CSV

### Backtesting
- **Execution Model**: Enter at next open, exit at SL/TP
- **Metrics**:
  - Total PnL
  - Win Rate
  - Profit Factor
  - Max Drawdown
  - Sharpe Ratio
  - Average Win/Loss
- **Visualization**: Equity curve, drawdown chart
- **Trade History**: Detailed trade log

## 📈 Example Output

### Signal Format (JSON)

```json
{
  "timestamp": "2024-01-15 10:00:00",
  "symbol": "EURUSD",
  "signal": "BUY",
  "entry_price": 1.0850,
  "stop_loss": 1.0830,
  "take_profit": 1.0890,
  "confidence": 0.74
}
```

### Backtest Metrics

```
=== Backtest Results ===
Initial Capital: $10,000.00
Final Capital:   $12,450.00
Total PnL:       $2,450.00 (+24.5%)

Trades:          147
Wins:            89 (60.5%)
Losses:          58 (39.5%)

Avg Win:         $65.20
Avg Loss:        -$42.30
Profit Factor:   1.85

Max Drawdown:    -$850.00 (-7.3%)
Sharpe Ratio:    1.42
```

## 🎓 How This Maps to Expert Advisor (EA) Development

This project demonstrates key EA concepts:

### 1. **Signal Generation Logic**
- EAs use technical indicators and price action to generate signals
- This project uses ML predictions + thresholds instead of hard-coded rules
- Output format matches EA signal structure

### 2. **Risk Management**
- EAs calculate SL/TP based on volatility (ATR)
- Same approach used here with configurable multipliers

### 3. **Backtesting**
- Critical for EA validation before live trading
- This backtester simulates realistic execution (slippage, commission)

### 4. **Configuration**
- EAs use input parameters for customization
- `config.yaml` serves same purpose

### 5. **Real-time Operation**
- EAs monitor markets and generate signals continuously
- `run_live_sim.py` demonstrates this pattern

## 🔮 Future Enhancements (v2)

- **Multiple Symbols**: Trade multiple forex pairs
- **Multiple Timeframes**: Multi-timeframe analysis
- **Advanced Models**: Transformers, reinforcement learning
- **Walk-Forward Optimization**: Robust parameter tuning
- **Broker Integration**: MetaTrader 4/5 bridge
- **Risk Management Module**: Position sizing, portfolio constraints
- **Real-time Dashboard**: Web UI for monitoring
- **Alert System**: Email/SMS notifications

## 📚 Key Concepts for Interviews

### Architecture
- **Modular Design**: Each component (data, features, model, signals, backtest) is independent
- **Pipeline Pattern**: Data flows through clear stages
- **Configuration-Driven**: Easy to modify behavior without code changes

### Machine Learning
- **Feature Engineering**: Transform raw prices into predictive signals
- **Time-Series Split**: Proper train/test split respecting temporal order
- **Model Selection**: Start simple (LR), add complexity (RF, LSTM) as needed
- **Probability Calibration**: Use probabilities for confidence-based filtering

### Trading
- **Signal Generation**: Convert predictions to actionable trades
- **Risk Management**: ATR-based stops protect against volatility
- **Backtesting**: Validate strategy before deployment
- **Performance Metrics**: Standard quantitative finance measures

### Software Engineering
- **Clean Code**: Well-documented, readable
- **Testing**: Backtesting serves as validation
- **CLI Interface**: Production-ready entry points
- **Extensibility**: Easy to add new models, indicators, or data sources

## 📝 Configuration Reference

See `config.yaml` for all available options:

- **data**: Symbol, timeframe, API settings
- **features**: Indicators and windows
- **model**: Model type and hyperparameters
- **signals**: Thresholds and risk management
- **backtest**: Capital, commission, execution rules
- **dates**: Train/test date ranges

## 🤝 Contributing

Contributions are welcome! This is a learning/portfolio project, so feel free to:
- Add new ML models
- Implement additional indicators
- Enhance the backtester
- Improve documentation

## 📄 License

MIT License - Feel free to use for learning and portfolio projects.

## 🙏 Acknowledgments

- Inspired by MQL5 Expert Advisors
- Built for demonstrating ML + trading integration
- Designed as a portfolio/interview project

---

**Note**: This is a prototype for educational and portfolio purposes. Not intended for live trading without significant additional development and testing.
