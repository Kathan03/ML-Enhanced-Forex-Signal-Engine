# Implementation Plan: ML-Enhanced Forex Signal Engine

## 📋 Overview

This document outlines the complete implementation strategy for building the forex signal engine in 4 distinct phases, each building upon the previous one.

## 🎯 Implementation Philosophy

1. **Incremental Development**: Each phase delivers working, testable functionality
2. **Clear Dependencies**: Later phases depend on earlier ones being complete
3. **Test as You Go**: Validate each component before moving forward
4. **Maintain Consistency**: Follow established patterns and conventions

---

## Phase 1: Data Ingestion & Storage

### Objective
Build a robust data pipeline that can fetch, store, and retrieve forex OHLCV data from multiple sources.

### Components to Implement

#### 1.1 `data_api/data_fetcher.py`

**Key Functions:**
- `fetch_historical_data()`: Main API to fetch historical bars
- `fetch_realtime_data()`: Fetch recent N bars for live simulation
- `_fetch_from_twelve_data()`: Twelve Data API implementation
- `_fetch_from_alpha_vantage()`: Alpha Vantage API implementation
- `_normalize_data()`: Convert various API formats to standard schema
- `_validate_data()`: Quality checks on fetched data

**Dependencies:**
- `requests` library for HTTP calls
- API keys from environment variables
- Rate limiting logic (API-specific)

**Implementation Details:**
1. **Twelve Data API**:
   - Endpoint: `https://api.twelvedata.com/time_series`
   - Parameters: `symbol`, `interval`, `apikey`, `outputsize`
   - Handle rate limits (8 calls/min on free tier)

2. **Alpha Vantage API**:
   - Endpoint: `https://www.alphavantage.co/query`
   - Function: `FX_INTRADAY` or `FX_DAILY`
   - Handle rate limits (5 calls/min on free tier)

3. **CSV Fallback**:
   - If `api_provider="csv"`, read from local file
   - Useful for testing without API calls

4. **Data Normalization**:
   ```python
   # Standard schema
   {
       "timestamp": datetime,
       "open": float,
       "high": float,
       "low": float,
       "close": float,
       "volume": float
   }
   ```

5. **Data Validation**:
   - Check for required columns
   - Validate: `high >= low`, `close` in `[low, high]`
   - Check for gaps in timestamps
   - Handle missing values

#### 1.2 `data_api/data_store.py`

**Key Functions:**
- `save_data()`: Save DataFrame to CSV
- `load_data()`: Load CSV with optional date filtering
- `data_exists()`: Check if file exists
- `get_data_info()`: Metadata about stored data
- `_validate_schema()`: Ensure data matches expected format

**Implementation Details:**
1. **File Naming Convention**: `{symbol_lowercase}_{timeframe}.csv`
   - Example: `eurusd_1h.csv`

2. **CSV Format**:
   - Include header row
   - Timestamp as index or first column
   - Use standard column names

3. **Append vs Overwrite**:
   - Support both modes
   - When appending, check for duplicates
   - Sort by timestamp after append

4. **Date Filtering**:
   - Parse date strings to datetime
   - Filter DataFrame efficiently using boolean indexing

### Testing Checklist

- [ ] Fetch 1000 bars from Twelve Data API
- [ ] Fetch data from Alpha Vantage API
- [ ] Save data to CSV
- [ ] Load data from CSV
- [ ] Verify data schema is correct
- [ ] Check data validation catches errors
- [ ] Test date range filtering

### Expected Outputs

- `data/raw/eurusd_1h.csv`: 5000+ bars of EURUSD 1h data
- Data validated and ready for feature engineering

---

## Phase 2: Feature Engineering & Model Training

### Objective
Transform raw OHLCV data into ML features, train models, and save them for prediction.

### Components to Implement

#### 2.1 `features/feature_engineering.py`

**Key Functions:**
- `create_features()`: Main feature engineering pipeline
- `create_target()`: Generate binary target (price up/down)
- `_compute_returns()`: Price returns
- `_compute_lagged_returns()`: Lagged return features
- `_compute_rolling_stats()`: Rolling mean/std
- `_compute_sma()`: Simple Moving Averages
- `_compute_rsi()`: Relative Strength Index
- `_compute_atr()`: Average True Range
- `_handle_missing_values()`: NaN handling
- `get_feature_names()`: List of feature columns

