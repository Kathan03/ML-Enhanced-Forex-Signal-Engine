# Project Structure Documentation

Complete guide to the ML-Enhanced Forex Signal Engine codebase.

---

## 📁 Directory Overview

```
ML-Enhanced-Forex-Signal-Engine/
├── config.yaml                 # Main configuration file
├── requirements.txt            # Python dependencies
├── setup.py                    # Package installation script
├── .env                        # Environment variables (API keys)
├── .gitignore                  # Git ignore patterns
│
├── data_api/                   # Data ingestion & storage
│   ├── __init__.py
│   ├── data_fetcher.py         # Multi-source data fetching
│   └── data_store.py           # Local data caching
│
├── features/                   # Feature engineering
│   ├── __init__.py
│   └── feature_engineering.py  # Technical indicators
│
├── model/                      # Machine learning models
│   ├── __init__.py
│   ├── train_model.py          # Model training
│   └── predict.py              # Inference/prediction
│
├── signals/                    # Signal generation
│   ├── __init__.py
│   └── signal_engine.py        # Trading signal creation
│
├── backtest/                   # Backtesting engine
│   ├── __init__.py
│   └── backtester.py           # Trade simulation
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── config.py               # Config loader
│   └── metrics.py              # Performance metrics
│
├── scripts/                    # Executable scripts
│   ├── run_train.py            # Train models
│   ├── run_signals.py          # Generate signals
│   └── run_backtest.py         # Run backtests
│
├── data/                       # Data storage
│   └── raw/                    # Raw OHLCV data
│
├── models/                     # Trained models
│
├── outputs/                    # Generated outputs
│   ├── signals.csv/json        # Trading signals
│   ├── trade_history.csv       # Backtest trades
│   └── backtest_results.png    # Performance plots
│
├── logs/                       # Application logs
│
└── tests/                      # Test files
    ├── test_phase1.py
    ├── test_phase2.py
    ├── test_phase3.py
    └── test_phase4.py
```

---

## 📄 File Descriptions

### Configuration Files

#### `config.yaml`
**Purpose**: Central configuration for all system parameters

**Key Sections**:
- `data`: Symbol, timeframe, API provider, data paths
- `features`: Technical indicators, lags, windows
- `model`: Model type, hyperparameters, training settings
- `signals`: Signal thresholds, risk management (SL/TP)
- `backtest`: Initial capital, commission, slippage
- `paths`: Output directories

**Dependencies**: None

**Used By**: All scripts (run_train.py, run_signals.py, run_backtest.py)

#### `.env`
**Purpose**: Store sensitive API keys (not in git)

**Contents**:
```bash
FOREX_API_KEY=
TWELVE_DATA_API_KEY=your_key_here
ALPHA_VANTAGE_API_KEY=your_key_here
```

**Dependencies**: None

**Used By**: `data_api/data_fetcher.py`

---

### Data Ingestion (`data_api/`)

#### `data_api/data_fetcher.py` (549 lines)

**Purpose**: Fetch OHLCV data from multiple sources

**Key Classes**:
- `ForexDataFetcher`: Main data fetching class

**Important Functions**:
```python
fetch_historical_data(bars, start_date, end_date)
  # Fetches historical OHLCV data
  # Returns: pandas DataFrame with columns [timestamp, open, high, low, close, volume]

_fetch_from_yfinance(bars, start_date, end_date)
  # FREE API - No key required
  # Symbol format: "EURUSD=X"

_fetch_from_twelve_data(bars, start_date, end_date)
  # Requires API key in .env
  # Symbol format: "EUR/USD"

_fetch_from_alpha_vantage(bars)
  # Requires API key in .env
  # Symbol format: "EURUSD"

_normalize_data(df)
  # Converts different API formats to standard schema

_validate_data(df)
  # Validates OHLC integrity (high >= low, etc.)
```

**Dependencies**:
- pandas
- yfinance (for free data)
- requests (for API calls)
- python-dotenv (for .env)

**Used By**: `scripts/run_train.py`, `scripts/run_backtest.py`

**Configuration**: `config.yaml` → `data.api_provider`, `data.api_key`

---

#### `data_api/data_store.py` (269 lines)

**Purpose**: Cache and persist forex data locally

