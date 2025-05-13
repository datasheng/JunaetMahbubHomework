import mysql.connector
from mysql.connector import Error
import pandas as pd
from datetime import datetime, timedelta

class RDSDataAccess:
    def __init__(self, host, user, password, port=3306):
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'port': port,
            'database': None  # Set per ticker/service
        }
        self.service_dbs = {
            'SPOT': 'spotify_service',
            'SIRI': 'siriusxm_service'
        }

    def _get_connection(self, ticker):
        """Create DB connection for specific service"""
        if ticker not in self.service_dbs:
            raise ValueError(f"Invalid ticker. Choose from: {list(self.service_dbs.keys())}")
        self.config['database'] = self.service_dbs[ticker]
        try:
            return mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error connecting to DB '{self.config['database']}': {e}")
            return None

    def get_all_data(self, ticker):
        """Get all data for ticker"""
        connection = self._get_connection(ticker)
        if connection is None:
            return None
        try:
            query = """
            SELECT ticker, date, open, high, low, close, volume 
            FROM stock_data 
            WHERE ticker = %s
            ORDER BY date DESC
            """
            df = pd.read_sql(query, connection, params=(ticker,))
            df['date'] = pd.to_datetime(df['date'])
            return df.set_index('date')
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()

    def get_data_by_date_range(self, ticker, start_date, end_date):
        """Get data in date range"""
        connection = self._get_connection(ticker)
        if connection is None:
            return None
        try:
            query = """
            SELECT ticker, date, open, high, low, close, volume 
            FROM stock_data 
            WHERE ticker = %s AND date BETWEEN %s AND %s
            ORDER BY date ASC
            """
            df = pd.read_sql(query, connection, params=(ticker, start_date, end_date))
            df['date'] = pd.to_datetime(df['date'])
            return df.set_index('date')
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()

    def get_latest_records(self, ticker, days=30):
        """Get recent data"""
        connection = self._get_connection(ticker)
        if connection is None:
            return None
        try:
            query = """
            SELECT ticker, date, open, high, low, close, volume 
            FROM stock_data 
            WHERE ticker = %s
            ORDER BY date DESC 
            LIMIT %s
            """
            df = pd.read_sql(query, connection, params=(ticker, days))
            df['date'] = pd.to_datetime(df['date'])
            return df.set_index('date')
        except Error as e:
            print(f"Error fetching data: {e}")
            return None
        finally:
            if connection.is_connected():
                connection.close()

    def compare_services(self, start_date, end_date):
        """Compare Spotify vs SiriusXM"""
        comparison_data = {}
        for ticker in ['SPOT', 'SIRI']:
            df = self.get_data_by_date_range(ticker, start_date, end_date)
            if df is not None:
                comparison_data[ticker] = df['close']

        if len(comparison_data) == 2:
            comparison_df = pd.DataFrame(comparison_data)
            comparison_df = comparison_df.sort_index()
            # Normalize
            comparison_df['SPOT_Norm'] = comparison_df['SPOT'] / comparison_df['SPOT'].iloc[0] * 100
            comparison_df['SIRI_Norm'] = comparison_df['SIRI'] / comparison_df['SIRI'].iloc[0] * 100
            return comparison_df
        return None


if __name__ == "__main__":
    RDS_CONFIG = {
        'host': 'spotifyvssiriusxm.cevge02u6cv8.us-east-1.rds.amazonaws.com',
        'user': 'admin',
        'password': 'Jdawg123',
        'port': 3306
    }

    data_access = RDSDataAccess(**RDS_CONFIG)

    try:
        spot_data = data_access.get_latest_records('SPOT')
        print("Latest Spotify Data:")
        print(spot_data.head())

        end_date = datetime.today().date()
        start_date = end_date - timedelta(days=180)

        comparison_df = data_access.compare_services(start_date, end_date)
        if comparison_df is not None:
            print("\nPerformance Comparison:")
            print(comparison_df[['SPOT_Norm', 'SIRI_Norm']].tail())

            correlation = comparison_df['SPOT_Norm'].corr(comparison_df['SIRI_Norm'])
            print(f"\nCorrelation: {correlation:.2%}")

    except Exception as e:
        print(f"Error: {e}")
