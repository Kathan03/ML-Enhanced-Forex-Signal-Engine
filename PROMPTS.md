# Implementation Prompts for ML-Enhanced Forex Signal Engine

This document contains 4 detailed prompts for implementing each phase of the forex signal engine. Each prompt is designed to be self-contained and can be given to Claude Code to implement that specific phase flawlessly.

---

## 📦 PROMPT 1: Data Ingestion & Storage (Phase 1)

```
You are implementing Phase 1 of the ML-Enhanced Forex Signal Engine: Data Ingestion & Storage.

### Context
You are working on a forex trading signal engine that uses ML to predict price movements. This phase focuses on building a robust data pipeline to fetch and store OHLCV (Open, High, Low, Close, Volume) data from multiple API providers.

### Your Task
Implement the complete data ingestion and storage system with the following components:

1. **data_api/data_fetcher.py** - API integration for fetching forex data
2. **data_api/data_store.py** - Local storage and caching
3. Test the entire pipeline by fetching real data

### Detailed Requirements

#### 1. ForexDataFetcher (data_api/data_fetcher.py)

Implement the following methods:

**fetch_historical_data(bars, start_date, end_date)**
- Support multiple API providers: "twelve_data", "alpha_vantage", "csv"
- For Twelve Data API:
  - Endpoint: https://api.twelvedata.com/time_series
  - Parameters: symbol={symbol}&interval={interval}&apikey={key}&outputsize={bars}
  - Parse JSON response and extract OHLCV data
  - Handle rate limits (8 calls/min on free tier)
- For Alpha Vantage API:
  - Endpoint: https://www.alphavantage.co/query
  - Function: FX_INTRADAY for intraday, FX_DAILY for daily
  - Parameters: function, from_symbol, to_symbol, interval, apikey
  - Parse JSON response
  - Handle rate limits (5 calls/min on free tier)
- For CSV mode:
  - Read from file path specified in config
  - Parse CSV with standard schema

**fetch_realtime_data(bars)**
- Fetch the most recent N bars
- Use same API as historical but with smaller outputsize
- Useful for live simulation

**_normalize_data(df)**
- Convert various API formats to standard schema:
  ```
  timestamp (datetime): Bar timestamp
  open (float): Opening price
  high (float): High price
  low (float): Low price
  close (float): Closing price
  volume (float): Volume
  ```
- Handle different column naming conventions:
  - Twelve Data uses: "datetime", "open", "high", "low", "close", "volume"
  - Alpha Vantage uses: numbered keys like "1. open", "2. high", etc.
- Convert timestamps to pandas datetime
- Sort by timestamp ascending (oldest first)
- Reset index

**_validate_data(df)**
- Check required columns exist
- Validate: high >= low for all rows
- Validate: close is within [low, high]
- Check for missing values in critical columns (OHLC)
- Validate timestamps are sequential with no major gaps
- Raise ValueError if validation fails

**Error Handling:**
- Handle API errors gracefully (timeouts, rate limits, invalid keys)
- Implement retry logic with exponential backoff
- Log errors with helpful messages
- Raise informative exceptions

#### 2. DataStore (data_api/data_store.py)

Implement the following methods:

**save_data(df, filename, append)**
- Validate schema before saving using _validate_schema()
- Default filename: {symbol_lowercase}_{timeframe}.csv
- If append=True:
  - Load existing data
  - Concatenate with new data
  - Remove duplicates based on timestamp
  - Sort by timestamp
- Save to CSV with header
- Use timestamp as index or first column

**load_data(filename, start_date, end_date)**
- Load CSV file from data_path
- Parse timestamp column
- If start_date or end_date specified, filter data
- Return DataFrame with standard schema
- Raise FileNotFoundError if file doesn't exist

**data_exists(filename)**
- Check if file exists in data_path
- Return boolean

**get_data_info(filename)**
- Return metadata dictionary:
  ```python
  {
      'filename': str,
      'rows': int,
      'start_date': str,
      'end_date': str,
      'last_modified': str
  }
  ```

**_validate_schema(df)**
- Check for required columns: timestamp, open, high, low, close, volume
- Check data types are numeric (except timestamp)
- Raise ValueError if invalid

#### 3. Integration & Testing

Create a test script or add to `scripts/run_train.py` to:

**Test Workflow:**
```python
# 1. Initialize components
config = ConfigLoader('config.yaml')
fetcher = ForexDataFetcher(
    api_provider=config.get('data.api_provider'),
    api_key=config.get('data.api_key'),
    symbol=config.get('data.symbol'),
    timeframe=config.get('data.timeframe')
)
store = DataStore(
    data_path=config.get('data.data_path'),
    symbol=config.get('data.symbol'),
    timeframe=config.get('data.timeframe')
)

# 2. Fetch data
print("Fetching data...")
df = fetcher.fetch_historical_data(bars=5000)
print(f"Fetched {len(df)} bars")
print(df.head())
print(df.tail())

# 3. Save data
print("Saving data...")
store.save_data(df)

# 4. Load and verify
print("Loading data...")
df_loaded = store.load_data()
assert len(df_loaded) == len(df)
print(f"Successfully loaded {len(df_loaded)} bars")

# 5. Test date filtering
df_filtered = store.load_data(
    start_date='2024-01-01',
    end_date='2024-06-30'
)
print(f"Filtered data: {len(df_filtered)} bars")

# 6. Get info
info = store.get_data_info()
print(f"Data info: {info}")
```

### Implementation Guidelines

1. **Read existing code structure**: The skeleton is already in place with docstrings
2. **Use environment variables**: API keys should come from .env file via config.yaml
3. **Handle edge cases**: Missing data, API errors, rate limits
4. **Add logging**: Use print statements or Python logging for debugging
5. **Test with real API**: Use Twelve Data free tier (apikey: demo works for testing)
6. **Validate thoroughly**: Run all validation checks
7. **Follow conventions**: Use existing code style and patterns

### Success Criteria

- [ ] Can fetch 1000+ bars from Twelve Data API
- [ ] Can fetch data from Alpha Vantage API (or handle gracefully)
- [ ] Can save data to CSV in correct format
- [ ] Can load data from CSV
- [ ] Data validation catches errors (test with bad data)
- [ ] Date filtering works correctly
- [ ] No data is lost in save/load cycle
- [ ] Code is clean, documented, and follows existing patterns

### Files to Modify

- `data_api/data_fetcher.py` - Implement all methods
- `data_api/data_store.py` - Implement all methods
- `utils/config.py` - Already implemented, use it
- Optionally create a test script to validate

### Example Configuration

Your config.yaml should have:
```yaml
data:
  symbol: "EURUSD"
  timeframe: "1h"
  api_provider: "twelve_data"
  api_key: "${FOREX_API_KEY}"  # Reads from .env
  historical_bars: 5000
  data_path: "data/raw"
