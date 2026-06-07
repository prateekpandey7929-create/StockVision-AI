from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from database.models import db, User, Prediction, Watchlist, ContactMessage
from ml.predictor import StockPredictor
import yfinance as yf
from datetime import datetime
import pandas as pd

main_bp = Blueprint('main', __name__)

def fetch_market_indices():
    """
    Helper to fetch major market index summaries for dashboard.
    """
    indices = {
        'S&P 500': '^GSPC',
        'Dow Jones': '^DJI',
        'NASDAQ': '^IXIC',
        'NIFTY 50': '^NSEI'
    }
    data = {}
    try:
        # Fetching basic info
        for name, sym in indices.items():
            ticker = yf.Ticker(sym)
            # Fetch 2 days of history to calculate change
            hist = ticker.history(period='2d')
            if not hist.empty and len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = current_price - prev_price
                pct_change = (change / prev_price) * 100.0
                data[name] = {
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'pct_change': round(pct_change, 2),
                    'symbol': sym
                }
            elif not hist.empty:
                current_price = hist['Close'].iloc[-1]
                data[name] = {
                    'price': round(current_price, 2),
                    'change': 0.0,
                    'pct_change': 0.0,
                    'symbol': sym
                }
            else:
                data[name] = {'price': 'N/A', 'change': 0.0, 'pct_change': 0.0, 'symbol': sym}
    except Exception as e:
        print(f"Error fetching market summary: {e}")
        # Default fallbacks if offline or rate-limited
        for name, sym in indices.items():
            data[name] = {'price': 'Service Unavailable', 'change': 0.0, 'pct_change': 0.0, 'symbol': sym}
    return data

@main_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # 1. Market Summary
    market_data = fetch_market_indices()
    
    # 2. Watchlist details (fetch real-time prices for watchlist stocks)
    watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
    watchlist_data = []
    
    for item in watchlist_items:
        try:
            ticker = yf.Ticker(item.stock_symbol)
            # Try to get 1 day info
            hist = ticker.history(period='1d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                # Try to get open price to calculate today's change
                open_price = hist['Open'].iloc[-1]
                change = current_price - open_price
                pct_change = (change / open_price) * 100.0 if open_price > 0 else 0.0
                watchlist_data.append({
                    'symbol': item.stock_symbol,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'pct_change': round(pct_change, 2)
                })
            else:
                watchlist_data.append({
                    'symbol': item.stock_symbol,
                    'price': 'N/A',
                    'change': 0.0,
                    'pct_change': 0.0
                })
        except Exception:
            watchlist_data.append({
                'symbol': item.stock_symbol,
                'price': 'Error',
                'change': 0.0,
                'pct_change': 0.0
            })
            
    # 3. Recent Predictions (last 5 predictions of this user)
    recent_predictions = Prediction.query.filter_by(user_id=current_user.id).order_by(Prediction.prediction_date.desc()).limit(5).all()
    
    # 4. Trending stocks (hardcoded top tickers for easy quick-access search)
    trending_symbols = ['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'META', 'AMZN', 'NFLX', 'RELIANCE.NS', 'TCS.NS', 'INFY.NS']
    trending_data = []
    
    # Fetch price for first 4 trending stocks to keep it quick
    for sym in trending_symbols[:4]:
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period='1d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                trending_data.append({
                    'symbol': sym,
                    'price': round(current_price, 2)
                })
        except Exception:
            trending_data.append({'symbol': sym, 'price': 'N/A'})
            
    # Add rest without fetching to save API load time
    for sym in trending_symbols[4:]:
        trending_data.append({'symbol': sym, 'price': 'View Info'})

    return render_template('dashboard.html', 
                           market_data=market_data, 
                           watchlist=watchlist_data,
                           recent_predictions=recent_predictions,
                           trending_stocks=trending_data)

