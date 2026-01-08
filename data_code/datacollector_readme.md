wh# 📚 FINANCIAL ANALYSIS SYSTEM - SETUP GUIDE
# ==========================================
# Complete Beginner's Guide to Automated Financial Analysis

## 🎯 WHAT THIS SYSTEM DOES
- Type any company name (e.g., "Infosys")
- Automatically finds NSE symbol (INFY)
- Scrapes 10+ financial metrics from Screener.in
- Cleans and processes data automatically
- Saves to database and Power BI format
- Ready for dashboard creation

## 🚀 ONE-STEP SETUP

### 1. Install Required Packages
```bash
pip install requests pandas beautifulsoup4 lxml
```

### 2. Run the System
```bash
python financial_analyzer.py
```

### 3. That's It! Just type company names when prompted.

## 📊 AVAILABLE METRICS

### Current Ratios
- **ROE (Return on Equity)**: Profitability for shareholders
- **ROCE (Return on Capital Employed)**: Overall efficiency
- **Debt to Equity**: Financial leverage
- **Interest Coverage**: Ability to pay interest
- **Operating Margin**: Operational profitability
- **P/E Ratio**: Valuation metric
- **Operating Cash Flow**: Cash generation

### Growth Metrics (5-Year)
- **Sales Growth**: Revenue growth rate
- **Profit Growth**: Profit growth rate
- **EPS Growth**: Earnings per share growth

## 📁 AUTOMATIC FOLDER STRUCTURE
```
finova/
├── financial_analyzer.py          # Main system
├── data/
│   ├── financial_data.db         # SQLite database
│   ├── powerbi/                  # Power BI files
│   ├── raw/                      # Raw scraped data
│   └── processed/                # Cleaned data
├── logs/
│   └── system.log                # Activity logs
└── modules/                      # Individual components
```

## 💻 POWER BI INTEGRATION

### Step 1: Connect to Data
1. Open Power BI Desktop
2. Click "Get Data" → "CSV/Text"
3. Select: `data/powerbi/latest_financial_data.csv`

### Step 2: Create Dashboard
1. **ROE & ROCE Card**: Add ROE_Percent and ROCE_Percent as cards
2. **Growth Chart**: Line chart with Sales_Growth_5Y_Percent
3. **Valuation**: PE_Ratio as gauge chart
4. **Company Filter**: Slicer on Company_Name

### Step 3: Auto-Refresh Setup
1. In Power BI, go to "Transform Data"
2. Set refresh interval (e.g., every 1 hour)
3. Publish to Power BI Service for web access

## 🎮 HOW TO USE

### Basic Usage
```bash
python financial_analyzer.py
```
Then type:
- `Infosys` → Gets INFY data
- `TCS` → Gets TCS data  
- `Reliance` → Gets RELIANCE data

### View Database
Type `view` to see all analyzed companies

### Commands
- Any company name → Analyze that company
- `view` → Show database summary
- `quit` → Exit system

## 🔧 TROUBLESHOOTING

### Common Issues & Solutions

#### ❌ "NSE Symbol not found"
**Cause**: Company not listed or name mismatch
**Solution**: 
- Try full name: "Infosys Limited"
- Try abbreviation: "INFY"
- Check if company is listed on NSE

#### ❌ "Could not scrape financial data"
**Cause**: Website blocked or server down
**Solution**: 
- Wait and try again
- Check internet connection
- Try different company

#### ❌ "Power BI shows no data"
**Cause**: Wrong file path or empty data
**Solution**: 
- Check `data/powerbi/latest_financial_data.csv`
- Ensure file has data
- Refresh Power BI connection

#### ❌ "Import errors"
**Cause**: Missing packages
**Solution**: 
```bash
pip install requests pandas beautifulsoup4 lxml
```

## 📈 SAMPLE OUTPUT

When you analyze "Infosys", you get:
```
🎉 ANALYSIS COMPLETED SUCCESSFULLY!
Company: Infosys Limited (INFY)
ROE: 25.8%
ROCE: 32.1%
P/E Ratio: 28.5
Sales Growth (5Y): 12.3%
Power BI Data: data/powerbi/financial_data_INFY_20240105_160000.csv
```

## 🔄 AUTOMATION WORKFLOW

1. **Input**: User types company name
2. **Symbol Detection**: Yahoo Finance → Screener.in
3. **Data Scraping**: Screener.in financial tables
4. **Data Cleaning**: Remove %, commas, validate ranges
5. **Storage**: SQLite database + CSV export
6. **Power BI**: Auto-refresh dashboard

## 🎯 POWER BI DASHBOARD IDEAS

### Layout 1: Company Overview
- Company Name & Logo
- Current Price & P/E Ratio
- ROE & ROCE (Big numbers)
- Quick ratios table

### Layout 2: Performance Analysis
- Sales & Profit Growth charts
- EPS trend line
- Margin analysis
- Debt position

### Layout 3: Comparison View
- Multiple companies comparison
- Industry averages
- Ranking tables
- Trend comparisons

## 📞 SUPPORT

### System Requirements
- Python 3.7+
- Internet connection
- 2GB RAM minimum
- 100MB disk space

### Performance Tips
- Analyze one company at a time
- System adds delays to avoid blocking
- Database stores all historical data

### Data Updates
- Real-time scraping from Screener.in
- Historical data stored in database
- Power BI auto-refresh capability

## 🚀 NEXT STEPS

1. **Run First Analysis**: `python financial_analyzer.py`
2. **Create Power BI Dashboard**: Connect to CSV file
3. **Set Auto-Refresh**: Configure Power BI refresh
4. **Analyze Multiple Companies**: Build your database
5. **Create Web Dashboard**: Publish Power BI to web

## 💡 PRO TIPS

- **Best Time to Run**: Market hours (9 AM - 4 PM IST)
- **Frequency**: Update data weekly for best results
- **Storage**: Database grows slowly, minimal space needed
- **Backup**: Copy `data/financial_data.db` regularly

---

🎉 **CONGRATULATIONS!** You now have a complete automated financial analysis system!

Just run `python financial_analyzer.py` and start analyzing any Indian company!
