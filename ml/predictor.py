import os
import joblib
from datetime import datetime, timedelta
import pandas as pd
from ml.train_model import train_ticker_model

class StockPredictor:
    def __init__(self, models_dir):
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)
        
    def get_model_path(self, ticker):
        return os.path.join(self.models_dir, f"{ticker.upper()}_model.joblib")
        
    def is_model_fresh(self, ticker):
        model_path = self.get_model_path(ticker)
        if not os.path.exists(model_path):
            return False
            
        try:
            # Check modification time of file
            mtime = datetime.fromtimestamp(os.path.getmtime(model_path))
            # If less than 24 hours old, we consider it fresh
            return datetime.now() - mtime < timedelta(hours=24)
        except Exception:
            return False
            
    def get_or_train_model(self, ticker, force_retrain=False):
        """
        Retrieves the model package for a ticker. Trains it if it doesn't exist,
        is stale, or if force_retrain is True.
        """
        ticker = ticker.upper()
        model_path = self.get_model_path(ticker)
        
        if force_retrain or not self.is_model_fresh(ticker):
            print(f"Model for {ticker} is missing or stale. Triggering training...")
            try:
                # This will download data and save the model
                model_package = train_ticker_model(ticker, self.models_dir)
                return model_package, True # Returns package and True (retrained)
            except Exception as e:
                # If training failed, check if we have a stale model we can fallback to
                if os.path.exists(model_path):
                    print(f"Training failed ({e}). Falling back to stale model.")
                    return joblib.load(model_path), False
                raise e
        else:
            print(f"Loading existing fresh model for {ticker}")
            return joblib.load(model_path), False
            
    def predict_next_day(self, ticker, force_retrain=False):
        """
        Predicts next day's price for a ticker and returns structured metrics.
        """
        ticker = ticker.upper()
        model_package, retrained = self.get_or_train_model(ticker, force_retrain)
        
        # Extract components
        rf_model = model_package['rf_model']
        latest_features_dict = model_package['latest_features']
        last_price = model_package['last_price']
        features = model_package['features']
        metrics = model_package['metrics']
        test_eval = model_package['test_evaluation']
        last_trained = model_package['last_trained']
        
        # Construct DataFrame for prediction
        features_df = pd.DataFrame([latest_features_dict])[features]
        
        # Generate prediction
        predicted_price_rf = float(rf_model.predict(features_df)[0])
        
        # Calculate changes
        price_diff = predicted_price_rf - last_price
        pct_change = (price_diff / last_price) * 100.0
        
        # Determine signals
        signal = "Bullish" if pct_change > 0 else "Bearish"
        
        # Dynamic Confidence Score based on Model MAE (Mean Absolute Percentage Error estimated)
        rf_mae = metrics['rf']['mae']
        mape = (rf_mae / last_price) * 100.0
        confidence = 100.0 - (mape * 2.0)  # Penalize confidence by 2x the average percentage error
        confidence = max(50.0, min(99.0, confidence))  # Keep it in a logical 50%-99% bound
        
        # Prediction Date (Tomorrow or next trading day - simple estimate is tomorrow)
        # However, if it's Friday, next trading day is Monday
        today = datetime.now()
        if today.weekday() == 4: # Friday
            pred_date = today + timedelta(days=3)
        elif today.weekday() == 5: # Saturday
            pred_date = today + timedelta(days=2)
        else:
            pred_date = today + timedelta(days=1)
            
        prediction_date_str = pred_date.strftime('%Y-%m-%d')
        
        return {
            'ticker': ticker,
            'current_price': round(last_price, 2),
            'predicted_price': round(predicted_price_rf, 2),
            'expected_change_pct': round(pct_change, 2),
            'signal': signal,
            'confidence_score': round(confidence, 1),
            'prediction_date': prediction_date_str,
            'metrics': metrics,
            'test_evaluation': test_eval,
            'last_trained': last_trained,
            'retrained': retrained
        }