@main_bp.route('/search', methods=['GET'])
@login_required
def search():
    symbol = request.args.get('symbol', '').strip().upper()
    if not symbol:
        flash('Please enter a stock symbol to search.', 'warning')
        return redirect(url_for('main.dashboard'))
        
    try:
        ticker = yf.Ticker(symbol)
        # Fetch latest info
        # yfinance info can be slow, history(1d) is much faster and more reliable
        hist = ticker.history(period='1d')
        if hist.empty:
            flash(f"Stock symbol '{symbol}' not found or no historical data available.", 'danger')
            return redirect(url_for('main.dashboard'))
            
        current_price = hist['Close'].iloc[-1]
        open_price = hist['Open'].iloc[-1]
        high_price = hist['High'].iloc[-1]
        low_price = hist['Low'].iloc[-1]
        volume = hist['Volume'].iloc[-1]
        
        # Try to get market cap from ticker info (fallback if missing)
        try:
            info = ticker.info
            market_cap = info.get('marketCap', 'N/A')
            company_name = info.get('longName', symbol)
        except Exception:
            market_cap = 'N/A'
            company_name = symbol
            
        if isinstance(market_cap, int):
            if market_cap >= 1e12:
                market_cap = f"${market_cap / 1e12:.2f} T"
            elif market_cap >= 1e9:
                market_cap = f"${market_cap / 1e9:.2f} B"
            elif market_cap >= 1e6:
                market_cap = f"${market_cap / 1e6:.2f} M"
        
        # Check if in watchlist
        in_watchlist = Watchlist.query.filter_by(user_id=current_user.id, stock_symbol=symbol).first() is not None
        
        stock_details = {
            'symbol': symbol,
            'name': company_name,
            'price': round(current_price, 2),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'volume': f"{volume:,}",
            'market_cap': market_cap,
            'in_watchlist': in_watchlist
        }
        
        return render_template('stock_detail.html', stock=stock_details)
        
    except Exception as e:
        flash(f"Error retrieving data for '{symbol}': {str(e)}", 'danger')
        return redirect(url_for('main.dashboard'))

@main_bp.route('/predict/<ticker>', methods=['GET'])
@login_required
def predict(ticker):
    ticker = ticker.upper()
    force_retrain = request.args.get('retrain', 'false').lower() == 'true'
    
    predictor = StockPredictor(current_app.config['MODELS_DIR'])
    
    try:
        # Get or train model & generate prediction
        pred_res = predictor.predict_next_day(ticker, force_retrain=force_retrain)
        
        # Save prediction to DB history
        prediction_record = Prediction(
            user_id=current_user.id,
            stock_symbol=ticker,
            current_price=pred_res['current_price'],
            predicted_price=pred_res['predicted_price'],
            signal=pred_res['signal'],
            confidence_score=pred_res['confidence_score']
        )
        db.session.add(prediction_record)
        db.session.commit()
        
        # Fetch stock basic info for detail header
        t_info = yf.Ticker(ticker)
        try:
            company_name = t_info.info.get('longName', ticker)
        except Exception:
            company_name = ticker
            
        in_watchlist = Watchlist.query.filter_by(user_id=current_user.id, stock_symbol=ticker).first() is not None
        
        stock_details = {
            'symbol': ticker,
            'name': company_name,
            'price': pred_res['current_price'],
            'in_watchlist': in_watchlist
        }
        
        return render_template('stock_detail.html', 
                               stock=stock_details, 
                               prediction=pred_res, 
                               show_prediction=True)
                               
    except Exception as e:
        flash(f"Machine learning training/prediction failed for '{ticker}': {str(e)}", 'danger')
        return redirect(url_for('main.search', symbol=ticker))