**Feature Specifications:**

1. **Returns** (2 features):
   ```python
   return = (close[t] - close[t-1]) / close[t-1]
   log_return = log(close[t] / close[t-1])
   ```

2. **Lagged Returns** (N features based on config):
   ```python
   return_lag_1 = return[t-1]
   return_lag_3 = return[t-3]
   return_lag_5 = return[t-5]
   ```

3. **Rolling Statistics** (2 × N_windows features):
   ```python
   return_mean_10 = rolling_mean(return, window=10)
   return_std_10 = rolling_std(return, window=10)
   # Repeat for windows: [10, 20, 50]
   ```

4. **Simple Moving Averages** (2 × N_windows features):
   ```python
   sma_10 = rolling_mean(close, window=10)
   price_to_sma_10 = (close - sma_10) / sma_10
   # Repeat for windows: [10, 20, 50]
   ```

5. **RSI** (1 feature):
   ```python
   # 14-period RSI
   gains = close.diff().clip(lower=0)
   losses = -close.diff().clip(upper=0)
   avg_gain = gains.rolling(14).mean()
   avg_loss = losses.rolling(14).mean()
   rs = avg_gain / avg_loss
   rsi = 100 - (100 / (1 + rs))
   ```

6. **ATR** (2 features):
   ```python
   tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
   atr = rolling_mean(tr, window=14)
   atr_pct = atr / close  # Normalized ATR
   ```

7. **Target Label**:
   ```python
   target = 1 if close[t+1] > close[t] else 0
   ```

**NaN Handling:**
- Drop initial rows where features are NaN (due to rolling windows)
- Typically drop first 50-100 rows depending on largest window

#### 2.2 `model/train_model.py`

**Key Functions:**
- `prepare_data()`: Split into train/validation sets (time-based)
- `train()`: Train the ML model
- `_init_model()`: Initialize model based on type
- `_train_sklearn_model()`: Train scikit-learn models
- `_train_lstm_model()`: Train LSTM (optional)
- `evaluate()`: Compute evaluation metrics
- `save_model()`: Serialize model + scaler
- `load_model()`: Deserialize model
- `get_feature_importance()`: For tree-based models

**Model Implementations:**

1. **Logistic Regression** (baseline):
   ```python
   from sklearn.linear_model import LogisticRegression

   model = LogisticRegression(
       C=1.0,
       max_iter=1000,
       random_state=42
   )
   model.fit(X_train_scaled, y_train)
   ```

2. **Random Forest**:
   ```python
   from sklearn.ensemble import RandomForestClassifier

   model = RandomForestClassifier(
       n_estimators=100,
       max_depth=10,
       min_samples_split=5,
       random_state=42
   )
   model.fit(X_train_scaled, y_train)
   ```

3. **LSTM** (optional, requires TensorFlow):
   ```python
   import tensorflow as tf

   model = tf.keras.Sequential([
       tf.keras.layers.LSTM(64, input_shape=(sequence_length, n_features)),
       tf.keras.layers.Dropout(0.2),
       tf.keras.layers.Dense(32, activation='relu'),
       tf.keras.layers.Dense(1, activation='sigmoid')
   ])
   model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
   model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=50)
   ```

**Data Splitting:**
- Time-based split (NOT random!)
- First 80% for training
- Next 20% for validation/testing
- Preserve temporal order

**Feature Scaling:**
```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
```

**Model Persistence:**
```python
import joblib

# Save
joblib.dump({
    'model': model,
    'scaler': scaler,
    'feature_names': feature_names,
    'metrics': metrics
}, 'models/model.joblib')

# Load
artifacts = joblib.load('models/model.joblib')
```

#### 2.3 `model/predict.py`

**Key Functions:**
- `load_model()`: Load trained model from disk
- `predict()`: Batch predictions with probabilities
- `predict_single()`: Single observation prediction
- `predict_signals()`: Format for signal engine
- `_validate_features()`: Ensure features match training
- `_scale_features()`: Apply fitted scaler

