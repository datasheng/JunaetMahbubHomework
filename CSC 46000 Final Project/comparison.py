import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import mysql.connector
from mysql.connector import Error
import os

def get_stock_data(ticker, api_key, months_back=86):
    """Fetch and process historical stock data from Alpha Vantage"""
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30*months_back)
    
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={api_key}&outputsize=full"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if "Time Series (Daily)" not in data:
            print(f"Error in {ticker} response structure")
            return None

        df = pd.DataFrame(data["Time Series (Daily)"]).T
        df.index = pd.to_datetime(df.index)
        df = df.sort_index(ascending=True)
        
        mask = (df.index >= start_date) & (df.index <= end_date)
        df = df.loc[mask]
        
        column_map = {
            "1. open": "Open",
            "2. high": "High",
            "3. low": "Low",
            "4. close": "Close",
            "5. volume": "Volume"
        }
        
        df = df.rename(columns=column_map)[list(column_map.values())]
        df = df.astype(float)
        df['Ticker'] = ticker
        return df

    except Exception as e:
        print(f"Error fetching {ticker}: {str(e)}")
        return None

def upload_to_rds_per_service(df, ticker, host, user, password, port=3306):
    """Upload DataFrame to AWS RDS with 2NF structure"""
    ticker_db_map = {'SPOT': 'spotify_service', 'SIRI': 'siriusxm_service'}
    database = ticker_db_map.get(ticker)
    
    if not database:
        print(f"No database mapped for ticker {ticker}")
        return
    
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )

        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create 2NF-compliant tables if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock_data (
                    ticker VARCHAR(10) NOT NULL,
                    date DATE NOT NULL,
                    open NUMERIC(10,4),
                    high NUMERIC(10,4),
                    low NUMERIC(10,4),
                    close NUMERIC(10,4),
                    volume BIGINT,
                    PRIMARY KEY (ticker, date)
                )""")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS comparison_metrics (
                    comparison_id INT AUTO_INCREMENT PRIMARY KEY,
                    comparison_date DATE NOT NULL,
                    ticker1 VARCHAR(10) NOT NULL,
                    ticker2 VARCHAR(10) NOT NULL,
                    correlation NUMERIC(5,4),
                    volatility1 NUMERIC(5,4),
                    volatility2 NUMERIC(5,4),
                    return1 NUMERIC(5,2),
                    return2 NUMERIC(5,2),
                    UNIQUE (comparison_date, ticker1, ticker2)
                )""")

            # Upsert stock data
            for index, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO stock_data 
                    (ticker, date, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        open=VALUES(open),
                        high=VALUES(high),
                        low=VALUES(low),
                        close=VALUES(close),
                        volume=VALUES(volume)
                    """, (
                        row['Ticker'],
                        index.date(),
                        row['Open'],
                        row['High'],
                        row['Low'],
                        row['Close'],
                        int(row['Volume'])
                    ))
            
            connection.commit()
            print(f"Uploaded {len(df)} records to {database}.stock_data")

    except Error as e:
        print(f"Database error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def save_comparison_metrics(metrics, ticker1, ticker2, host, user, password):
    """Save 2NF-compliant comparison metrics to database"""
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database='spotify_service',  # Store comparisons in one service DB
            port=3306
        )
        
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO comparison_metrics 
            (comparison_date, ticker1, ticker2, correlation, 
             volatility1, volatility2, return1, return2)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.today().date(),
                ticker1,
                ticker2,
                metrics['correlation'],
                metrics['spot_volatility'],
                metrics['siri_volatility'],
                metrics['spot_return'],
                metrics['siri_return']
            ))
        connection.commit()
        print("Saved comparison metrics to database")
        
    except Error as e:
        print(f"Error saving metrics: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def compare_companies(df1, df2):
    """Generate analysis and return metrics for 2NF storage"""
    combined = pd.merge(df1[['Close']], df2[['Close']], 
                       left_index=True, right_index=True,
                       suffixes=('_SPOT', '_SIRI'))
    
    combined['SPOT_Norm'] = combined['Close_SPOT'] / combined['Close_SPOT'].iloc[0] * 100
    combined['SIRI_Norm'] = combined['Close_SIRI'] / combined['Close_SIRI'].iloc[0] * 100
    
    returns = combined[['Close_SPOT', 'Close_SIRI']].pct_change()
    corr = returns.corr().iloc[0,1]
    
    # Generate visualization
    plt.figure(figsize=(12, 6))
    plt.plot(combined.index, combined['SPOT_Norm'], label='Spotify (SPOT)')
    plt.plot(combined.index, combined['SIRI_Norm'], label='SiriusXM (SIRI)')
    plt.title('Normalized Price Performance Comparison (6 Months)')
    plt.ylabel('Normalized Price (Base=100)')
    plt.legend()
    plt.grid(True)
    plt.savefig('spot_vs_siri_performance.png')
    
    # Return metrics for database storage
    return {
        'correlation': corr,
        'spot_volatility': returns['Close_SPOT'].std(),
        'siri_volatility': returns['Close_SIRI'].std(),
        'spot_return': (combined['SPOT_Norm'][-1]-100),
        'siri_return': (combined['SIRI_Norm'][-1]-100),
        'combined_data': combined
    }

# Configuration
API_KEY = "9KFO5THXMSGNE40J"
TICKERS = ['SPOT', 'SIRI']
RDS_CONFIG = {
    'host': 'spotifyvssiriusxm.cevge02u6cv8.us-east-1.rds.amazonaws.com',
    'user': 'admin',
    'password': 'Jdawg123',
    'port': 3306
}

if __name__ == "__main__":
    dataframes = {}
    for ticker in TICKERS:
        df = get_stock_data(ticker, API_KEY)
        if df is not None:
            df.to_csv(f"{ticker}_stock_data_{datetime.today().strftime('%Y%m%d')}.csv")
            upload_to_rds_per_service(df, ticker, **RDS_CONFIG)
            dataframes[ticker] = df

    if len(dataframes) == 2:
        comparison_results = compare_companies(dataframes['SPOT'], dataframes['SIRI'])
        comparison_results['combined_data'].to_csv('SPOT_SIRI_comparison.csv')
        
        # Save metrics with 2NF compliance
        save_comparison_metrics(
            comparison_results,
            'SPOT',
            'SIRI',
            RDS_CONFIG['host'],
            RDS_CONFIG['user'],
            RDS_CONFIG['password']
        )
        
        print("\nLatest Comparison Metrics:")
        print(f"Correlation: {comparison_results['correlation']:.2%}")
        print(f"SPOT Return: {comparison_results['spot_return']:.2f}%")
        print(f"SIRI Return: {comparison_results['siri_return']:.2f}%")
    else:
        print("Data retrieval failed")