**Key Classes**:
- `DataStore`: Data persistence manager

**Important Functions**:
```python
save_data(df, filename, append=False)
  # Saves DataFrame to CSV
  # Handles duplicate removal if append=True

load_data(filename, start_date, end_date)
  # Loads cached data with optional date filtering
  # Returns: pandas DataFrame

data_exists(filename)
  # Checks if cached data file exists

get_data_info(filename)
  # Returns metadata: rows, date range, file size
```

**Dependencies**:
- pandas
- pathlib

**Used By**: All scripts for data caching

**File Format**: CSV with columns `[timestamp, open, high, low, close, volume]`

---

### Feature Engineering (`features/`)

#### `features/feature_engineering.py` (368 lines)

**Purpose**: Transform raw OHLCV into ML features

**Key Classes**:
- `FeatureEngineer`: Feature creation pipeline

**Important Functions**:
```python
create_features(df)
  # Creates all features from OHLCV data
  # Returns: DataFrame with 16 feature columns
  # Features: returns, lagged returns, rolling stats, SMA, RSI, ATR

create_target(df)
  # Creates binary target (1=price up, 0=price down)
  # Returns: DataFrame with 'target' column

get_feature_names()
  # Returns: List of feature column names (excludes OHLCV, timestamp)

_compute_rsi(df, period=14)
  # Computes Relative Strength Index

_compute_atr(df, period=14)
  # Computes Average True Range (for volatility)

_compute_sma(df, windows)
  # Computes Simple Moving Averages
```

**Features Created** (16 total):
1. `return` - Simple return
2. `log_return` - Log return
3. `return_lag_1`, `return_lag_3`, `return_lag_5` - Lagged returns
4. `return_mean_10`, `return_mean_20` - Rolling mean
5. `return_std_10`, `return_std_20` - Rolling std dev
6. `sma_10`, `sma_20` - Simple Moving Average
7. `price_to_sma_10`, `price_to_sma_20` - Price relative to SMA
8. `rsi` - Relative Strength Index
9. `atr` - Average True Range
10. `atr_pct` - ATR as percentage

**Dependencies**:
- pandas
- numpy

**Used By**: `scripts/run_train.py`, `scripts/run_backtest.py`

**Configuration**: `config.yaml` → `features.*`

---

### Machine Learning Models (`model/`)

#### `model/train_model.py` (597 lines)

**Purpose**: Train ML models for price prediction

**Key Classes**:
- `ModelTrainer`: Model training orchestrator

**Important Functions**:
```python
prepare_data(df, feature_cols, target_col, train_ratio=0.8)
  # Time-based train/validation split
  # Returns: X_train, X_val, y_train, y_val

train(X_train, y_train, X_val, y_val)
  # Trains the model
  # Returns: Dict of metrics (accuracy, precision, recall, F1, ROC-AUC)

_init_model()
  # Initializes model based on model_type
  # Supports: logistic_regression, random_forest, lstm

_train_sklearn_model(X_train, y_train)
  # Trains Logistic Regression or Random Forest

_train_lstm_model(X_train, y_train, X_val, y_val)
  # Trains LSTM with TensorFlow/Keras
  # Creates sequences for time-series

_create_sequences(X, y, sequence_length)
  # Converts data to LSTM sequences (sliding windows)

save_model(filename)
  # Saves model + scaler + metadata
  # Format: .joblib for sklearn, .h5 + .metadata for LSTM

load_model(filename)
  # Loads trained model from disk

get_feature_importance()
  # Returns feature importance for tree models
```

**Supported Models**:
1. **Logistic Regression**: Fast baseline, linear decision boundary
2. **Random Forest**: Non-linear, feature importance available
3. **LSTM**: Deep learning, captures temporal patterns

**Dependencies**:
- scikit-learn (LogisticRegression, RandomForestClassifier)
- tensorflow/keras (for LSTM)
- joblib (model persistence)
- pandas, numpy

**Used By**: `scripts/run_train.py`

**Configuration**: `config.yaml` → `model.*`

**Output**: `models/model.joblib` (or `.h5` for LSTM)

---

#### `model/predict.py` (289 lines)

**Purpose**: Make predictions with trained models

**Key Classes**:
- `ModelPredictor`: Inference engine

