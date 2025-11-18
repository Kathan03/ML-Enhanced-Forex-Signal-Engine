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

#### Step 2.1: Set Up Environment Variables

Create or edit the `.env` file in the project root:

```bash
# .env file

# For yfinance (FREE - no API key required!)
# Leave empty if using yfinance
FOREX_API_KEY=

# For Twelve Data (FREE tier available)
TWELVE_DATA_API_KEY=your_twelve_data_key_here

# For Alpha Vantage (optional)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

**Default Configuration**: The project is pre-configured to use **yfinance** (completely free, no signup required).

#### Step 2.2: Configure Data Provider

Edit `config.yaml` to select your data provider:

**Option A: yfinance (Default - FREE)**
```yaml
data:
  api_provider: "yfinance"
  symbol: "EURUSD=X"  # yfinance format: pair + "=X"
  timeframe: "1h"
  data_path: "data/raw"
```

**Option B: Twelve Data**
```yaml
data:
  api_provider: "twelve_data"
  symbol: "EUR/USD"  # Twelve Data format: "PAIR1/PAIR2"
  timeframe: "1h"
  data_path: "data/raw"
```

**Option C: Alpha Vantage**
```yaml
data:
  api_provider: "alpha_vantage"
  symbol: "EURUSD"  # Alpha Vantage format: no separator
  timeframe: "60min"
  data_path: "data/raw"
```

#### Step 2.3: Configure Model Type

Choose your ML model in `config.yaml`:

**Option A: Logistic Regression (Fast, good baseline)**
```yaml
model:
  type: "logistic_regression"
  train_ratio: 0.8
  model_path: "models"
  params:
    C: 1.0
    max_iter: 1000
```

**Option B: Random Forest (Better for non-linear patterns)**
```yaml
model:
  type: "random_forest"
  train_ratio: 0.8
  model_path: "models"
  params:
    n_estimators: 100
    max_depth: 10
    min_samples_split: 5
    min_samples_leaf: 2
```

**Option C: LSTM (Best for sequential patterns)**
```yaml
model:
  type: "lstm"
  train_ratio: 0.8
  model_path: "models"
  params:
    lstm_units: 64
    dropout_rate: 0.2
    epochs: 50
    batch_size: 32
    sequence_length: 20
```

#### Step 2.4: Configure Signal Generation

Adjust trading signal parameters:

```yaml
signals:
  thresholds:
    buy_probability: 0.6   # BUY if model confidence > 60%
    sell_probability: 0.4  # SELL if model confidence < 40%

  risk_management:
    stop_loss_atr_multiplier: 2.0   # SL = Entry ± (2 × ATR)
    take_profit_atr_multiplier: 3.0 # TP = Entry ± (3 × ATR)

  output_path: "outputs"
```

#### Step 2.5: Configure Backtesting

Set backtest parameters:

```yaml
backtest:
  initial_capital: 10000.0  # Starting capital in USD
  position_size: 1.0        # Position size in lots (0.1 = micro)
  commission: 0.0002        # 0.02% per trade
  slippage: 0.0001          # 1 pip slippage
  plot_equity_curve: true
```

### 3. Run the Pipeline

#### Step 3.1: Train a Model

**Basic Usage (with default config.yaml):**
```bash
python scripts/run_train.py --config config.yaml
```

**With Custom Parameters:**
```bash
# Specify date range
python scripts/run_train.py \
  --config config.yaml \
  --start-date 2023-01-01 \
  --end-date 2024-01-01

# Use specific data file (CSV)
python scripts/run_train.py \
  --config config.yaml \
  --data data/raw/my_custom_data.csv
```

**What happens during training:**
1. ✓ Loads configuration from `config.yaml`
2. ✓ Fetches historical data (or loads from cache)
3. ✓ Engineers 16 features (returns, SMA, RSI, ATR, etc.)
4. ✓ Splits data temporally (80% train, 20% validation)
5. ✓ Trains the selected model (LR/RF/LSTM)
6. ✓ Evaluates on validation set
7. ✓ Saves model to `models/model.joblib` (or `.h5` for LSTM)
8. ✓ Prints metrics (accuracy, precision, recall, F1)

**Expected Output:**
```
======================================================================
 ML-Enhanced Forex Signal Engine - Model Training
======================================================================

[1/6] Loading configuration...
  Config file: config.yaml

[2/6] Loading data...
  Fetching from API: yfinance
  Symbol: EURUSD=X, Bars: 1000
  Loaded 1000 bars
  Date range: 2023-01-01 to 2024-01-01

