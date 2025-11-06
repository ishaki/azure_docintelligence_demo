# Document Intelligence Demo

A modern web application for uploading and analyzing PDF documents using Azure Document Intelligence API. The app supports drag-and-drop file uploads, multi-file processing, and displays extracted fields with confidence levels.

## Features

- 📄 PDF document upload (drag & drop or file selection)
- 📤 Multi-file upload support
- 🤖 Azure Document Intelligence integration
- 📊 Structured results display (field name, value, confidence)
- 🎨 Modern, professional UI
- ⚡ **Asynchronous processing** with real-time progress updates
- 📈 **Live progress tracking** for each document
- 🔄 **Concurrent processing** of multiple files
- ✨ Beautiful progress indicators with file-by-file status

## Prerequisites

- Python 3.9 or higher
- Azure Document Intelligence resource (formerly Form Recognizer)
- Azure account with Document Intelligence API access

## Setup Instructions

### 1. Clone or Download the Project

```bash
cd DocIntelligentDemo
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Azure Credentials

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```
   (On Linux/Mac: `cp .env.example .env`)

2. Edit `.env` and add your Azure credentials:
   ```
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=https://your-resource-name.cognitiveservices.azure.com/
   AZURE_DOCUMENT_INTELLIGENCE_KEY=your-api-key-here
   AZURE_DOCUMENT_MODEL_ID=YOUR_MODELNAME_v1
   ```

   To get these credentials:
   - Go to Azure Portal
   - Create or select a Document Intelligence resource
   - Copy the Endpoint URL
   - Copy one of the API keys from the "Keys and Endpoint" section
   - Set the Model ID:
     - For **custom trained models**: Use your model ID (e.g., `AIHarvest_Energy_Model_v1`)
     - For **prebuilt models**: Use `prebuilt-layout`, `prebuilt-invoice`, `prebuilt-receipt`, etc.

### 6. Run the Application

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Access the Web Application

Open your browser and navigate to:
```
http://localhost:8000
```

## Logging

The application automatically creates daily log files in the `logs/` directory:

- **`logs/app.log`** - All application logs (INFO, DEBUG, WARNING, ERROR)
  - Rotates daily at midnight
  - Keeps 30 days of history
  - Includes detailed information: timestamp, logger name, log level, function name, line number, and message

- **`logs/error.log`** - Error logs only (ERROR and above)
  - Rotates daily at midnight
  - Keeps 90 days of history
  - Useful for troubleshooting production issues

Log files are automatically created when the application starts. The logs directory is already included in `.gitignore` to prevent committing log files to version control.

### Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages about application operation
- **WARNING**: Warning messages for potentially problematic situations
- **ERROR**: Error messages for failures that don't stop the application

### Viewing Logs

To view logs in real-time:

```bash
# View all logs
tail -f logs/app.log

# View error logs only
tail -f logs/error.log

# View today's log file
cat logs/app.log.$(date +%Y-%m-%d)
```

## Usage

1. **Upload Documents**: 
   - Click "Select Files" button, or
   - Drag and drop PDF files into the upload area

2. **Process Documents**:
   - Click "Upload and Extract" button
   - Wait for processing to complete

3. **View Results**:
   - Results will display below with:
     - Field Name
     - Field Value
     - Confidence Level (as percentage)

## Project Structure

```
DocIntelligentDemo/
├── main.py                 # FastAPI backend application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .env                   # Your actual credentials (create this)
├── README.md              # This file
└── static/
    ├── index.html         # Frontend HTML
    ├── style.css          # CSS styles
    └── script.js          # Frontend JavaScript
```

## API Endpoints

- `GET /` - Main web interface
- `POST /api/analyze` - Analyze uploaded PDF documents
- `GET /api/health` - Health check endpoint

## Using Different Document Models

The app currently uses the `prebuilt-read` model. You can change this in `main.py` to use other models:

- `prebuilt-invoice` - For invoices
- `prebuilt-receipt` - For receipts
- `prebuilt-businessCard` - For business cards
- `prebuilt-idDocument` - For ID documents
- `prebuilt-tax.us.1098` - For US tax forms

Simply replace `"prebuilt-read"` with your desired model in the `analyze_documents` function.

## Troubleshooting

### "Azure Document Intelligence credentials not configured"
- Make sure you created `.env` file with your credentials
- Check that the environment variable names are correct

### "Only PDF files are supported"
- Ensure you're uploading PDF files only
- Check file extension is `.pdf`

### Connection errors
- Verify your Azure endpoint URL is correct
- Check your API key is valid
- Ensure your Azure resource is active

## License

This project is provided as-is for demonstration purposes.

## Notes

- The application processes documents synchronously
- Large files may take longer to process
- Ensure your Azure subscription has sufficient quota for Document Intelligence API calls