**Important Functions**:
```python
load_model(model_path)
  # Loads trained model + scaler + features

predict(X)
  # Makes batch predictions
  # Returns: (predictions, probabilities)
  # Note: LSTM predictions may have NaN for first N rows

predict_single(features_dict)
  # Predicts for single observation
  # Returns: (prediction, probability)

predict_signals(df_features)
  # Generates predictions with metadata for signal engine
  # Returns: DataFrame with [timestamp, close, prediction, probability]

_validate_features(X)
  # Ensures input features match trained model

_scale_features(X)
  # Applies fitted scaler to features
```

**Dependencies**:
- scikit-learn
- tensorflow/keras (if LSTM)
- joblib
- pandas, numpy

**Used By**: `scripts/run_signals.py`, `scripts/run_backtest.py`

---

### Signal Generation (`signals/`)

#### `signals/signal_engine.py` (343 lines)

**Purpose**: Convert ML predictions to trading signals

**Key Classes**:
- `SignalEngine`: Signal generation with risk management

**Important Functions**:
```python
generate_signals(df)
  # Converts predictions to BUY/SELL/FLAT signals
  # Input: DataFrame with [timestamp, close, atr, prediction, probability]
  # Output: DataFrame with [timestamp, symbol, signal, entry_price, stop_loss, take_profit, confidence]

_determine_signal(probability)
  # Signal logic:
  #   BUY if probability > buy_threshold (default 0.6)
  #   SELL if probability < sell_threshold (default 0.4)
  #   FLAT otherwise

_calculate_sl_tp(signal, entry_price, atr)
  # Calculates stop-loss and take-profit
  # BUY:  SL = entry - (ATR × sl_multiplier), TP = entry + (ATR × tp_multiplier)
  # SELL: SL = entry + (ATR × sl_multiplier), TP = entry - (ATR × tp_multiplier)

export_signals(signals, filename, format='both')
  # Exports signals to CSV and/or JSON

filter_signals(signals, min_confidence=0.0, exclude_flat=True)
  # Filters signals by confidence and type

get_signal_statistics(signals)
  # Returns: total, buy_count, sell_count, flat_count, avg_confidence
```

**Signal Structure**:
```python
{
  'timestamp': '2024-01-15 10:00:00',
  'symbol': 'EURUSD',
  'signal': 'BUY',           # BUY, SELL, or FLAT
  'entry_price': 1.0850,
  'stop_loss': 1.0830,       # ATR-based
  'take_profit': 1.0890,     # ATR-based
  'confidence': 0.74         # Model probability
}
```

**Dependencies**:
- pandas
- numpy

**Used By**: `scripts/run_signals.py`, `scripts/run_backtest.py`

**Configuration**: `config.yaml` → `signals.*`

**Output**: `outputs/signals.csv`, `outputs/signals.json`

---

### Backtesting (`backtest/`)

#### `backtest/backtester.py` (610 lines)

**Purpose**: Simulate trading and calculate performance

**Key Classes**:
- `Backtester`: Trade simulation engine

**Important Functions**:
```python
run_backtest(df_ohlcv, df_signals)
  # Main simulation loop
  # Returns: equity_curve DataFrame
  # Process: Merge data → Iterate bars → Execute trades → Track equity

_execute_trade(signal, entry_price, stop_loss, take_profit, timestamp, current_equity)
  # Opens new position with slippage
  # Returns: Trade dict

_check_exit(trade, current_bar)
  # Checks if SL or TP hit
  # BUY: Exit if low ≤ SL or high ≥ TP
  # SELL: Exit if high ≥ SL or low ≤ TP
  # Returns: (should_exit, exit_price, exit_reason)

_close_trade(trade, exit_price, exit_timestamp, exit_reason)
  # Closes position and calculates P&L
  # P&L = (price_change × position_value) - commission
  # Returns: Closed trade dict with P&L

calculate_metrics()
  # Computes 15+ performance metrics
  # Returns: Dict with total_pnl, win_rate, sharpe_ratio, max_drawdown, etc.

_calculate_drawdown()
  # Computes drawdown series from equity curve

_calculate_sharpe_ratio(returns)
  # Risk-adjusted return metric

plot_results(save=True, show=False)
  # Creates equity curve and drawdown charts
  # Saves to backtest_results.png

export_trades(filename)
  # Exports trade history to CSV

print_summary()
  # Prints formatted performance report
```

