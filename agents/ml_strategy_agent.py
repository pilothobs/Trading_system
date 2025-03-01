import os
# Disable GPU usage
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score
import tensorflow as tf
from typing import List, Dict, Tuple
import warnings
import traceback
warnings.filterwarnings('ignore')  # Suppress warnings for cleaner output

class MLStrategyAgent:
    def __init__(self):
        self.model = None
        self.timeframes = ['5min', '15min', '1H', '4H', 'D']
        self.indicators = {
            'Trend': {
                'SMA': [20, 50, 200],
                'EMA': [9, 21, 55],
                'MACD': [(12,26,9)],
            },
            'Momentum': {
                'RSI': [14, 21],
                'Stochastic': [(14,3)],
            },
            'Volatility': {
                'BB': [(20,2)],
                'ATR': [14],
            }
        }
        # Force TensorFlow to use CPU
        self.strategy = tf.distribute.get_strategy()
    
    def resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """Resample data to different timeframes"""
        try:
            if timeframe == '1H':
                return df
            
            # Convert timeframe string to pandas offset
            timeframe_map = {
                '5min': '5T',
                '15min': '15T',
                '4H': '4H',
                'D': 'D'
            }
            offset = timeframe_map.get(timeframe)
            if not offset:
                print(f"Invalid timeframe: {timeframe}")
                return df
            
            # Resample with proper aggregation methods
            resampled = df.resample(offset).agg({
                'open': lambda x: x.iloc[0],
                'high': 'max',
                'low': 'min',
                'close': lambda x: x.iloc[-1],
                'volume': 'sum'
            })
            
            return resampled.dropna()
        
        except Exception as e:
            print(f"Error in resample_data: {e}")
            traceback.print_exc()
            return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate indicators for multiple timeframes"""
        try:
            # Create DataFrame for all features
            all_features = pd.DataFrame(index=df.index)
            
            # Calculate base timeframe indicators first
            print("\nCalculating base indicators...")
            all_features['SMA_20'] = df['close'].rolling(window=20).mean()
            all_features['SMA_50'] = df['close'].rolling(window=50).mean()
            all_features['SMA_200'] = df['close'].rolling(window=200).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            all_features['RSI'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            all_features['BB_middle'] = df['close'].rolling(window=20).mean()
            all_features['BB_std'] = df['close'].rolling(window=20).std()
            all_features['BB_upper'] = all_features['BB_middle'] + (all_features['BB_std'] * 2)
            all_features['BB_lower'] = all_features['BB_middle'] - (all_features['BB_std'] * 2)
            
            # Add original OHLCV data
            for col in ['open', 'high', 'low', 'close', 'volume']:
                all_features[col] = df[col]
            
            print(f"Calculated {len(all_features.columns)} indicators")
            return all_features.dropna()
        
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            traceback.print_exc()
            return df
    
    def find_best_features(self, X: np.ndarray, y: np.ndarray, feature_names: List[str]) -> List[str]:
        """Find most predictive features using Random Forest"""
        rf = RandomForestClassifier(n_estimators=100, random_state=42)
        rf.fit(X, y)
        
        # Get feature importance
        importance = dict(zip(feature_names, rf.feature_importances_))
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        
        # Print top features
        print("\nTop 10 Most Important Indicators:")
        for feat, imp in sorted_features[:10]:
            print(f"{feat}: {imp:.4f}")
        
        # Return top 20 feature names
        return [feat for feat, _ in sorted_features[:20]]
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Prepare features for ML model"""
        try:
            print("\nPreparing features...")
            print(f"Initial data shape: {df.shape}")
            
            # Drop NaN values from indicator calculations
            df_clean = df.dropna()
            print(f"Shape after dropping NaN: {df_clean.shape}")
            
            # Create target: 1 if price goes up in next n periods, 0 if down
            look_ahead = 5  # Predict 5 periods ahead
            df_clean['target'] = (df_clean['close'].shift(-look_ahead) > df_clean['close']).astype(int)
            
            # Select features (all numeric columns except target)
            feature_cols = df_clean.select_dtypes(include=[np.number]).columns
            feature_cols = [col for col in feature_cols 
                           if col not in ['target', 'signal', 'volume']]
            
            print(f"\nSelected features: {len(feature_cols)}")
            print("Sample features:", feature_cols[:5])
            
            # Remove last look_ahead rows where target is NaN
            X = df_clean[feature_cols].iloc[:-look_ahead].values
            y = df_clean['target'].iloc[:-look_ahead].values
            
            print(f"\nFinal shapes - X: {X.shape}, y: {y.shape}")
            
            if len(X) == 0:
                raise ValueError("No valid samples after feature preparation!")
            
            return X, y, feature_cols
        
        except Exception as e:
            print(f"\nError in prepare_features: {e}")
            traceback.print_exc()
            # Return minimal valid data to prevent downstream errors
            return np.array([[0]*5]), np.array([0]), ['dummy_feature']
    
    def train_model(self, X: np.ndarray, y: np.ndarray):
        """Train a deep learning model"""
        try:
            print(f"\nTraining model on {len(X)} samples...")
            
            if len(X) < 10:  # Arbitrary minimum sample size
                print("Not enough samples for training!")
                return
            
            # Simple model for testing
            model = tf.keras.Sequential([
                tf.keras.layers.Dense(32, activation='relu', input_shape=(X.shape[1],)),
                tf.keras.layers.Dense(16, activation='relu'),
                tf.keras.layers.Dense(1, activation='sigmoid')
            ])
            
            model.compile(optimizer='adam',
                         loss='binary_crossentropy',
                         metrics=['accuracy'])
            
            # Use smaller number of splits for TimeSeriesSplit
            n_splits = min(5, len(X) // 10)  # Ensure we have enough samples per split
            tscv = TimeSeriesSplit(n_splits=n_splits)
            
            print("\nTraining progress:")
            for i, (train_idx, val_idx) in enumerate(tscv.split(X)):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                print(f"\nFold {i+1}/{n_splits}")
                print(f"Train samples: {len(X_train)}, Validation samples: {len(X_val)}")
                
                model.fit(X_train, y_train,
                         epochs=10,  # Reduced epochs for testing
                         batch_size=32,
                         validation_data=(X_val, y_val),
                         verbose=0)
                
                # Evaluate on validation set
                val_loss, val_acc = model.evaluate(X_val, y_val, verbose=0)
                print(f"Validation accuracy: {val_acc:.2%}")
            
            self.model = model
            print("\nModel training completed")
        
        except Exception as e:
            print(f"\nError in train_model: {e}")
            traceback.print_exc() 

    def analyze_market(self, df: pd.DataFrame) -> Dict:
        """Analyze market and generate signals"""
        try:
            signals = []
            
            # Calculate basic indicators
            df = self.calculate_indicators(df)
            
            # Generate signals
            for i in range(1, len(df)):
                if df['RSI'].iloc[i] < 30 and df['close'].iloc[i] > df['SMA_50'].iloc[i]:
                    signals.append({
                        'timestamp': df.index[i],
                        'type': 'BUY',
                        'price': df['close'].iloc[i],
                        'reason': 'RSI oversold + Above SMA50'
                    })
                elif df['RSI'].iloc[i] > 70 and df['close'].iloc[i] < df['SMA_50'].iloc[i]:
                    signals.append({
                        'timestamp': df.index[i],
                        'type': 'SELL',
                        'price': df['close'].iloc[i],
                        'reason': 'RSI overbought + Below SMA50'
                    })
            
            return {
                'signals': signals,
                'indicators': df.columns.tolist()
            }
            
        except Exception as e:
            print(f"Error in analyze_market: {e}")
            traceback.print_exc()
            return {'signals': [], 'indicators': []} 