[3/6] Engineering features...
  Created 16 features
  Features: ['return', 'log_return', 'return_lag_1', 'return_lag_3', ...]

[4/6] Preparing data...
  Train samples: 800
  Validation samples: 200

[5/6] Training model: logistic_regression
  Training...
  Training complete in 0.5s

[6/6] Evaluating model...

  Validation Metrics:
    Accuracy:  0.9375
    Precision: 0.9500
    Recall:    0.9250
    F1 Score:  0.9374

Model saved to: models/model.joblib

✓ Training complete!
```

#### Step 3.2: Generate Signals

**Basic Usage:**
```bash
python scripts/run_signals.py --config config.yaml
```

**With Options:**
```bash
# Use specific model
python scripts/run_signals.py \
  --config config.yaml \
  --model models/my_custom_model.joblib

# Filter signals (exclude FLAT)
python scripts/run_signals.py \
  --config config.yaml \
  --filter-signals

# Specify output format
python scripts/run_signals.py \
  --config config.yaml \
  --format json  # Options: json, csv, both
```

**What happens during signal generation:**
1. ✓ Loads trained model
2. ✓ Fetches recent data
3. ✓ Engineers features
4. ✓ Makes predictions
5. ✓ Generates BUY/SELL/FLAT signals
6. ✓ Calculates SL/TP levels (ATR-based)
7. ✓ Exports signals to `outputs/signals.json` and/or `.csv`

**Output Files:**
- `outputs/signals.json` - JSON format for API integration
- `outputs/signals.csv` - CSV format for analysis

#### Step 3.3: Run Backtest

**Basic Usage:**
```bash
python scripts/run_backtest.py --config config.yaml
```

**With Options:**
```bash
# Show plots interactively
python scripts/run_backtest.py \
  --config config.yaml \
  --plot

# Use specific model and data
python scripts/run_backtest.py \
  --config config.yaml \
  --model models/random_forest_model.joblib \
  --data data/raw/test_data.csv

# Save trade history
python scripts/run_backtest.py \
  --config config.yaml \
  --save-trades
```

**What happens during backtesting:**
1. ✓ Loads trained model
2. ✓ Loads historical data (test period)
3. ✓ Generates signals
4. ✓ Simulates trades bar-by-bar
5. ✓ Tracks SL/TP hits
6. ✓ Calculates 15+ performance metrics
7. ✓ Generates equity curve and drawdown plots
8. ✓ Exports trade history (if requested)

**Expected Output:**
```
======================================================================
 ML-Enhanced Forex Signal Engine - Backtesting
======================================================================

[1/8] Loading configuration...
[2/8] Loading trained model...
[3/8] Loading historical data...
  Loaded 500 bars
  Date range: 2024-01-01 to 2024-06-01

[4/8] Engineering features...
[5/8] Making predictions...
[6/8] Generating trading signals...
  Total signals: 500
  BUY: 120, SELL: 115, FLAT: 265

[7/8] Running backtest...
  Equity curve points: 500
  Trades executed: 47

[8/8] Calculating performance metrics...

======================================================================
                      BACKTEST RESULTS
======================================================================

Capital:
  Initial Capital:    $10,000.00
  Final Capital:      $10,734.50
  Total P&L:          $734.50
  Total Return:       +7.35%

Trades:
  Total Trades:       47
  Winning Trades:     34 (72.34%)
  Losing Trades:      13 (27.66%)

Performance:
  Profit Factor:      2.85
  Sharpe Ratio:       1.42
  Max Drawdown:       -$185.30 (-1.85%)

  Average Win:        $45.60
  Average Loss:       -$28.30
  Avg Win/Loss Ratio: 1.61

======================================================================

Results saved to: outputs/

Files created:
  - outputs/backtest_results.png (equity curve and drawdown chart)
  - outputs/trade_history.csv (detailed trade log)
```

#### Step 3.4: Run Complete Workflow

**All-in-one command to train, generate signals, and backtest:**

```bash
# Train model
python scripts/run_train.py --config config.yaml

# Run backtest with plots
python scripts/run_backtest.py --config config.yaml --plot --save-trades
```

#### Step 3.5: Test Phase by Phase

The project includes comprehensive test scripts for each phase:

```bash
# Test Phase 1: Data Ingestion
python test_phase1_csv.py

# Test Phase 2: Feature Engineering & Model Training
python test_phase2.py

# Test Phase 3: Signal Generation
python test_phase3.py