**Prediction Output:**
```python
# Returns tuple: (predictions, probabilities)
predictions = [0, 1, 1, 0, ...]  # Binary class
probabilities = [0.42, 0.68, 0.73, 0.35, ...]  # P(class=1)
```

#### 2.4 `scripts/run_train.py`

**Complete Workflow:**
```python
1. Load config
2. Initialize components:
   - DataStore
   - FeatureEngineer
   - ModelTrainer
3. Load data from CSV (or fetch if not exists)
4. Engineer features
5. Create target
6. Prepare train/val split
7. Train model
8. Evaluate on validation set
9. Save model
10. Print metrics and feature importance
```

### Testing Checklist

- [ ] Features computed correctly (verify calculations manually)
- [ ] No data leakage (future data not used in features)
- [ ] Target labels aligned correctly (shifted by 1)
- [ ] NaN values handled properly
- [ ] Train/val split preserves temporal order
- [ ] Model trains without errors
- [ ] Model achieves >50% validation accuracy
- [ ] Model saves and loads correctly
- [ ] Feature importance makes sense (for RF)

### Expected Outputs

- `models/model.joblib`: Trained model with scaler and metadata
- Training metrics printed to console
- Validation accuracy, precision, recall, F1, AUC

---

## Phase 3: Signal Generation

### Objective
Convert ML predictions into EA-style trading signals with stop loss, take profit, and confidence scores.

### Components to Implement

#### 3.1 `signals/signal_engine.py`

**Key Functions:**
- `generate_signals()`: Main signal generation pipeline
- `_determine_signal()`: Map probability to BUY/SELL/FLAT
- `_calculate_sl_tp()`: Calculate stop loss and take profit
- `export_signals()`: Save to JSON/CSV
- `_export_to_csv()`: CSV export
- `_export_to_json()`: JSON export
- `filter_signals()`: Filter by confidence
- `get_signal_statistics()`: Signal distribution stats

**Signal Generation Logic:**

1. **Signal Determination**:
   ```python
   if probability > buy_threshold (e.g., 0.6):
       signal = "BUY"
   elif probability < sell_threshold (e.g., 0.4):
       signal = "SELL"
   else:
       signal = "FLAT"
   ```

2. **Risk Management**:
   ```python
   # For BUY signal:
   entry_price = current_close
   stop_loss = entry_price - (atr * sl_multiplier)
   take_profit = entry_price + (atr * tp_multiplier)
   confidence = probability

   # For SELL signal:
   entry_price = current_close
   stop_loss = entry_price + (atr * sl_multiplier)
   take_profit = entry_price - (atr * tp_multiplier)
   confidence = 1 - probability  # Confidence in down move

   # For FLAT:
   stop_loss = None
   take_profit = None
   ```

3. **Signal Structure**:
   ```python
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

**Export Formats:**

1. **CSV**:
   ```csv
   timestamp,symbol,signal,entry_price,stop_loss,take_profit,confidence
   2024-01-15 10:00:00,EURUSD,BUY,1.0850,1.0830,1.0890,0.74
   ```

2. **JSON**:
   ```json
   [
       {
           "timestamp": "2024-01-15 10:00:00",
           "symbol": "EURUSD",
           "signal": "BUY",
           "entry_price": 1.0850,
           "stop_loss": 1.0830,
           "take_profit": 1.0890,
           "confidence": 0.74
       }
   ]
   ```

#### 3.2 `scripts/run_live_sim.py`

**Workflow:**
```python
1. Load config and model
2. Loop (or run once):
   a. Fetch recent N bars (e.g., last 100)
   b. Engineer features
   c. Make prediction
   d. Generate signal
   e. Log signal to file
   f. Sleep for interval