```

### Notes

- For testing, you can use Twelve Data's demo API key: "demo"
- The demo key works with limited symbols (AAPL, MSFT, etc.) but not all forex pairs
- For EURUSD, you'll need a real API key (free tier is fine)
- Alternatively, use CSV mode with sample data for initial testing

### Expected Outputs

After implementation:
- `data/raw/eurusd_1h.csv` - 5000+ bars of EURUSD hourly data
- Console output showing successful fetch and save
- Data validated and ready for Phase 2

Implement this phase completely and test thoroughly before moving to Phase 2.
```

---

## 🧠 PROMPT 2: Feature Engineering & Model Training (Phase 2)

```
You are implementing Phase 2 of the ML-Enhanced Forex Signal Engine: Feature Engineering & Model Training.

### Context
Phase 1 is complete - you now have OHLCV data stored in `data/raw/eurusd_1h.csv`. This phase transforms that raw data into ML features, trains a model, and saves it for prediction.

### Your Task
Implement the complete feature engineering and model training pipeline:

1. **features/feature_engineering.py** - Transform OHLCV into ML features
2. **model/train_model.py** - Train and save ML models
3. **model/predict.py** - Load models and make predictions
4. **scripts/run_train.py** - End-to-end training script

### Detailed Requirements

#### 1. FeatureEngineer (features/feature_engineering.py)

Implement the following methods:

**create_features(df)**
- Input: DataFrame with columns [timestamp, open, high, low, close, volume]
- Process:
  1. Compute returns using _compute_returns()
  2. Compute lagged returns using _compute_lagged_returns()
  3. Compute rolling statistics using _compute_rolling_stats()
  4. Compute SMAs using _compute_sma()
  5. Compute RSI using _compute_rsi()
  6. Compute ATR using _compute_atr()
  7. Handle NaN values using _handle_missing_values()
- Output: DataFrame with original columns + all feature columns
- Keep timestamp, OHLCV columns for later use

**create_target(df)**
- Input: DataFrame with OHLCV and features
- Create binary target:
  ```python
  target = 1 if close[t+target_horizon] > close[t] else 0
  ```
- Use target_horizon from config (default: 1)
- Shift to align properly:
  ```python
  df['target'] = (df['close'].shift(-target_horizon) > df['close']).astype(int)
  ```
- Drop last target_horizon rows (they have NaN target)
- Output: DataFrame with 'target' column added

**_compute_returns(df)**
- Add columns:
  ```python
  df['return'] = df['close'].pct_change()  # (close[t] - close[t-1]) / close[t-1]
  df['log_return'] = np.log(df['close'] / df['close'].shift(1))
  ```

**_compute_lagged_returns(df)**
- For each lag in self.lagged_returns (e.g., [1, 3, 5]):
  ```python
  df[f'return_lag_{lag}'] = df['return'].shift(lag)
  ```

**_compute_rolling_stats(df)**
- For each window in self.rolling_windows (e.g., [10, 20, 50]):
  ```python
  df[f'return_mean_{window}'] = df['return'].rolling(window).mean()
  df[f'return_std_{window}'] = df['return'].rolling(window).std()
  ```

**_compute_sma(df)**
- For each window in self.rolling_windows:
  ```python
  df[f'sma_{window}'] = df['close'].rolling(window).mean()
  df[f'price_to_sma_{window}'] = (df['close'] - df[f'sma_{window}']) / df[f'sma_{window}']
  ```

**_compute_rsi(df, period=14)**
- RSI calculation:
  ```python
  delta = df['close'].diff()
  gain = delta.where(delta > 0, 0)
  loss = -delta.where(delta < 0, 0)
  avg_gain = gain.rolling(window=period).mean()
  avg_loss = loss.rolling(window=period).mean()
  rs = avg_gain / avg_loss
  rsi = 100 - (100 / (1 + rs))
  df['rsi'] = rsi
  ```

**_compute_atr(df, period=14)**
- ATR calculation:
  ```python
  high_low = df['high'] - df['low']
  high_close = np.abs(df['high'] - df['close'].shift())
  low_close = np.abs(df['low'] - df['close'].shift())
  true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
  atr = true_range.rolling(window=period).mean()
  df['atr'] = atr
  df['atr_pct'] = atr / df['close']  # Normalized ATR
  ```

**_handle_missing_values(df, method='drop')**
- If method='drop': Drop rows with any NaN in feature columns
- Feature columns are all except: timestamp, open, high, low, close, volume, target
- Use df.dropna() appropriately
- Return cleaned DataFrame

**get_feature_names()**
- Return list of feature column names
- Exclude: timestamp, open, high, low, close, volume, target
- Example return:
  ```python
  ['return', 'log_return', 'return_lag_1', 'return_lag_3', 'return_lag_5',
   'return_mean_10', 'return_std_10', 'sma_10', 'price_to_sma_10', 'rsi', 'atr', 'atr_pct']
  ```

#### 2. ModelTrainer (model/train_model.py)

Implement the following methods:

**prepare_data(df, feature_cols, target_col, train_ratio)**
- Split DataFrame by time (NOT random):
  ```python
  split_idx = int(len(df) * train_ratio)
  train_df = df.iloc[:split_idx]
  val_df = df.iloc[split_idx:]

  X_train = train_df[feature_cols]
  y_train = train_df[target_col]
  X_val = val_df[feature_cols]
  y_val = val_df[target_col]
  ```
- Return (X_train, X_val, y_train, y_val)

**train(X_train, y_train, X_val, y_val)**
- Scale features:
  ```python
  self.scaler = StandardScaler()
  X_train_scaled = self.scaler.fit_transform(X_train)
  X_val_scaled = self.scaler.transform(X_val)
  ```
- Initialize model using _init_model()
- Train using _train_sklearn_model() or _train_lstm_model()
- Evaluate on validation set
- Store metrics in self.training_metrics
- Return metrics dictionary

**_init_model()**
- Based on self.model_type:
  ```python
  if self.model_type == 'logistic_regression':
      from sklearn.linear_model import LogisticRegression
      params = self.model_params or {'C': 1.0, 'max_iter': 1000}
      return LogisticRegression(**params, random_state=self.random_state)

  elif self.model_type == 'random_forest':
      from sklearn.ensemble import RandomForestClassifier
      params = self.model_params or {
          'n_estimators': 100,
          'max_depth': 10,
          'min_samples_split': 5
      }
      return RandomForestClassifier(**params, random_state=self.random_state)

  else:
      raise ValueError(f"Unsupported model type: {self.model_type}")
  ```

**_train_sklearn_model(X_train, y_train)**
- Simple fit:
  ```python
  self.model.fit(X_train, y_train)
  ```

**evaluate(X, y)**
- Make predictions:
  ```python
  X_scaled = self.scaler.transform(X)
  y_pred = self.model.predict(X_scaled)
  y_pred_proba = self.model.predict_proba(X_scaled)[:, 1]
  ```
- Calculate metrics:
  ```python
  from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

  metrics = {
      'accuracy': accuracy_score(y, y_pred),
      'precision': precision_score(y, y_pred),
      'recall': recall_score(y, y_pred),
      'f1': f1_score(y, y_pred),
      'auc': roc_auc_score(y, y_pred_proba)
  }
  ```
- Return metrics

**save_model(filename)**
- Save model, scaler, feature names, and metrics:
  ```python
  import joblib

  filepath = self.model_path / filename
  joblib.dump({
      'model': self.model,
      'scaler': self.scaler,
      'feature_names': self.feature_names,
      'metrics': self.training_metrics,
      'model_type': self.model_type
  }, filepath)
  ```

**load_model(filename)**
- Load from disk:
  ```python
  filepath = self.model_path / filename
  artifacts = joblib.load(filepath)

  self.model = artifacts['model']
  self.scaler = artifacts['scaler']
  self.feature_names = artifacts['feature_names']
  self.training_metrics = artifacts.get('metrics', {})
  self.model_type = artifacts.get('model_type', 'unknown')
  ```

**get_feature_importance()**
- For tree-based models:
  ```python
  if hasattr(self.model, 'feature_importances_'):
      importance_df = pd.DataFrame({
          'feature': self.feature_names,
          'importance': self.model.feature_importances_
      }).sort_values('importance', ascending=False)
      return importance_df
  return None
  ```

#### 3. ModelPredictor (model/predict.py)

Implement the following methods:

**load_model()**
- Load saved model:
  ```python
  artifacts = joblib.load(self.model_path)
  self.model = artifacts['model']
  self.scaler = artifacts['scaler']
  self.feature_names = artifacts['feature_names']
  ```

**predict(X)**
- Validate features using _validate_features()
- Scale using _scale_features()
- Predict:
  ```python
  predictions = self.model.predict(X_scaled)
  probabilities = self.model.predict_proba(X_scaled)[:, 1]
  return predictions, probabilities
  ```

**predict_signals(df_features)**
- Extract features and make predictions
- Return DataFrame with:
  ```python
  result = pd.DataFrame({
      'timestamp': df_features['timestamp'],
      'close': df_features['close'],
      'atr': df_features['atr'],
      'prediction': predictions,
      'probability': probabilities
  })
  ```

**_validate_features(X)**
- Check columns match self.feature_names
- Raise ValueError if mismatch

**_scale_features(X)**
- Apply scaler:
  ```python
  return self.scaler.transform(X[self.feature_names])
  ```

#### 4. run_train.py Script

Implement complete training workflow:

```python
def main():
    # 1. Parse args and load config
    args = parse_args()
    config = ConfigLoader(args.config)

    # 2. Load data
    store = DataStore(
        data_path=config.get('data.data_path'),
        symbol=config.get('data.symbol'),
        timeframe=config.get('data.timeframe')
    )

    df = store.load_data()
    print(f"Loaded {len(df)} bars")

    # 3. Engineer features
    engineer = FeatureEngineer(
        lagged_returns=config.get('features.lagged_returns'),
        rolling_windows=config.get('features.rolling_windows'),
        indicators=config.get('features.indicators'),
        target_horizon=config.get('features.target_horizon')
    )

    df_features = engineer.create_features(df)
    df_with_target = engineer.create_target(df_features)

    print(f"Features created: {len(df_with_target)} rows after cleaning")
    print(f"Feature columns: {engineer.get_feature_names()}")

    # 4. Prepare train/val split
    trainer = ModelTrainer(
        model_type=args.model or config.get('model.type'),
        model_params=config.get(f'model.{config.get("model.type")}'),
        random_state=config.get('model.random_state')
    )

    feature_cols = engineer.get_feature_names()
    X_train, X_val, y_train, y_val = trainer.prepare_data(
        df_with_target,
        feature_cols,
        target_col='target',
        train_ratio=config.get('model.train_test_split')
    )

    print(f"Train size: {len(X_train)}, Val size: {len(X_val)}")
    print(f"Train target distribution: {y_train.value_counts().to_dict()}")

    # 5. Train model
    print("Training model...")
    trainer.feature_names = feature_cols
    metrics = trainer.train(X_train, y_train, X_val, y_val)

    # 6. Evaluate
    val_metrics = trainer.evaluate(X_val, y_val)
    print("\n=== Training Complete ===")
    print(f"Validation Accuracy: {val_metrics['accuracy']:.4f}")
    print(f"Validation Precision: {val_metrics['precision']:.4f}")
    print(f"Validation Recall: {val_metrics['recall']:.4f}")
    print(f"Validation F1: {val_metrics['f1']:.4f}")
    print(f"Validation AUC: {val_metrics['auc']:.4f}")

    # 7. Feature importance (if available)
    importance = trainer.get_feature_importance()
    if importance is not None:
        print("\n=== Feature Importance (Top 10) ===")
        print(importance.head(10))

    # 8. Save model
    output_path = args.output
    trainer.save_model(output_path)
    print(f"\nModel saved to: {output_path}")