# Test Phase 4: Backtesting
python test_phase4.py
```

Each test script validates the implementation and shows expected behavior.

## 🔄 Switching API Providers

### From yfinance to Twelve Data

The project is designed to work with multiple data providers. **No code changes are required** - just update configuration files.

#### Step 1: Get Twelve Data API Key

1. Visit [https://twelvedata.com](https://twelvedata.com)
2. Sign up for a free account
3. Copy your API key from the dashboard
4. Free tier includes: 800 API calls/day, real-time data, 8+ years of history

#### Step 2: Update `.env` File

```bash
# .env file
TWELVE_DATA_API_KEY=your_actual_api_key_here
```

#### Step 3: Update `config.yaml`

Change two fields in the `data` section:

```yaml
data:
  # OLD (yfinance)
  # api_provider: "yfinance"
  # symbol: "EURUSD=X"

  # NEW (Twelve Data)
  api_provider: "twelve_data"
  symbol: "EUR/USD"  # Note: Different format! Use slash instead of "=X"

  timeframe: "1h"      # No change needed
  data_path: "data/raw"  # No change needed
```

**Important Symbol Format Differences:**
| Provider | Format | Example |
|----------|--------|---------|
| yfinance | `PAIR1PAIR2=X` | `EURUSD=X` |
| Twelve Data | `PAIR1/PAIR2` | `EUR/USD` |
| Alpha Vantage | `PAIR1PAIR2` | `EURUSD` |

#### Step 4: Test the Change

```bash
# Test data fetching
python -c "
from data_api.data_fetcher import DataFetcher
fetcher = DataFetcher(api_provider='twelve_data', symbol='EUR/USD')
df = fetcher.fetch_historical_data(bars=10)
print(f'Fetched {len(df)} bars')
print(df.head())
"
```

#### Step 5: Run Training Pipeline

```bash
# Train with new data source
python scripts/run_train.py --config config.yaml
```

That's it! The entire pipeline will now use Twelve Data instead of yfinance.

### From yfinance to Alpha Vantage

Same process, different configuration:

**`.env` file:**
```bash
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
```

**`config.yaml` file:**
```yaml
data:
  api_provider: "alpha_vantage"
  symbol: "EURUSD"  # No separator
  timeframe: "60min"  # Alpha Vantage uses different format
```

### Comparison of API Providers

| Feature | yfinance | Twelve Data | Alpha Vantage |
|---------|----------|-------------|---------------|
| **Cost** | 100% Free | Free tier: 800 calls/day | Free tier: 500 calls/day |
| **API Key Required** | No | Yes | Yes |
| **Real-time Data** | 15-min delayed | Yes (free tier) | Yes (free tier) |
| **Historical Data** | Limited | 8+ years | 20+ years |
| **Rate Limits** | Moderate | 8 calls/min (free) | 5 calls/min (free) |
| **Reliability** | Good | Excellent | Good |
| **Best For** | Quick testing | Production use | Long backtests |

**Recommendation**: Start with **yfinance** for development, switch to **Twelve Data** for production.

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### Issue 1: `ModuleNotFoundError: No module named 'pandas'`

**Solution:**
```bash
pip install -r requirements.txt
# or
pip install pandas numpy scikit-learn matplotlib pyyaml python-dotenv requests joblib
```

#### Issue 2: yfinance Installation Fails

**Solution 1 (Use CSV mode):**
```bash
# Create sample data and use CSV mode
python test_phase1_csv.py
```

**Solution 2 (Switch to Twelve Data):**
Follow the "Switching API Providers" section above.

#### Issue 3: API Rate Limit Exceeded

**Error Message:** `429 Too Many Requests`

**Solution:**
- **yfinance**: Wait a few minutes between requests
- **Twelve Data**: Free tier allows 8 API calls/minute
- **Alpha Vantage**: Free tier allows 5 API calls/minute

**Workaround**: Use data caching
```python
# Data is automatically cached in data/raw/
# Subsequent calls load from cache instead of API
store = DataStore(data_path="data/raw")
df = store.load_data()  # Loads from cache if available
```

#### Issue 4: Model Training Fails with "Only One Class in Data"

**Error Message:** `ValueError: This solver needs samples of at least 2 classes`

**Cause:** Dataset too small or not enough price variation

**Solution:**
```bash
# Use larger dataset (500+ bars recommended)
python scripts/run_train.py --config config.yaml --bars 1000
```

#### Issue 5: LSTM Model Not Training

**Error Message:** `ModuleNotFoundError: No module named 'tensorflow'`

**Solution:**
```bash
# Install TensorFlow (required for LSTM)
pip install tensorflow
# or for CPU-only (smaller, faster install)
pip install tensorflow-cpu
```

#### Issue 6: Backtest Shows Zero Trades

**Cause:** Signal thresholds too strict or bad model predictions

**Solution 1 (Lower thresholds):**
```yaml
signals:
  thresholds:
    buy_probability: 0.55  # Lower from 0.6
    sell_probability: 0.45  # Raise from 0.4
