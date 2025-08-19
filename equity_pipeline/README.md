# Public Equities Data Pipeline

A clean, modular pipeline for enriching company data with retry logic using Supabase as the database backend.

## Features

- **Modular Architecture**: Clean separation between data enrichers, database operations, and pipeline orchestration
- **Retry Logic**: Automatic retry with exponential backoff for failed operations
- **Configurable**: Easy configuration through environment variables
- **Batch Processing**: Efficient batch updates to minimize database calls
- **Comprehensive Logging**: Detailed logging for monitoring and debugging
- **Multiple Data Sources**: Yahoo Finance integration with extensible enricher pattern

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd equity_pipeline
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

Or install as a package:
```bash
pip install -e .
```

## Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your Supabase credentials:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
LOG_LEVEL=INFO
```

## Database Setup

The pipeline expects a Supabase table named `companies_bbt` with at least a `Ticker` column. Example schema:

```sql
CREATE TABLE companies_bbt (
    id SERIAL PRIMARY KEY,
    "Ticker" TEXT NOT NULL UNIQUE,
    "Market Cap" BIGINT,
    "EV" BIGINT,
    "Avg D Val Traded 3M" NUMERIC,
    "GICS Sector" TEXT,
    "GICS Ind Grp Name" TEXT,
    "Cntry Tertry Of Dom" TEXT,
    last_enriched TIMESTAMP
);

-- Optional: Create enrichment logs table
CREATE TABLE enrichment_logs (
    id SERIAL PRIMARY KEY,
    ticker TEXT,
    error TEXT,
    timestamp TIMESTAMP,
    enricher TEXT
);
```

## Usage

### Command Line

If installed as a package:
```bash
equity-pipeline
```

Or run directly:
```bash
python src/equity_pipeline/main.py
```

### Programmatic Usage

```python
from equity_pipeline.main import Config, EnrichmentPipeline

# Create configuration
config = Config()

# Create and run pipeline
pipeline = EnrichmentPipeline(config)

# Run with limit for testing
pipeline.run(limit=10)

# Or process all companies
pipeline.run()
```

## Architecture

### Core Components

1. **Config**: Central configuration management
2. **DatabaseManager**: Handles all Supabase database operations
3. **BaseEnricher**: Base class for all data enrichers
4. **EnrichmentPipeline**: Main orchestrator

### Data Enrichers

- **YahooFinanceEnricher**: Fetches market data from Yahoo Finance
- **ISINEnricher**: Placeholder for ISIN code enrichment
- **SectorClassificationEnricher**: Placeholder for BICS classification

### Configuration Options

- `batch_size`: Number of companies to process in each batch (default: 10)
- `save_frequency`: Save to database every N companies (default: 5)
- `max_retries`: Maximum retry attempts for failed operations (default: 2)
- `retry_delay`: Base delay between retries in seconds (default: 1.0)

## Extending the Pipeline

### Adding New Enrichers

1. Create a new class inheriting from `BaseEnricher`:

```python
class MyCustomEnricher(BaseEnricher):
    @retry_on_failure(max_retries=2, delay=1.0)
    def enrich(self, company: Dict[str, Any]) -> Dict[str, Any]:
        # Your enrichment logic here
        return enriched_data
```

2. Add it to the pipeline in `EnrichmentPipeline._initialize_enrichers()`:

```python
def _initialize_enrichers(self) -> List[BaseEnricher]:
    return [
        YahooFinanceEnricher(self.config),
        MyCustomEnricher(self.config),  # Add your enricher
        # ... other enrichers
    ]
```

## Error Handling

The pipeline includes comprehensive error handling:

- **Retry Logic**: Failed operations are retried with exponential backoff
- **Graceful Degradation**: If one enricher fails, others continue processing
- **Error Logging**: All errors are logged to the enrichment_logs table
- **Batch Safety**: Failed batch updates don't affect other batches

## Logging

The pipeline uses Python's built-in logging module. Log levels can be configured via the `LOG_LEVEL` environment variable:

- `DEBUG`: Detailed debugging information
- `INFO`: General information about pipeline progress (default)
- `WARNING`: Warning messages for non-critical issues
- `ERROR`: Error messages for failed operations

## Development

### Project Structure

```
equity_pipeline/
├── src/
│   └── equity_pipeline/
│       ├── __init__.py
│       └── main.py
├── tests/
├── docs/
├── requirements.txt
├── setup.py
├── .env.example
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
pytest tests/

# Run with coverage
pytest --cov=equity_pipeline tests/
```

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request