```

### Implementation Guidelines

1. **Use NumPy and Pandas efficiently**: Vectorized operations are faster
2. **No data leakage**: Never use future data in features (careful with shifts)
3. **Time-based split**: NEVER use random split for time series
4. **Handle NaN properly**: Drop rows created by rolling windows and shifts
5. **Store feature names**: Critical for consistent prediction
6. **Test incrementally**: Test each feature function individually first

### Success Criteria

- [ ] Features computed correctly (verify calculations manually on first few rows)
- [ ] Target label aligned properly (check alignment with prints)
- [ ] No data leakage (features only use past data)
- [ ] Train/val split maintains temporal order
- [ ] Model trains without errors
- [ ] Validation accuracy > 50% (better than random)
- [ ] Model saves and loads correctly
- [ ] Can make predictions on new data

### Files to Modify

- `features/feature_engineering.py` - Implement all methods
- `model/train_model.py` - Implement all methods
- `model/predict.py` - Implement all methods
- `scripts/run_train.py` - Implement main workflow

### Testing Commands

```bash
# Run training
python scripts/run_train.py --config config.yaml

# Should output:
# - Loaded X bars
# - Created Y features
# - Train/val split sizes
# - Training metrics
# - Model saved to models/model.joblib
```

### Expected Outputs

- `models/model.joblib` - Trained model with scaler and metadata
- Console output with metrics
- Validation accuracy around 52-60% (forex is noisy, this is expected)

Implement this phase completely and test thoroughly before moving to Phase 3.
```