**Performance Metrics**:
1. `total_pnl` - Total profit/loss
2. `total_return` - Return percentage
3. `num_trades` - Total trades executed
4. `num_wins` / `num_losses` - Win/loss counts
5. `win_rate` - Percentage of winning trades
6. `avg_win` / `avg_loss` - Average P&L per trade
7. `profit_factor` - Gross profit / gross loss
8. `max_drawdown` - Largest equity decline ($)
9. `max_drawdown_pct` - Largest equity decline (%)
10. `sharpe_ratio` - Risk-adjusted returns

**Dependencies**:
- pandas
- numpy
- matplotlib (for plotting)

**Used By**: `scripts/run_backtest.py`

**Configuration**: `config.yaml` → `backtest.*`

**Output**:
- `outputs/trade_history.csv`
- `outputs/backtest_results.png`

---

### Utilities (`utils/`)

#### `utils/config.py`

**Purpose**: Load and parse configuration

**Key Functions**:
```python
ConfigLoader(config_path)
  # Loads config.yaml
  # Supports environment variable substitution

get(key, default=None)
  # Retrieves config value by dot notation
  # Example: config.get('data.symbol')
```

**Dependencies**:
- pyyaml
- os

---

#### `utils/metrics.py`

**Purpose**: Performance metric calculations

**Key Functions**:
- Various metric computation helpers
- Used by backtester

**Dependencies**:
- numpy

---

### Executable Scripts (`scripts/`)

#### `scripts/run_train.py` (210 lines)

**Purpose**: Train ML models on forex data

**Workflow**:
1. Load configuration
2. Load/fetch data (API or cached)
3. Engineer features
4. Prepare train/validation split
5. Train model
6. Save model and print metrics

**Usage**:
```bash
# Default (Logistic Regression)
python scripts/run_train.py

# Random Forest
python scripts/run_train.py --model random_forest

# LSTM
python scripts/run_train.py --model lstm

# Custom data
python scripts/run_train.py --data data/my_data.csv --output models/my_model.joblib
```

**Arguments**:
- `--config`: Config file path (default: config.yaml)
- `--model`: Model type (logistic_regression, random_forest, lstm)
- `--data`: Data file path (overrides API fetch)
- `--output`: Model output path (default: models/model.joblib)

**Dependencies**: All data, features, model modules

**Output**: Trained model in `models/`

---

#### `scripts/run_signals.py` (239 lines)

**Purpose**: Generate trading signals from trained model

**Workflow**:
1. Load configuration
2. Load trained model
3. Load/fetch data
4. Engineer features
5. Make predictions
6. Generate signals with SL/TP
7. Export signals (CSV/JSON)

**Usage**:
```bash
# Default
python scripts/run_signals.py

# Custom model and output
python scripts/run_signals.py --model models/rf_model.joblib --output my_signals

# Filter FLAT signals
python scripts/run_signals.py --filter

# JSON only
python scripts/run_signals.py --format json
```

**Arguments**:
- `--config`: Config file
- `--model`: Model path
- `--data`: Data file
- `--output`: Output filename (without extension)
- `--format`: Output format (csv, json, both)
- `--filter`: Export filtered signals (BUY/SELL only)

**Dependencies**: All modules

**Output**: `outputs/signals.csv`, `outputs/signals.json`

---

#### `scripts/run_backtest.py` (210 lines)

**Purpose**: Backtest trading strategy

**Workflow**:
1. Load configuration
2. Load trained model
3. Load data
4. Engineer features
5. Make predictions
6. Generate signals
7. Run backtest simulation
8. Calculate metrics
9. Export results and plots

**Usage**:
```bash
# Default
python scripts/run_backtest.py --model models/model.joblib

# Save trades and show plots
python scripts/run_backtest.py --model models/model.joblib --save-trades --plot

# Custom data
python scripts/run_backtest.py --model models/model.joblib --data data/test_data.csv
```

**Arguments**:
- `--config`: Config file
- `--model`: Model path
- `--data`: Data file
- `--plot`: Show plots interactively
- `--save-trades`: Export trade history

**Dependencies**: All modules

