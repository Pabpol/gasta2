# Expense Management Backend

A unified backend system for managing expenses with automatic categorization, Telegram integration, and Excel reporting.

## 🚀 Features

- **Automatic Expense Processing**: Receives expenses from MacroDroid and other sources
- **Smart Categorization**: Uses merchant mapping, rule-based matching, and optional ML
- **Telegram Integration**: Interactive categorization and sharing decisions via Telegram bot
- **Shared Expense Tracking**: Handles expense sharing and automatic reconciliation
- **Excel Reporting**: Automatic sync with Excel for budgeting and analysis
- **RESTful API**: Complete API for expense management operations

## 📂 Project Structure

```
backend_gastos/
├── app.py                    # FastAPI main application
├── requirements.txt          # Python dependencies
├── start.sh                 # Startup script
├── create_sample_excel.py   # Excel file creation utility
├── merchant_map.csv         # Merchant-to-category mapping
├── config.yaml              # Configuration file
├── core/
│   ├── __init__.py
│   ├── paths.py             # Path configurations
│   ├── storage.py           # Data storage and Excel sync
│   ├── categorize.py        # Expense categorization logic
│   └── reconcile.py         # Income-expense reconciliation
├── integrations/
│   ├── __init__.py
│   └── messenger.py         # Telegram bot integration
├── data/                    # Runtime data directory
├── models/                  # Optional ML models
└── Presupuesto_Auto.xlsx    # Excel file for reporting
```

## 🔧 Setup

### 1. Clone and Navigate
```bash
cd backend_gastos
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Telegram Bot
```bash
# Set your Telegram bot token and chat ID
export TELEGRAM_BOT_TOKEN="your_bot_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"
```

### 4. Create Excel File (Optional)
```bash
python create_sample_excel.py
```

### 5. Start the Server
```bash
./start.sh
# or manually:
uvicorn app:app --reload --port 8000
```

## 📱 Telegram Setup

1. **Create a Telegram Bot**:
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Save the bot token

2. **Get Your Chat ID**:
   - Start a chat with your bot
   - Send a message
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your chat ID in the response

3. **Set Webhook** (for production):
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://YOUR_DOMAIN/telegram/webhook"
   ```

## 🔗 API Endpoints

### Core Endpoints

- `GET /` - Health check
- `POST /api/gasto` - Create new expense
- `GET /api/pendientes` - Get uncategorized expenses
- `POST /api/ingreso` - Record income/refund
- `GET /api/receivables` - Get shared expenses pending settlement
- `POST /api/reembolso/match` - Manually match income with expense
- `GET /api/stats` - Get system statistics

### Management Endpoints

- `POST /api/category/update` - Update expense category
- `POST /api/share/update` - Update expense sharing info
- `POST /telegram/webhook` - Telegram webhook handler

### Example Usage

**Create an Expense**:
```bash
curl -X POST "http://localhost:8000/api/gasto" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Almuerzo en Restaurant XYZ",
    "monto_clp": 15000,
    "medio": "TC"
  }'
```

**Record Income**:
```bash
curl -X POST "http://localhost:8000/api/ingreso" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Transferencia de Juan",
    "monto_clp": 7500,
    "contraparte": "Juan"
  }'
```

## 📊 Data Flow

1. **Expense Creation**: MacroDroid sends expense data
2. **Auto-Categorization**: System attempts to categorize using:
   - Merchant mapping (`merchant_map.csv`)
   - Rule-based matching (`config.yaml`)
   - ML model (optional)
3. **Telegram Interaction**: If categorization fails, Telegram bot prompts user
4. **Sharing Decision**: After categorization, system asks if expense was shared
5. **Excel Sync**: Data is synchronized to Excel with summaries
6. **Income Processing**: When income arrives, system attempts auto-matching
7. **Reconciliation**: Shared expenses are marked as settled when matched

## 🔧 Configuration

### Merchant Mapping (`merchant_map.csv`)
```csv
merchant,categoria,subcategoria
uber,transporte,rideshare
jumbo,supermercado,supermercado
netflix,servicios,suscripciones
```

### Rules Configuration (`config.yaml`)
```yaml
categorization_rules:
  transporte:
    keywords:
      - uber
      - taxi
      - metro
    subcategoria: transporte_publico
```

## 📈 Excel Integration

The system automatically maintains three Excel sheets:

1. **MOVIMIENTOS**: All transactions with full details
2. **RESUMEN_AUTO**: Net expenses by category (using `monto_tu_parte`)
3. **RESUMEN_CASHFLOW**: Monthly income/expense/net summary

## 🤖 Telegram Commands

### Automatic Prompts
- **Category Selection**: Choose from predefined categories
- **Sharing Questions**: Decide if expense was shared (No/50-50/Custom)

### Text Commands
- `id <expense_id> con <Name>` - Share 50/50 with someone
- `id <expense_id> con <Name> % <percentage>` - Custom sharing percentage

### Example Telegram Flow
1. 💳 New expense detected → Bot sends category buttons
2. 👆 User selects "Alimentación" → Bot asks about sharing
3. 👥 User clicks "50/50" → Bot asks for person's name
4. 💬 User types: `id abc123 con María` → System processes sharing

## 🔍 Reconciliation

The system automatically matches incoming payments with shared expenses using:

- **Amount Tolerance**: ±$1,000 CLP or ±5% for amounts >$100k
- **Date Window**: 10-day window around expense date
- **Name Matching**: Fuzzy matching of counterpart names
- **Confidence Scoring**: Weighted scoring for automatic decisions

## 🚨 Troubleshooting

### Common Issues

1. **Telegram not responding**:
   - Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
   - Verify bot has permission to send messages

2. **Excel not updating**:
   - Ensure `Presupuesto_Auto.xlsx` exists and is not open
   - Check file permissions

3. **Categorization not working**:
   - Review `merchant_map.csv` format
   - Check `config.yaml` syntax

### Logs
Check application logs for detailed error information:
```bash
# View real-time logs
tail -f logs/app.log

# Check for specific errors
grep "ERROR" logs/app.log
```

## 🔒 Security Notes

- Keep Telegram bot token secure
- Use HTTPS in production
- Consider rate limiting for API endpoints
- Regularly backup Excel files and data

## 📚 Dependencies

- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **pandas**: Data manipulation
- **openpyxl**: Excel file handling
- **httpx**: HTTP client for Telegram
- **scikit-learn**: Optional ML capabilities

## 🤝 Contributing

1. Follow the existing code structure
2. Add tests for new features
3. Update documentation
4. Ensure Telegram integration works
5. Test Excel synchronization

## 📄 License

This project is for personal/internal use. Modify as needed for your requirements.