---

## 📊 PROMPT 3: Signal Generation (Phase 3)

```
You are implementing Phase 3 of the ML-Enhanced Forex Signal Engine: Signal Generation.

### Context
Phases 1 and 2 are complete:
- You have OHLCV data in `data/raw/eurusd_1h.csv`
- You have a trained model in `models/model.joblib`
- The model can predict price direction with probabilities

This phase converts ML predictions into actionable trading signals with stop loss, take profit, and confidence scores in EA (Expert Advisor) format.

### Your Task
Implement the complete signal generation pipeline:

1. **signals/signal_engine.py** - Convert predictions to trading signals
2. **scripts/run_live_sim.py** - Simulate live signal generation
3. Test signal generation on historical data

### Detailed Requirements

#### 1. SignalEngine (signals/signal_engine.py)

Implement the following methods:

**generate_signals(df)**
- Input: DataFrame with columns:
  - timestamp: datetime
  - close: current price
  - atr: Average True Range for risk management
  - prediction: binary class (0 or 1)
  - probability: probability of class 1 (price up)

- Process:
  ```python
  signals = []

  for idx, row in df.iterrows():
      # 1. Determine signal type
      signal_type = self._determine_signal(row['probability'])

      # 2. Calculate SL/TP if not FLAT
      if signal_type != 'FLAT':
          sl, tp = self._calculate_sl_tp(
              signal_type,
              row['close'],
              row['atr']
          )
      else:
          sl, tp = None, None

      # 3. Calculate confidence
      if signal_type == 'BUY':
          confidence = row['probability']
      elif signal_type == 'SELL':
          confidence = 1 - row['probability']
      else:
          confidence = 0.0

      # 4. Create signal record
      signal = {
          'timestamp': row['timestamp'],
          'symbol': self.symbol,
          'signal': signal_type,
          'entry_price': row['close'],
          'stop_loss': sl,
          'take_profit': tp,
          'confidence': confidence
      }

      signals.append(signal)

  return pd.DataFrame(signals)
  ```

**_determine_signal(probability)**
- Logic:
  ```python
  if probability > self.buy_threshold:  # e.g., 0.6
      return 'BUY'
  elif probability < self.sell_threshold:  # e.g., 0.4
      return 'SELL'
  else:
      return 'FLAT'
  ```

**_calculate_sl_tp(signal, entry_price, atr)**
- For BUY signal:
  ```python
  stop_loss = entry_price - (atr * self.sl_multiplier)
  take_profit = entry_price + (atr * self.tp_multiplier)
  return stop_loss, take_profit
  ```

- For SELL signal:
  ```python
  stop_loss = entry_price + (atr * self.sl_multiplier)
  take_profit = entry_price - (atr * self.tp_multiplier)
  return stop_loss, take_profit
  ```

- Round to appropriate decimal places (5 for forex):
  ```python
  stop_loss = round(stop_loss, 5)
  take_profit = round(take_profit, 5)
  ```

**export_signals(signals, filename, format)**
- If format == 'csv' or 'both':
  - Call _export_to_csv()
- If format == 'json' or 'both':
  - Call _export_to_json()

**_export_to_csv(signals, filepath)**
- Save to CSV:
  ```python
  signals.to_csv(filepath, index=False)
  print(f"Signals exported to: {filepath}")
  ```

**_export_to_json(signals, filepath)**
- Save to JSON:
  ```python
  # Convert timestamp to string for JSON serialization
  signals_json = signals.copy()
  signals_json['timestamp'] = signals_json['timestamp'].astype(str)

  with open(filepath, 'w') as f:
      json.dump(signals_json.to_dict('records'), f, indent=2)

  print(f"Signals exported to: {filepath}")
  ```

**filter_signals(signals, min_confidence, exclude_flat)**
- Filter logic:
  ```python
  filtered = signals.copy()

  if min_confidence > 0:
      filtered = filtered[filtered['confidence'] >= min_confidence]

  if exclude_flat:
      filtered = filtered[filtered['signal'] != 'FLAT']

  return filtered
  ```

**get_signal_statistics(signals)**
- Calculate stats:
  ```python
  stats = {
      'total_signals': len(signals),
      'buy_count': len(signals[signals['signal'] == 'BUY']),
      'sell_count': len(signals[signals['signal'] == 'SELL']),
      'flat_count': len(signals[signals['signal'] == 'FLAT']),
      'avg_confidence': signals[signals['signal'] != 'FLAT']['confidence'].mean()
  }

  return stats
  ```

#### 2. run_live_sim.py Script

Implement live simulation workflow:

```python
def main():
    args = parse_args()
    config = ConfigLoader(args.config)

    # 1. Load model
    predictor = ModelPredictor(args.model)
    predictor.load_model()
    print("Model loaded successfully")

    # 2. Initialize components
    fetcher = ForexDataFetcher(
        api_provider=config.get('data.api_provider'),
        api_key=config.get('data.api_key'),
        symbol=config.get('data.symbol'),
        timeframe=config.get('data.timeframe')
    )

    engineer = FeatureEngineer(
        lagged_returns=config.get('features.lagged_returns'),
        rolling_windows=config.get('features.rolling_windows'),
        indicators=config.get('features.indicators')
    )

    signal_engine = SignalEngine(
        buy_threshold=config.get('signals.thresholds.buy_probability'),
        sell_threshold=config.get('signals.thresholds.sell_probability'),
        sl_multiplier=config.get('signals.risk_management.stop_loss_atr_multiplier'),
        tp_multiplier=config.get('signals.risk_management.take_profit_atr_multiplier'),
        symbol=config.get('data.symbol')
    )

    # 3. Simulation loop
    print(f"Starting live simulation (interval: {args.interval}s)")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            # Fetch recent data (need enough for feature calculation)
            bars_needed = max(config.get('features.rolling_windows')) + 10
            df = fetcher.fetch_realtime_data(bars=bars_needed)

            # Engineer features
            df_features = engineer.create_features(df)

            # Get latest bar
            latest = df_features.iloc[[-1]]  # Last row as DataFrame

            # Make prediction
            predictions, probabilities = predictor.predict(latest[predictor.feature_names])

            # Generate signal
            signal_data = pd.DataFrame({
                'timestamp': latest['timestamp'],
                'close': latest['close'],
                'atr': latest['atr'],
                'prediction': predictions,
                'probability': probabilities
            })

            signals = signal_engine.generate_signals(signal_data)
            current_signal = signals.iloc[0]

            # Display signal
            print(f"[{current_signal['timestamp']}] "
                  f"{current_signal['signal']} @ {current_signal['entry_price']:.5f} "
                  f"(confidence: {current_signal['confidence']:.2%})")

            if current_signal['signal'] != 'FLAT':
                print(f"  SL: {current_signal['stop_loss']:.5f}, "
                      f"TP: {current_signal['take_profit']:.5f}")

            # Append to output file
            output_path = Path(args.output)
            if output_path.suffix == '.json':
                # Append to JSON array (read, append, write)
                if output_path.exists():
                    with open(output_path, 'r') as f:
                        existing = json.load(f)
                else:
                    existing = []

                signal_dict = current_signal.to_dict()
                signal_dict['timestamp'] = str(signal_dict['timestamp'])
                existing.append(signal_dict)

                with open(output_path, 'w') as f:
                    json.dump(existing, f, indent=2)

            # Wait for next interval
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
```

#### 3. Integration Test

Create a test to verify signals on historical data:

```python
# In run_train.py or separate test script