```

**Solution 2 (Check model performance):**
```bash
# Retrain with more data
python scripts/run_train.py --config config.yaml --bars 2000
```

#### Issue 7: Plots Not Showing

**Error:** `No module named 'matplotlib'` or plots not displaying

**Solution:**
```bash
# Install matplotlib
pip install matplotlib

# For headless servers, plots are saved to outputs/ instead
python scripts/run_backtest.py --config config.yaml
# Check: outputs/backtest_results.png
```

#### Issue 8: Permission Denied When Saving Files

**Solution:**
```bash
# Create required directories
mkdir -p data/raw models outputs logs

# Check permissions
chmod -R 755 data/ models/ outputs/ logs/
```

### Getting Help

- **Check logs**: Error details are in `logs/` directory
- **Review PROJECT_STRUCTURE.md**: Comprehensive documentation of all files
- **Run tests**: Each phase has a test script (test_phase1.py through test_phase4.py)
- **Verify config**: Ensure `config.yaml` has correct paths and parameters

## 📖 Quick Reference Guide

### Common Workflows

#### Workflow 1: Train and Test Different Models

```bash
# 1. Train Logistic Regression
# Edit config.yaml: model.type = "logistic_regression"
python scripts/run_train.py --config config.yaml
python scripts/run_backtest.py --config config.yaml --save-trades
mv outputs/trade_history.csv outputs/lr_trades.csv

# 2. Train Random Forest
# Edit config.yaml: model.type = "random_forest"
python scripts/run_train.py --config config.yaml
python scripts/run_backtest.py --config config.yaml --save-trades
mv outputs/trade_history.csv outputs/rf_trades.csv

# 3. Train LSTM (requires tensorflow)
# Edit config.yaml: model.type = "lstm"
pip install tensorflow
python scripts/run_train.py --config config.yaml
python scripts/run_backtest.py --config config.yaml --save-trades
mv outputs/trade_history.csv outputs/lstm_trades.csv

# 4. Compare results
python -c "
import pandas as pd
lr = pd.read_csv('outputs/lr_trades.csv')
rf = pd.read_csv('outputs/rf_trades.csv')
lstm = pd.read_csv('outputs/lstm_trades.csv')

print('Model Comparison:')
print(f'LR Win Rate: {(lr[\"pnl\"] > 0).mean():.2%}')
print(f'RF Win Rate: {(rf[\"pnl\"] > 0).mean():.2%}')
print(f'LSTM Win Rate: {(lstm[\"pnl\"] > 0).mean():.2%}')
"
```

#### Workflow 2: Parameter Optimization

```bash
# Test different signal thresholds
for threshold in 0.55 0.60 0.65 0.70; do
  # Update config.yaml programmatically
  python -c "
import yaml
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)
config['signals']['thresholds']['buy_probability'] = $threshold
config['signals']['thresholds']['sell_probability'] = 1 - $threshold
with open('config.yaml', 'w') as f:
    yaml.dump(config, f)
"

  # Run backtest
  echo "Testing threshold: $threshold"
  python scripts/run_backtest.py --config config.yaml
done
```

#### Workflow 3: Train on Historical Data, Test on Recent Data

```bash
# 1. Train on older data
python scripts/run_train.py \
  --config config.yaml \
  --start-date 2023-01-01 \
  --end-date 2023-12-31

# 2. Backtest on recent data
python scripts/run_backtest.py \
  --config config.yaml \
  --data data/raw/2024_test_data.csv \
  --plot \
  --save-trades

# This simulates walk-forward testing
```

#### Workflow 4: Export Signals for External Use

```bash
# Generate signals and export to JSON (for API integration)
python scripts/run_signals.py \
  --config config.yaml \
  --format json \
  --filter-signals

# Output: outputs/signals.json
# Can be consumed by:
# - MetaTrader EA via REST API
# - Web dashboard
# - Trading bot
# - Alert system
```

### File Modification Cheat Sheet

| Task | File to Edit | What to Change |
|------|--------------|----------------|
| Switch API provider | `.env` + `config.yaml` | Update `api_provider` and add API key |
| Change forex pair | `config.yaml` | Update `data.symbol` |
| Change model type | `config.yaml` | Update `model.type` |
| Adjust signal thresholds | `config.yaml` | Update `signals.thresholds.buy_probability` |
| Change SL/TP multipliers | `config.yaml` | Update `signals.risk_management.*_multiplier` |
| Adjust position size | `config.yaml` | Update `backtest.position_size` |
| Change training split | `config.yaml` | Update `model.train_ratio` |

### Configuration Templates

#### Conservative Trading (Lower Risk)
```yaml
signals:
  thresholds:
    buy_probability: 0.70   # High confidence only
    sell_probability: 0.30
  risk_management:
    stop_loss_atr_multiplier: 1.5   # Tighter stops
    take_profit_atr_multiplier: 4.0 # Higher reward