@main_bp.route('/api/historical/<ticker>')
@login_required
def api_historical(ticker):
    ticker = ticker.upper()
    period = request.args.get('period', '1m').lower()
    
    if period not in ['1m', '3m', '6m', '1y', '5y']:
        period = '1m'
        
    # Map frontend period to yfinance period
    yf_period_map = {
        '1m': '1mo',
        '3m': '3mo',
        '6m': '6mo',
        '1y': '1y',
        '5y': '5y'
    }
    yf_period = yf_period_map.get(period, '1mo')
        
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=yf_period)
        if hist.empty:
            return jsonify({'error': 'No historical data found'}), 400
            
        dates = hist.index.strftime('%Y-%m-%d').tolist()
        prices = [round(val, 2) for val in hist['Close'].tolist()]
        
        return jsonify({
            'ticker': ticker,
            'period': period,
            'dates': dates,
            'prices': prices
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/watchlist/add/<ticker>', methods=['POST'])
@login_required
def add_watchlist(ticker):
    ticker = ticker.upper()
    
    # Check if already in watchlist
    existing = Watchlist.query.filter_by(user_id=current_user.id, stock_symbol=ticker).first()
    if not existing:
        try:
            # Validate it's a real ticker first
            t = yf.Ticker(ticker)
            h = t.history(period='1d')
            if h.empty:
                flash(f"Invalid ticker symbol '{ticker}'", 'danger')
                return redirect(request.referrer or url_for('main.dashboard'))
                
            item = Watchlist(user_id=current_user.id, stock_symbol=ticker)
            db.session.add(item)
            db.session.commit()
            flash(f"Added {ticker} to your watchlist.", 'success')
        except Exception as e:
            flash(f"Could not add {ticker}: {str(e)}", 'danger')
    else:
        flash(f"{ticker} is already in your watchlist.", 'info')
        
    return redirect(request.referrer or url_for('main.dashboard'))

@main_bp.route('/watchlist/remove/<ticker>', methods=['POST'])
@login_required
def remove_watchlist(ticker):
    ticker = ticker.upper()
    item = Watchlist.query.filter_by(user_id=current_user.id, stock_symbol=ticker).first()
    if item:
        db.session.delete(item)
        db.session.commit()
        flash(f"Removed {ticker} from your watchlist.", 'success')
    else:
        flash(f"{ticker} was not in your watchlist.", 'warning')
        
    return redirect(request.referrer or url_for('main.dashboard'))

@main_bp.route('/watchlist')
@login_required
def watchlist():
    watchlist_items = Watchlist.query.filter_by(user_id=current_user.id).all()
    watchlist_data = []
    
    for item in watchlist_items:
        try:
            ticker = yf.Ticker(item.stock_symbol)
            hist = ticker.history(period='1d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                open_price = hist['Open'].iloc[-1]
                change = current_price - open_price
                pct_change = (change / open_price) * 100.0 if open_price > 0 else 0.0
                
                try:
                    name = ticker.info.get('longName', item.stock_symbol)
                except Exception:
                    name = item.stock_symbol
                    
                watchlist_data.append({
                    'symbol': item.stock_symbol,
                    'name': name,
                    'price': round(current_price, 2),
                    'change': round(change, 2),
                    'pct_change': round(pct_change, 2)
                })
            else:
                watchlist_data.append({
                    'symbol': item.stock_symbol,
                    'name': item.stock_symbol,
                    'price': 'N/A',
                    'change': 0.0,
                    'pct_change': 0.0
                })
        except Exception:
            watchlist_data.append({
                'symbol': item.stock_symbol,
                'name': item.stock_symbol,
                'price': 'Error',
                'change': 0.0,
                'pct_change': 0.0
            })
            
    return render_template('watchlist.html', watchlist=watchlist_data)

@main_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    search_q = request.args.get('search', '').strip().upper()
    signal_filter = request.args.get('signal', '')
    
    query = Prediction.query.filter_by(user_id=current_user.id)
    
    if search_q:
        query = query.filter(Prediction.stock_symbol.like(f"%{search_q}%"))
        
    if signal_filter in ['Bullish', 'Bearish']:
        query = query.filter(Prediction.signal == signal_filter)
        
    # Paginate predictions (10 per page)
    pagination = query.order_by(Prediction.prediction_date.desc()).paginate(page=page, per_page=10, error_out=False)
    predictions = pagination.items
    
    return render_template('history.html', 
                           predictions=predictions, 
                           pagination=pagination,
                           search=search_q,
                           signal_filter=signal_filter)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not name or not email or not subject or not message:
            flash('All contact fields are required.', 'danger')
            return render_template('contact.html')
            
        msg = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(msg)
        db.session.commit()
        
        flash('Thank you for your message! Our team will get back to you shortly.', 'success')
        return redirect(url_for('main.landing') if not current_user.is_authenticated else redirect(url_for('main.dashboard')))
        
    return render_template('contact.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')