# After training model, generate signals on validation set
print("\n=== Generating Test Signals ===")

# Load validation data with features
val_data_with_features = df_with_target.iloc[split_idx:]

# Make predictions
predictor = ModelPredictor(args.output)
predictor.load_model()

predictions, probabilities = predictor.predict(
    val_data_with_features[feature_cols]
)

# Prepare data for signal generation
signal_input = pd.DataFrame({
    'timestamp': val_data_with_features['timestamp'].values,
    'close': val_data_with_features['close'].values,
    'atr': val_data_with_features['atr'].values,
    'prediction': predictions,
    'probability': probabilities
})

# Generate signals
signal_engine = SignalEngine(
    buy_threshold=config.get('signals.thresholds.buy_probability'),
    sell_threshold=config.get('signals.thresholds.sell_probability'),
    sl_multiplier=config.get('signals.risk_management.stop_loss_atr_multiplier'),
    tp_multiplier=config.get('signals.risk_management.take_profit_atr_multiplier'),
    symbol=config.get('data.symbol')
)

signals = signal_engine.generate_signals(signal_input)

# Export signals
signal_engine.export_signals(signals, filename='test_signals', format='both')

# Print statistics
stats = signal_engine.get_signal_statistics(signals)
print(f"\nSignal Statistics:")
print(f"  Total: {stats['total_signals']}")
print(f"  BUY: {stats['buy_count']} ({stats['buy_count']/stats['total_signals']*100:.1f}%)")
print(f"  SELL: {stats['sell_count']} ({stats['sell_count']/stats['total_signals']*100:.1f}%)")
print(f"  FLAT: {stats['flat_count']} ({stats['flat_count']/stats['total_signals']*100:.1f}%)")
print(f"  Avg Confidence: {stats['avg_confidence']:.2%}")

# Show sample signals
print("\nSample Signals:")
print(signals[signals['signal'] != 'FLAT'].head(10))
```

### Implementation Guidelines

1. **Precision matters**: Round prices to 5 decimal places for forex
2. **Handle edge cases**: What if ATR is zero or NaN?
3. **Validate logic**: BUY should have SL < entry < TP
4. **Test exports**: Verify JSON and CSV are valid formats
5. **Confidence calculation**: Should reflect actual signal confidence

### Success Criteria

- [ ] Signals generated for all predictions
- [ ] BUY signals: stop_loss < entry_price < take_profit
- [ ] SELL signals: take_profit < entry_price < stop_loss
- [ ] FLAT signals: no SL/TP
- [ ] Confidence values between 0 and 1
- [ ] JSON export is valid JSON (test with json.load())
- [ ] CSV export is valid CSV (test with pandas.read_csv())
- [ ] Signal statistics are correct
- [ ] Live simulation runs without errors

### Files to Modify

- `signals/signal_engine.py` - Implement all methods
- `scripts/run_live_sim.py` - Implement main workflow
- Optionally add signal generation to `scripts/run_train.py` for testing

### Testing Commands

```bash
# Generate signals on test data (add to run_train.py)
python scripts/run_train.py --config config.yaml

