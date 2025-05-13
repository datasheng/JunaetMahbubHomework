# Stock Data Analysis Project

This project analyzes and compares stock data between Spotify (SPOT) and SiriusXM (SIRI) using AWS RDS, Alpha Vantage API, and Python.

## 📂 Repository Structure
JunaetMahbubHomework/
├── comparison.py # Main analysis & database upload script
├── database_access.py # Database query interface
├── umlDiagrams.py # Generates UML/Data Flow diagrams
├── requirements.txt # Python dependencies
├── .env.example # Configuration template
└── README.md # Usage guide


## 🛠️ Prerequisites
1. Python 3.8+
2. AWS RDS MySQL instance
3. [Alpha Vantage API Key](https://www.alphavantage.co/)
4. Install dependencies:
```bash
pip install mysql-connector-python pandas matplotlib requests python-dotenv

## Configuration
Environment File (rename .env.example to .env):

ini
ALPHA_VANTAGE_API_KEY="YOUR_API_KEY"
RDS_HOST="your-rds-endpoint.region.rds.amazonaws.com"
RDS_USER="admin"
RDS_PASSWORD="Jdawg123"
RDS_PORT=3306


