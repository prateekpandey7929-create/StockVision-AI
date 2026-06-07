import os
import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from datetime import datetime

def train_ticker_model(ticker_symbol, models_dir):
    """
    Downloads historical data for ticker_symbol, engineers features,
    trains Random Forest and Linear Regression models, evaluates them,
    and saves the model metadata to models_dir.
    """
    print(f"Starting ML training pipeline for: {ticker_symbol}")
    
    # 1. Download historical data (2 years of daily data is perfect for dynamic training)
    # yfinance returns pandas DataFrame
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="2y")
    
    if df.empty or len(df) < 50:
        raise ValueError(f"Insufficient or no historical data found for symbol '{ticker_symbol}'. Please verify the symbol.")
        
    df = df.reset_index()
    
    # Clean column names (sometimes yfinance column names vary slightly)
    # Ensure standard names: Date, Open, High, Low, Close, Volume
    df = df.rename(columns={
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    })
    
    # Sort by date
    df = df.sort_values(by='date').reset_index(drop=True)
    
    # Keep copies of date strings for UI plotting
    df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
    
    # 2. Feature Engineering
    # Technical Indicators & Lags
    df['Close_Lag_1'] = df['close'].shift(1)
    df['Close_Lag_2'] = df['close'].shift(2)
    df['Close_Lag_3'] = df['close'].shift(3)
    df['Volume_Lag_1'] = df['volume'].shift(1)
    
    # Simple Moving Averages based on previous Close
    df['SMA_5'] = df['Close_Lag_1'].rolling(window=5).mean()
    df['SMA_10'] = df['Close_Lag_1'].rolling(window=10).mean()
    df['SMA_20'] = df['Close_Lag_1'].rolling(window=20).mean()
    
    # High-Low spread of previous day
    df['HL_Spread_Lag_1'] = (df['high'] - df['low']).shift(1)
    
    # Daily returns lag
    df['Daily_Return_Lag_1'] = df['close'].pct_change().shift(1)
    
    # Volatility lag (rolling std dev of daily return over 5 days)
    df['Volatility_5'] = df['Daily_Return_Lag_1'].rolling(window=5).std()
    
    # Target: Next Day's Close
    df['Target_Next_Close'] = df['close'].shift(-1)
    
    # Features List
    features = [
        'open', 'high', 'low', 'close', 'volume', 
        'Close_Lag_1', 'Close_Lag_2', 'Close_Lag_3', 'Volume_Lag_1',
        'SMA_5', 'SMA_10', 'SMA_20', 'HL_Spread_Lag_1', 
        'Daily_Return_Lag_1', 'Volatility_5'
    ]
    
    # Extract the very last row which represents "today"'s data. 
    # This row has all features calculated, but its Target_Next_Close is NaN (future price).
    # We will use this to generate the prediction for "tomorrow".
    latest_row = df.iloc[-1].copy()
    
    # Check if the latest row has NaN in features (e.g. if we have extremely short data, which shouldn't happen with 2y period)
    # If it does, we fill NaN with 0 or mean just in case.
    latest_features_dict = {}
    for feat in features:
        val = latest_row[feat]
        if pd.isna(val):
            # Fallback to mean of the column
            val = float(df[feat].mean()) if not pd.isna(df[feat].mean()) else 0.0
        latest_features_dict[feat] = float(val)
        
    latest_features_df = pd.DataFrame([latest_features_dict])[features]
    
    # For training, drop the last row (target is NaN) and drop rows with NaN in features (first 20 rows due to SMAs/Lags)
    train_df = df.dropna(subset=['Target_Next_Close'] + features).copy()
    
    if len(train_df) < 30:
        raise ValueError(f"Insufficient cleaned historical data for ticker '{ticker_symbol}' (Need at least 30 rows of valid data).")
        
    X = train_df[features]
    y = train_df['Target_Next_Close']
    dates = train_df['date_str'].values
    
    # 3. Train Test Split (Chronological, typical for time series)
    split_idx = int(len(train_df) * 0.8)
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
    test_dates = dates[split_idx:]
    
    # 4. Model Training
    # Random Forest Regressor
    rf_model = RandomForestRegressor(n_estimators=150, max_depth=10, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    rf_preds = rf_model.predict(X_test)
    
    # Linear Regression (Comparison Baseline)
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    lr_preds = lr_model.predict(X_test)
    
    # 5. Evaluation Metrics
    # Random Forest
    rf_mae = mean_absolute_error(y_test, rf_preds)
    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_preds))
    rf_r2 = r2_score(y_test, rf_preds)
    
    # Linear Regression
    lr_mae = mean_absolute_error(y_test, lr_preds)
    lr_rmse = np.sqrt(mean_squared_error(y_test, lr_preds))
    lr_r2 = r2_score(y_test, lr_preds)
    
    # Save test actuals and predictions (limit to last 60 days to keep file size small and clean for plots)
    plot_limit = min(60, len(y_test))
    eval_data = {
        'dates': list(test_dates[-plot_limit:]),
        'actual': [float(val) for val in y_test[-plot_limit:]],
        'predicted_rf': [float(val) for val in rf_preds[-plot_limit:]],
        'predicted_lr': [float(val) for val in lr_preds[-plot_limit:]]
    }
    
    # Save package to dictionary
    model_package = {
        'ticker': ticker_symbol,
        'rf_model': rf_model,
        'lr_model': lr_model,
        'features': features,
        'latest_features': latest_features_dict,
        'last_price': float(latest_row['close']),
        'metrics': {
            'rf': {
                'mae': float(rf_mae),
                'rmse': float(rf_rmse),
                'r2': float(rf_r2)
            },
            'lr': {
                'mae': float(lr_mae),
                'rmse': float(lr_rmse),
                'r2': float(lr_r2)
            }
        },
        'test_evaluation': eval_data,
        'last_trained': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    }
    
    # Create models directory if not exists
    os.makedirs(models_dir, exist_ok=True)
    model_path = os.path.join(models_dir, f"{ticker_symbol}_model.joblib")
    
    # Save using joblib
    joblib.dump(model_package, model_path)
    print(f"Model successfully saved to {model_path}")
    
    return model_package
