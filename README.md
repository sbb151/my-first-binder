# SEC Filings Downloader and Cleaner

A Python tool to download SEC filings from EDGAR and remove all HTML, XBRL, and XML tags to extract clean text.

## Features

- **Download SEC filings** for specified form types (10-K, 10-Q, 8-K, etc.) and years
- **Automatic folder organization**: Creates `{year}/Raw/` and `{year}/Clean/` folder structure
- **Tag removal**: Strips all HTML, XBRL, and XML tags from filings
- **Flexible filtering**: Download filings by company CIK or form type
- **Rate limiting**: Respects SEC EDGAR server guidelines with appropriate delays

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests beautifulsoup4 lxml
```

## Quick Start

### Python Script

```python
from sec_filings_downloader import SECFilingsProcessor

# Initialize the processor
processor = SECFilingsProcessor()

# Download 10-K filings for Apple in 2023
processor.process_filings(
    form_types=['10-K'],
    year=2023,
    cik_list=['0000320193']  # Apple's CIK
)
```

### Jupyter Notebook

See `SEC_Filings_Example.ipynb` for detailed examples.

## Usage Examples

### Example 1: Download Filings for a Specific Company

```python
processor = SECFilingsProcessor()

# Download all 10-K and 10-Q filings for Microsoft in 2023
processor.process_filings(
    form_types=['10-K', '10-Q'],
    year=2023,
    cik_list=['0000789019']  # Microsoft's CIK
)
```

### Example 2: Download Filings for Multiple Companies

```python
processor = SECFilingsProcessor()

processor.process_filings(
    form_types=['10-K'],
    year=2023,
    cik_list=[
        '0000320193',  # Apple Inc.
        '0000789019',  # Microsoft Corporation
        '0001018724'   # Amazon.com Inc.
    ]
)
```

### Example 3: Download Limited Number of Filings

```python
processor = SECFilingsProcessor()

# Download first 10 filings of any company
processor.process_filings(
    form_types=['10-K', '10-Q'],
    year=2023,
    max_filings=10
)
```

### Example 4: Custom Output Directory

```python
processor = SECFilingsProcessor(base_dir="./my_data")

processor.process_filings(
    form_types=['8-K'],
    year=2023,
    cik_list=['0000320193']
)

# Creates: ./my_data/2023/Raw/ and ./my_data/2023/Clean/
```

## Output Structure

After running the processor, files are organized as follows:

```
{year}/
├── Raw/
│   ├── {CIK}_{FormType}_{FilingDate}.html
│   ├── {CIK}_{FormType}_{FilingDate}.html
│   └── ...
└── Clean/
    ├── {CIK}_{FormType}_{FilingDate}.txt
    ├── {CIK}_{FormType}_{FilingDate}.txt
    └── ...
```

- **Raw folder**: Original HTML/XBRL filings as downloaded from SEC EDGAR
- **Clean folder**: Text-only versions with all tags removed

## Common Form Types

- **10-K**: Annual report
- **10-Q**: Quarterly report
- **8-K**: Current report (significant events)
- **DEF 14A**: Proxy statement
- **S-1**: Registration statement for new securities

## Common CIK Numbers

| Company | CIK |
|---------|-----|
| Apple Inc. | 0000320193 |
| Microsoft Corporation | 0000789019 |
| Amazon.com Inc. | 0001018724 |
| Tesla Inc. | 0001318605 |
| Alphabet Inc. | 0001652044 |
| Meta Platforms Inc. | 0001326801 |
| NVIDIA Corporation | 0001045810 |
| Berkshire Hathaway | 0001067983 |

Find more CIK numbers at: https://www.sec.gov/edgar/searchedgar/companysearch.html

## How It Works

1. **Download**: Fetches filings from SEC EDGAR using the company's CIK, form type, and date range
2. **Parse**: Identifies the primary document from the filing index page
3. **Save Raw**: Stores the original HTML/XBRL file in the Raw folder
4. **Clean**: Uses BeautifulSoup to remove all HTML, XML, and XBRL tags
5. **Save Clean**: Stores the cleaned text in the Clean folder

## Class Reference

### SECFilingsProcessor

Main class for downloading and cleaning SEC filings.

#### Methods

- **`__init__(base_dir='.')`**: Initialize processor with optional base directory
- **`process_filings(form_types, year, cik_list=None, max_filings=None)`**: Main method to download and clean filings
  - `form_types` (List[str]): List of form types (e.g., ['10-K', '10-Q'])
  - `year` (int): Year of filings to retrieve
  - `cik_list` (List[str], optional): List of CIKs to filter by
  - `max_filings` (int, optional): Maximum number of filings to process

## Notes

- The tool implements rate limiting to respect SEC EDGAR server guidelines (0.15 second delay between requests)
- Large filings may take time to download and process
- The SEC EDGAR system requires a User-Agent header, which this tool provides
- Cleaned files may still contain some formatting artifacts depending on the original filing structure

## License

This tool is provided for educational and research purposes.

## Acknowledgments

- SEC EDGAR database: https://www.sec.gov/edgar
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