# Run live simulation (use CSV mode or demo API)
python scripts/run_live_sim.py --config config.yaml --interval 60
```

### Expected Outputs

- `outputs/test_signals.csv` - Signals in CSV format
- `outputs/test_signals.json` - Signals in JSON format
- `outputs/live_signals.json` - Live simulation signals
- Console output with signal statistics

### Example Signal Output

```json
{
  "timestamp": "2024-01-15 10:00:00",
  "symbol": "EURUSD",
  "signal": "BUY",
  "entry_price": 1.08500,
  "stop_loss": 1.08300,
  "take_profit": 1.08900,
  "confidence": 0.74
}
```

Implement this phase completely and test thoroughly before moving to Phase 4.
```

---

## 🎯 PROMPT 4: Backtesting (Phase 4)

```
You are implementing Phase 4 of the ML-Enhanced Forex Signal Engine: Backtesting.

### Context
Phases 1, 2, and 3 are complete:
- Data pipeline works
- Model trains and predicts
- Signals are generated with SL/TP

This final phase simulates trading based on signals and evaluates performance with comprehensive metrics and visualization.

### Your Task
Implement the complete backtesting system:

1. **backtest/backtester.py** - Trade simulation and metrics
2. **utils/metrics.py** - Metrics calculation utilities
3. **scripts/run_backtest.py** - End-to-end backtest script
4. Generate plots and reports

### Detailed Requirements

#### 1. Backtester (backtest/backtester.py)

Implement the following methods:

**run_backtest(df_ohlcv, df_signals)**
- Input:
  - df_ohlcv: Historical OHLCV data with timestamp
  - df_signals: Signals DataFrame from SignalEngine

- Merge data:
  ```python
  # Merge on timestamp
  df = df_ohlcv.merge(df_signals, on='timestamp', how='inner')
  df = df.sort_values('timestamp').reset_index(drop=True)
  ```

- Simulation loop:
  ```python
  current_position = None
  equity = self.initial_capital
  equity_curve = [equity]
  trades = []

  for i in range(len(df)):
      current_bar = df.iloc[i]

      # Check if we have an open position
      if current_position is not None:
          # Check for exit (SL/TP hit)
          should_exit, exit_price, exit_reason = self._check_exit(
              current_position,
              current_bar
          )

          if should_exit:
              # Close trade
              closed_trade = self._close_trade(
                  current_position,
                  exit_price,
                  current_bar['timestamp'],
                  exit_reason
              )

              # Update equity
              equity += closed_trade['pnl']
              equity_curve.append(equity)
              trades.append(closed_trade)

              current_position = None

      # Check for new signal (only if no position)
      if current_position is None:
          if current_bar['signal'] in ['BUY', 'SELL']:
              # Execute trade at next bar's open
              if i + 1 < len(df):
                  next_bar = df.iloc[i + 1]
                  current_position = self._execute_trade(
                      signal=current_bar['signal'],
                      entry_price=next_bar['open'],  # Enter at next open
                      stop_loss=current_bar['stop_loss'],
                      take_profit=current_bar['take_profit'],
                      timestamp=next_bar['timestamp'],
                      current_equity=equity
                  )

  # Close any remaining position at last bar
  if current_position is not None:
      closed_trade = self._close_trade(
          current_position,
          df.iloc[-1]['close'],
          df.iloc[-1]['timestamp'],
          'END_OF_DATA'
      )
      equity += closed_trade['pnl']
      trades.append(closed_trade)

  # Store results
  self.trades = trades
  self.equity_curve = equity_curve

  return pd.DataFrame(trades)
  ```

**_execute_trade(signal, entry_price, stop_loss, take_profit, timestamp, current_equity)**
- Create trade record:
  ```python
  # Apply slippage
  if signal == 'BUY':
      entry_price += entry_price * self.slippage
  else:  # SELL
      entry_price -= entry_price * self.slippage

  trade = {
      'signal': signal,
      'entry_price': entry_price,
      'stop_loss': stop_loss,
      'take_profit': take_profit,
      'entry_timestamp': timestamp,
      'position_size': self.position_size,
      'entry_equity': current_equity
  }

  return trade
  ```

**_check_exit(trade, current_bar)**
- Check stop loss and take profit:
  ```python
  if trade['signal'] == 'BUY':
      # Check SL
      if current_bar['low'] <= trade['stop_loss']:
          return True, trade['stop_loss'], 'STOP_LOSS'

      # Check TP
      if current_bar['high'] >= trade['take_profit']:
          return True, trade['take_profit'], 'TAKE_PROFIT'

  elif trade['signal'] == 'SELL':
      # Check SL
      if current_bar['high'] >= trade['stop_loss']:
          return True, trade['stop_loss'], 'STOP_LOSS'

      # Check TP
      if current_bar['low'] <= trade['take_profit']:
          return True, trade['take_profit'], 'TAKE_PROFIT'

  return False, None, None
  ```

**_close_trade(trade, exit_price, exit_timestamp, exit_reason)**
- Calculate PnL:
  ```python
  # Apply slippage on exit
  if trade['signal'] == 'BUY':
      exit_price -= exit_price * self.slippage
      pnl = (exit_price - trade['entry_price']) * trade['position_size']
  else:  # SELL
      exit_price += exit_price * self.slippage
      pnl = (trade['entry_price'] - exit_price) * trade['position_size']

  # Subtract commission
  pnl -= self.commission * trade['position_size'] * 2  # Entry + exit

  trade['exit_price'] = exit_price
  trade['exit_timestamp'] = exit_timestamp
  trade['exit_reason'] = exit_reason
  trade['pnl'] = pnl
  trade['return_pct'] = (pnl / trade['entry_equity']) * 100

  return trade
  ```

**calculate_metrics()**
- Calculate all performance metrics:
  ```python
  if len(self.trades) == 0:
      return {}

  trades_df = pd.DataFrame(self.trades)

  # Basic metrics
  total_pnl = trades_df['pnl'].sum()
  final_equity = self.initial_capital + total_pnl
  total_return = (total_pnl / self.initial_capital) * 100

  # Trade statistics
  num_trades = len(trades_df)
  wins = trades_df[trades_df['pnl'] > 0]
  losses = trades_df[trades_df['pnl'] < 0]

  num_wins = len(wins)
  num_losses = len(losses)
  win_rate = (num_wins / num_trades * 100) if num_trades > 0 else 0

  avg_win = wins['pnl'].mean() if len(wins) > 0 else 0
  avg_loss = losses['pnl'].mean() if len(losses) > 0 else 0

  # Profit factor
  gross_profit = wins['pnl'].sum() if len(wins) > 0 else 0
  gross_loss = abs(losses['pnl'].sum()) if len(losses) > 0 else 0
  profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf')

  # Drawdown
  equity_series = pd.Series(self.equity_curve)
  drawdown_df = self._calculate_drawdown()
  max_dd = abs(drawdown_df['drawdown'].min())
  max_dd_pct = abs(drawdown_df['drawdown_pct'].min())

  # Sharpe ratio
  returns = trades_df['return_pct'].values
  sharpe = self._calculate_sharpe_ratio(returns) if len(returns) > 1 else 0

  self.metrics = {
      'initial_capital': self.initial_capital,
      'final_capital': final_equity,
      'total_pnl': total_pnl,
      'total_return': total_return,
      'num_trades': num_trades,
      'num_wins': num_wins,
      'num_losses': num_losses,
      'win_rate': win_rate,
      'avg_win': avg_win,
      'avg_loss': avg_loss,
      'profit_factor': profit_factor,
      'max_drawdown': max_dd,
      'max_drawdown_pct': max_dd_pct,
      'sharpe_ratio': sharpe
  }

  return self.metrics
  ```

**_calculate_drawdown()**
- Compute drawdown series:
  ```python
  equity = pd.Series(self.equity_curve)
  peak = equity.expanding(min_periods=1).max()
  drawdown = equity - peak
  drawdown_pct = (drawdown / peak) * 100

  return pd.DataFrame({
      'equity': equity,
      'peak': peak,
      'drawdown': drawdown,
      'drawdown_pct': drawdown_pct
  })
  ```

**_calculate_sharpe_ratio(returns, risk_free_rate=0.0)**
- Calculate Sharpe:
  ```python
  if len(returns) < 2:
      return 0.0

  excess_returns = returns - risk_free_rate
  return np.mean(excess_returns) / np.std(returns) if np.std(returns) > 0 else 0.0
  ```

**plot_results(save, show)**
- Create visualization:
  ```python
  import matplotlib.pyplot as plt

  fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 10))

  # Equity curve
  self._plot_equity_curve(ax1)

  # Drawdown
  self._plot_drawdown(ax2)

  # Trade distribution
  trades_df = pd.DataFrame(self.trades)
  ax3.hist(trades_df['pnl'], bins=50, edgecolor='black', alpha=0.7)
  ax3.axvline(0, color='red', linestyle='--', linewidth=2)
  ax3.set_xlabel('PnL ($)')
  ax3.set_ylabel('Frequency')
  ax3.set_title('Trade PnL Distribution')
  ax3.grid(True, alpha=0.3)

  plt.tight_layout()

  if save:
      plt.savefig(self.output_path / 'backtest_results.png', dpi=150)
      print(f"Plot saved to: {self.output_path / 'backtest_results.png'}")

  if show:
      plt.show()
  ```

**_plot_equity_curve(ax)**
- Plot equity:
  ```python
  ax.plot(self.equity_curve, linewidth=2, color='blue')
  ax.axhline(self.initial_capital, color='gray', linestyle='--', alpha=0.7, label='Initial Capital')
  ax.set_ylabel('Equity ($)')
  ax.set_title('Equity Curve')
  ax.legend()
  ax.grid(True, alpha=0.3)
  ```

**_plot_drawdown(ax)**
- Plot drawdown:
  ```python
  dd_df = self._calculate_drawdown()
  ax.fill_between(range(len(dd_df)), dd_df['drawdown'], 0, color='red', alpha=0.3)
  ax.plot(dd_df['drawdown'], color='darkred', linewidth=1.5)
  ax.set_ylabel('Drawdown ($)')
  ax.set_title('Drawdown')
  ax.grid(True, alpha=0.3)
  ```

**export_trades(filename)**
- Export to CSV:
  ```python
  trades_df = pd.DataFrame(self.trades)
  filepath = self.output_path / filename
  trades_df.to_csv(filepath, index=False)
  print(f"Trade history saved to: {filepath}")
  ```

**print_summary()**
- Print formatted results:
  ```python
  metrics = self.metrics

  print("\n" + "="*50)
  print(" BACKTEST RESULTS")
  print("="*50)
  print(f"\nCapital:")
  print(f"  Initial:  ${metrics['initial_capital']:,.2f}")
  print(f"  Final:    ${metrics['final_capital']:,.2f}")
  print(f"  Total PnL: ${metrics['total_pnl']:,.2f} ({metrics['total_return']:+.2f}%)")

  print(f"\nTrades:")
  print(f"  Total:    {metrics['num_trades']}")
  print(f"  Wins:     {metrics['num_wins']} ({metrics['win_rate']:.1f}%)")
  print(f"  Losses:   {metrics['num_losses']}")

  print(f"\nPerformance:")
  print(f"  Avg Win:  ${metrics['avg_win']:,.2f}")
  print(f"  Avg Loss: ${metrics['avg_loss']:,.2f}")
  print(f"  Profit Factor: {metrics['profit_factor']:.2f}")

  print(f"\nRisk:")
  print(f"  Max Drawdown: ${metrics['max_drawdown']:,.2f} ({metrics['max_drawdown_pct']:.2f}%)")
  print(f"  Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

  print("="*50 + "\n")
  ```

#### 2. MetricsCalculator (utils/metrics.py)

Implement static methods (already defined in scaffold):
- `sharpe_ratio()`
- `max_drawdown()`
- `max_drawdown_pct()`
- `win_rate()`
- `profit_factor()`
- `average_win_loss()`

These are helper methods used by the backtester.

#### 3. run_backtest.py Script

Implement complete backtest workflow:

```python
def main():
    args = parse_args()
    config = ConfigLoader(args.config)

    print("="*60)
    print(" ML-Enhanced Forex Signal Engine - Backtesting")
    print("="*60)

    # 1. Load data
    print("\n[1/6] Loading data...")
    store = DataStore(
        data_path=config.get('data.data_path'),
        symbol=config.get('data.symbol'),
        timeframe=config.get('data.timeframe')
    )

    df_ohlcv = store.load_data(
        start_date=config.get('dates.test_start'),
        end_date=config.get('dates.test_end')
    )
    print(f"Loaded {len(df_ohlcv)} bars for backtesting")

    # 2. Engineer features
    print("\n[2/6] Engineering features...")
    engineer = FeatureEngineer(
        lagged_returns=config.get('features.lagged_returns'),
        rolling_windows=config.get('features.rolling_windows'),
        indicators=config.get('features.indicators')
    )

    df_features = engineer.create_features(df_ohlcv)
    print(f"Features created: {len(df_features)} rows")

    # 3. Load model and predict
    print("\n[3/6] Loading model and generating predictions...")
    predictor = ModelPredictor(args.model)
    predictor.load_model()

    predictions, probabilities = predictor.predict(
        df_features[predictor.feature_names]
    )
    print(f"Predictions generated: {len(predictions)}")

    # 4. Generate signals
    print("\n[4/6] Generating trading signals...")
    signal_input = pd.DataFrame({
        'timestamp': df_features['timestamp'].values,
        'close': df_features['close'].values,
        'atr': df_features['atr'].values,
        'prediction': predictions,
        'probability': probabilities
    })

    signal_engine = SignalEngine(
        buy_threshold=config.get('signals.thresholds.buy_probability'),
        sell_threshold=config.get('signals.thresholds.sell_probability'),
        sl_multiplier=config.get('signals.risk_management.stop_loss_atr_multiplier'),
        tp_multiplier=config.get('signals.risk_management.take_profit_atr_multiplier'),
        symbol=config.get('data.symbol')
    )

    df_signals = signal_engine.generate_signals(signal_input)

    # Print signal stats
    stats = signal_engine.get_signal_statistics(df_signals)
    print(f"Signals: {stats['buy_count']} BUY, {stats['sell_count']} SELL, {stats['flat_count']} FLAT")

    # 5. Run backtest
    print("\n[5/6] Running backtest simulation...")
    backtester = Backtester(
        initial_capital=config.get('backtest.initial_capital'),
        position_size=config.get('backtest.position_size'),
        commission=config.get('backtest.commission'),
        slippage=config.get('backtest.slippage')
    )

    trade_history = backtester.run_backtest(df_features, df_signals)
    print(f"Backtest complete: {len(trade_history)} trades executed")

    # 6. Calculate and display metrics
    print("\n[6/6] Calculating performance metrics...")
    metrics = backtester.calculate_metrics()

    backtester.print_summary()

    # Export results
    if args.save_trades:
        backtester.export_trades('trade_history.csv')

    if args.plot:
        backtester.plot_results(save=True, show=True)
    else:
        backtester.plot_results(save=True, show=False)

    print("Backtest complete!")
```

### Implementation Guidelines

1. **Realistic execution**: Enter at next bar's open, not current close
2. **SL/TP checking**: Check both high and low of each bar
3. **Commission and slippage**: Apply to both entry and exit
4. **Single position**: Close before opening new (no overlapping)
5. **Edge cases**: Handle last bar, no trades, etc.

### Success Criteria

- [ ] Backtest runs without errors
- [ ] All trades have entry and exit
- [ ] PnL calculations are correct (spot check manually)
- [ ] Equity curve is logical (no huge jumps)
- [ ] Win rate between 0-100%
- [ ] Metrics match manual calculations
- [ ] Plots display correctly
- [ ] Trade history exports successfully

### Files to Modify

- `backtest/backtester.py` - Implement all methods
- `utils/metrics.py` - Implement helper methods (already have skeletons)
- `scripts/run_backtest.py` - Implement main workflow

### Testing Commands

```bash
# Run complete backtest
python scripts/run_backtest.py --config config.yaml --plot --save-trades

# Check outputs
ls outputs/
cat outputs/trade_history.csv | head -20
```

### Expected Outputs

- Console output with formatted metrics
- `outputs/backtest_results.png` - 3-panel plot (equity, drawdown, distribution)
- `outputs/trade_history.csv` - Detailed trade log

### Example Output

```
==================================================
 BACKTEST RESULTS
==================================================

Capital:
  Initial:  $10,000.00
  Final:    $11,250.00
  Total PnL: $1,250.00 (+12.50%)

Trades:
  Total:    87
  Wins:     52 (59.8%)
  Losses:   35

Performance:
  Avg Win:  $48.50
  Avg Loss: $-32.10
  Profit Factor: 1.95

Risk:
  Max Drawdown: $-425.00 (-4.12%)
  Sharpe Ratio: 1.23

==================================================
```

Implement this phase completely and test thoroughly. After completion, the entire system is functional!
```

---

## ✅ Summary

These 4 prompts provide complete, step-by-step instructions for implementing the entire ML-Enhanced Forex Signal Engine:

1. **Prompt 1**: Data fetching from APIs, storage, caching
2. **Prompt 2**: Feature engineering, model training, prediction
3. **Prompt 3**: Signal generation with SL/TP, live simulation
4. **Prompt 4**: Backtesting with metrics and visualization

Each prompt:
- Is self-contained and detailed
- Includes complete code examples
- Specifies exact implementation requirements
- Provides testing instructions
- Defines success criteria
- Lists expected outputs

When given to Claude Code sequentially, these prompts will result in a fully functional forex signal engine ready for portfolio demonstration.