```

### Testing Checklist

- [ ] Signals generated for all predictions
- [ ] BUY signals have SL < entry < TP
- [ ] SELL signals have TP < entry < SL
- [ ] FLAT signals have no SL/TP
- [ ] Confidence values are valid probabilities
- [ ] JSON export is valid JSON
- [ ] CSV export is valid CSV
- [ ] Signal statistics are correct

### Expected Outputs

- `outputs/signals.csv`: All signals in CSV format
- `outputs/signals.json`: All signals in JSON format
- Console output showing signal distribution

---

## Phase 4: Backtesting

### Objective
Simulate trading based on generated signals and evaluate performance with comprehensive metrics.

### Components to Implement

#### 4.1 `backtest/backtester.py`

**Key Functions:**
- `run_backtest()`: Main backtesting loop
- `_execute_trade()`: Open a new trade
- `_check_exit()`: Check if position should close
- `_close_trade()`: Close position and calculate PnL
- `calculate_metrics()`: Performance metrics
- `_calculate_drawdown()`: Drawdown series
- `_calculate_sharpe_ratio()`: Sharpe ratio
- `plot_results()`: Visualization
- `_plot_equity_curve()`: Equity curve subplot
- `_plot_drawdown()`: Drawdown subplot
- `export_trades()`: Trade history to CSV
- `print_summary()`: Formatted results

**Backtesting Logic:**

1. **Trade Execution Model**:
   ```
   Signal received at bar[t] close
   → Enter at bar[t+1] open (or use entry_price from signal)
   → Exit when:
      - Stop loss hit: bar[i].low <= stop_loss (for BUY)
      - Take profit hit: bar[i].high >= take_profit (for BUY)
      - Opposite signal received
      - End of data
   ```

2. **Position Management**:
   ```python
   # Single position at a time
   current_position = None  # or {"type": "BUY", "entry": 1.0850, ...}

   # For each bar:
   if current_position is None:
       if signal == "BUY" or signal == "SELL":
           current_position = open_trade(signal)
   else:
       if should_exit(current_position, current_bar):
           pnl = close_trade(current_position)
           current_position = None
   ```

3. **PnL Calculation**:
   ```python
   # For BUY trade:
   pnl = (exit_price - entry_price) * position_size
   pnl -= commission * position_size
   pnl -= slippage * position_size

   # For SELL trade:
   pnl = (entry_price - exit_price) * position_size
   pnl -= commission * position_size
   pnl -= slippage * position_size
   ```

4. **Equity Tracking**:
   ```python
   equity_curve = [initial_capital]

   for trade in closed_trades:
       new_equity = equity_curve[-1] + trade.pnl
       equity_curve.append(new_equity)
   ```

**Metrics to Calculate:**

1. **Total PnL**:
   ```python
   total_pnl = sum(trade.pnl for trade in trades)
   total_return = (final_equity - initial_equity) / initial_equity * 100
   ```

2. **Win Rate**:
   ```python
   wins = [t for t in trades if t.pnl > 0]
   win_rate = len(wins) / len(trades) * 100
   ```

3. **Average Win/Loss**:
   ```python
   avg_win = mean([t.pnl for t in trades if t.pnl > 0])
   avg_loss = mean([t.pnl for t in trades if t.pnl < 0])
   ```

4. **Profit Factor**:
   ```python
   gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
   gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
   profit_factor = gross_profit / gross_loss if gross_loss > 0 else inf
   ```

5. **Max Drawdown**:
   ```python
   peak = expanding_max(equity_curve)
   drawdown = equity_curve - peak
   max_drawdown = min(drawdown)
   max_drawdown_pct = (max_drawdown / peak[max_dd_index]) * 100
   ```

6. **Sharpe Ratio**:
   ```python
   returns = diff(equity_curve) / equity_curve[:-1]
   sharpe = sqrt(252) * mean(returns) / std(returns)
   # Assumes daily returns; adjust for timeframe
   ```

#### 4.2 `utils/metrics.py`

Implement helper functions used by backtester:
- `sharpe_ratio()`
- `max_drawdown()`
- `max_drawdown_pct()`
- `win_rate()`
- `profit_factor()`
- `average_win_loss()`

#### 4.3 Visualization

**Equity Curve Plot**:
```python
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Equity curve
ax1.plot(timestamps, equity_curve, label='Equity')
ax1.set_ylabel('Equity ($)')
ax1.set_title('Equity Curve')
ax1.legend()
ax1.grid(True)