backtest:
  position_size: 0.5  # Smaller position
```

#### Aggressive Trading (Higher Risk)
```yaml
signals:
  thresholds:
    buy_probability: 0.55   # Lower confidence threshold
    sell_probability: 0.45
  risk_management:
    stop_loss_atr_multiplier: 3.0   # Wider stops
    take_profit_atr_multiplier: 2.0 # Lower reward

backtest:
  position_size: 2.0  # Larger position
```

#### Day Trading (1-minute bars)
```yaml
data:
  timeframe: "1m"

features:
  lagged_returns: [1, 2, 3]      # Shorter lags
  rolling_windows: [5, 10, 20]   # Shorter windows

signals:
  risk_management:
    stop_loss_atr_multiplier: 1.0
    take_profit_atr_multiplier: 1.5
```

#### Swing Trading (Daily bars)
```yaml
data:
  timeframe: "1d"

features:
  lagged_returns: [1, 3, 5, 10]  # Longer lags
  rolling_windows: [20, 50, 200] # Longer windows

signals:
  risk_management:
    stop_loss_atr_multiplier: 3.0
    take_profit_atr_multiplier: 6.0
```

### Python API Usage Examples

#### Example 1: Custom Data Pipeline

```python
from data_api.data_store import DataStore
from features.feature_engineering import FeatureEngineer
from model.predict import ModelPredictor
from signals.signal_engine import SignalEngine

# Load data
store = DataStore(data_path="data/raw")
df = store.load_data(filename="custom_data.csv")

# Engineer features
engineer = FeatureEngineer(
    lagged_returns=[1, 3, 5],
    rolling_windows=[10, 20],
    indicators=['sma', 'rsi', 'atr']
)
df_features = engineer.create_features(df)

# Make predictions
predictor = ModelPredictor(model_path="models/model.joblib")
predictor.load_model()
X = df_features[predictor.feature_names]
predictions, probabilities = predictor.predict(X)

# Generate signals
signal_engine = SignalEngine(
    buy_threshold=0.6,
    sell_threshold=0.4,
    sl_multiplier=2.0,
    tp_multiplier=3.0
)

df_features['prediction'] = predictions
df_features['probability'] = probabilities
signals = signal_engine.generate_signals(df_features)

print(f"Generated {len(signals)} signals")
print(signals.head())
```

#### Example 2: Custom Backtesting

```python
from backtest.backtester import Backtester
import pandas as pd

# Prepare data
df_ohlcv = pd.read_csv("data/raw/test_data.csv")
df_signals = pd.read_csv("outputs/signals.csv")

# Run custom backtest
backtester = Backtester(
    initial_capital=50000.0,  # Custom capital
    position_size=2.0,        # 2 lots
    commission=0.0001,        # Lower commission
    slippage=0.00005          # Lower slippage
)

equity_curve = backtester.run_backtest(df_ohlcv, df_signals)
metrics = backtester.calculate_metrics()

# Print custom metrics
print(f"ROI: {metrics['total_return']:.2f}%")
print(f"Sharpe: {metrics['sharpe_ratio']:.2f}")
print(f"Max DD: {metrics['max_drawdown_pct']:.2f}%")
```

#### Example 3: Live Signal Generation (Simulation)

```python
import time
from datetime import datetime

# Simulate real-time signal generation
while True:
    # Fetch latest data
    fetcher = DataFetcher(api_provider='twelve_data', symbol='EUR/USD')
    df = fetcher.fetch_historical_data(bars=100)

    # Generate features and predictions
    df_features = engineer.create_features(df)
    X = df_features[predictor.feature_names].iloc[-1:]  # Latest bar
    predictions, probabilities = predictor.predict(X)

    # Generate signal
    if probabilities[0] > 0.6:
        print(f"[{datetime.now()}] BUY signal: {probabilities[0]:.2%} confidence")
    elif probabilities[0] < 0.4:
        print(f"[{datetime.now()}] SELL signal: {(1-probabilities[0]):.2%} confidence")

    time.sleep(60)  # Wait 1 minute
```

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