**Output**:
- `outputs/trade_history.csv`
- `outputs/backtest_results.png`
- Console summary

---

### Test Files

#### `test_phase1_csv.py`
Tests data ingestion and storage

#### `test_phase2.py`
Tests feature engineering and model training

#### `test_phase3.py`
Tests signal generation

#### `test_phase4.py`
Tests backtesting engine

**Usage**: `python test_phaseN.py`

---

## 🔗 Dependency Graph

```
run_train.py
  → ConfigLoader
  → DataStore
  → DataFetcher
  → FeatureEngineer
  → ModelTrainer

run_signals.py
  → ConfigLoader
  → DataStore
  → DataFetcher (optional)
  → FeatureEngineer
  → ModelPredictor
  → SignalEngine

run_backtest.py
  → ConfigLoader
  → DataStore
  → FeatureEngineer
  → ModelPredictor
  → SignalEngine
  → Backtester
```

---

## 📊 Data Flow

```
1. Data Ingestion:
   API/CSV → DataFetcher → DataStore (cached CSV)

2. Training:
   Raw Data → FeatureEngineer → Features + Target
   Features → ModelTrainer → Trained Model (.joblib)

3. Signal Generation:
   Raw Data → FeatureEngineer → Features
   Features → ModelPredictor → Predictions
   Predictions → SignalEngine → Signals (CSV/JSON)

4. Backtesting:
   Raw Data → FeatureEngineer → Features
   Features → ModelPredictor → Predictions
   Predictions → SignalEngine → Signals
   Signals + Raw Data → Backtester → Metrics + Plots
```

---

## 🎯 Key Configuration Paths

**Data Source**:
- `config.yaml` → `data.api_provider` (yfinance, twelve_data, alpha_vantage, csv)
- `.env` → API keys

**Model Selection**:
- `config.yaml` → `model.type` (logistic_regression, random_forest, lstm)
- `config.yaml` → `model.params` (hyperparameters)

**Signal Thresholds**:
- `config.yaml` → `signals.thresholds.buy_probability` (default: 0.6)
- `config.yaml` → `signals.thresholds.sell_probability` (default: 0.4)

**Risk Management**:
- `config.yaml` → `signals.risk_management.stop_loss_atr_multiplier` (default: 2.0)
- `config.yaml` → `signals.risk_management.take_profit_atr_multiplier` (default: 3.0)

**Backtest Settings**:
- `config.yaml` → `backtest.initial_capital` (default: 10000)
- `config.yaml` → `backtest.commission` (default: 0.0002 = 2 pips)
- `config.yaml` → `backtest.slippage` (default: 0.0001 = 1 pip)

---

## 🔄 Common Workflows

### 1. Train New Model
```bash
python scripts/run_train.py --model random_forest --output models/rf_model.joblib
```

### 2. Generate Signals
```bash
python scripts/run_signals.py --model models/rf_model.joblib --filter
```

### 3. Backtest Strategy
```bash
python scripts/run_backtest.py --model models/rf_model.joblib --save-trades
```

### 4. Full Pipeline
```bash
# Train
python scripts/run_train.py

# Backtest
python scripts/run_backtest.py --model models/model.joblib --save-trades --plot
```

---

## 📦 External Dependencies

**Core**:
- pandas: Data manipulation
- numpy: Numerical operations
- scikit-learn: ML models (LR, RF)
- joblib: Model persistence

**Data**:
- yfinance: Free forex data
- requests: API calls
- python-dotenv: Environment variables

**Deep Learning (Optional)**:
- tensorflow: LSTM models

**Visualization**:
- matplotlib: Plotting

**Config**:
- pyyaml: YAML parsing

**See `requirements.txt` for exact versions**

---

## 💡 Tips for Understanding the Codebase

1. **Start with config.yaml**: Understand all configurable parameters
2. **Follow data flow**: Data → Features → Model → Signals → Backtest
3. **Run tests**: Execute test_phaseN.py to see each component in action
4. **Read docstrings**: Every function has detailed documentation
5. **Check examples**: Test files show usage patterns
6. **Trace a workflow**: Follow run_train.py step by step to see integration

---

This documentation covers the entire codebase structure. Each file's purpose, dependencies, and key functions are described in detail.