# Drawdown
ax2.fill_between(timestamps, drawdown, 0, color='red', alpha=0.3)
ax2.set_ylabel('Drawdown ($)')
ax2.set_xlabel('Date')
ax2.set_title('Drawdown')
ax2.grid(True)

plt.tight_layout()
plt.savefig('outputs/backtest_results.png')
```

#### 4.4 `scripts/run_backtest.py`

**Complete Workflow**:
```python
1. Load config
2. Load trained model
3. Load test data
4. Engineer features
5. Generate predictions
6. Create signals
7. Run backtest simulation
8. Calculate metrics
9. Generate plots
10. Print summary report
11. Export trade history
```

### Testing Checklist

- [ ] Backtest runs without errors
- [ ] All trades have entry and exit prices
- [ ] PnL calculations are correct
- [ ] Equity curve is monotonic or realistic
- [ ] Drawdown is always negative or zero
- [ ] Win rate is between 0-100%
- [ ] Metrics match manual calculations
- [ ] Plots display correctly
- [ ] Trade history exports correctly

### Expected Outputs

- Console output with formatted metrics
- `outputs/backtest_results.png`: Equity curve and drawdown plots
- `outputs/trade_history.csv`: Detailed trade log
- Performance summary report

---

## 🔄 Integration & End-to-End Testing

After all 4 phases are complete, run the full pipeline:

```bash
# 1. Train model
python scripts/run_train.py --config config.yaml

# 2. Run backtest
python scripts/run_backtest.py --config config.yaml --plot --save-trades

# 3. Check results
cat outputs/trade_history.csv
open outputs/backtest_results.png
```

**End-to-End Validation:**

1. Data flows correctly through all stages
2. Feature engineering is consistent (train vs test)
3. Model loads and predicts correctly
4. Signals are valid and actionable
5. Backtest produces realistic results
6. Metrics are calculated correctly
7. All outputs are generated

---

## 📊 Success Criteria

### Phase 1
- [ ] Successfully fetch 5000+ bars from API
- [ ] Data saved to CSV and loadable
- [ ] Data validation passes

### Phase 2
- [ ] Features computed without errors
- [ ] Model trained with >50% validation accuracy
- [ ] Model saves and loads correctly
- [ ] Feature importance available (for tree models)

### Phase 3
- [ ] Signals generated for all predictions
- [ ] JSON and CSV exports valid
- [ ] Risk management (SL/TP) calculated correctly

### Phase 4
- [ ] Backtest completes successfully
- [ ] Metrics are realistic (not too good to be true)
- [ ] Plots generated and meaningful
- [ ] Trade history is detailed and accurate

---

## 🚨 Common Pitfalls to Avoid

1. **Data Leakage**:
   - Never use future data in features
   - Always maintain temporal order
   - Split data by time, not randomly

2. **Look-Ahead Bias**:
   - Signals based on bar[t] close can only execute at bar[t+1] open
   - Don't backtest with bar close prices

3. **Overfitting**:
   - Start with simple models
   - Use time-based validation
   - Don't optimize on test set

4. **Unrealistic Assumptions**:
   - Include slippage and commission
   - Model realistic execution
   - Don't assume perfect fills

5. **NaN Handling**:
   - Drop initial rows with NaN features
   - Ensure train and test use same logic
   - Validate data before training

---

## 📝 Documentation Checklist

For each phase:
- [ ] Code comments explaining key logic
- [ ] Docstrings for all functions
- [ ] README updated with usage examples
- [ ] Configuration options documented
- [ ] Example outputs provided

---

## 🎯 Next Steps After Completion

1. **Model Experimentation**:
   - Try RandomForest
   - Experiment with feature combinations
   - Test different hyperparameters

2. **Strategy Improvement**:
   - Adjust signal thresholds
   - Modify SL/TP multipliers
   - Add filters (volatility, trend)

3. **Portfolio Ready**:
   - Clean up code
   - Add comprehensive README
   - Create demo notebook
   - Record demo video

---

This implementation plan ensures a systematic, testable approach to building the complete forex signal engine. Each phase builds incrementally, allowing for validation at every step.
