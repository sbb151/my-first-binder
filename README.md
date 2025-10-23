# SEC Filings Downloader and Cleaner

A Python tool to download SEC filings from EDGAR and remove all HTML, XBRL, and XML tags to extract clean text.

## Features

- **Download the ENTIRE population** of SEC filings using quarterly index files
- **Download SEC filings** for specified form types (10-K, 10-Q, 8-K, etc.) and years
- **Automatic folder organization**: Creates `{year}/Raw/` and `{year}/Clean/` folder structure
- **Tag removal**: Strips all HTML, XBRL, and XML tags from filings
- **Flexible filtering**: Download filings by company CIK, form type, or quarter
- **Rate limiting**: Respects SEC EDGAR server guidelines with appropriate delays
- **Resumption support**: Skips already downloaded files if interrupted

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

### Method 1: Download ALL Filings (Recommended)

Use SEC quarterly index files to download the **complete population** of filings:

```python
from sec_filings_downloader import SECFilingsProcessor

processor = SECFilingsProcessor()

# Download ALL 10-K filings from 2023
processor.process_all_filings_from_index(
    form_types=['10-K'],
    year=2023,
    max_filings=100  # Optional: remove to download ALL
)
```

### Method 2: Download Filings for Specific Companies

```python
from sec_filings_downloader import SECFilingsProcessor

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

### Example 1: Download ALL Filings from Index Files (RECOMMENDED)

This method downloads the **entire population** of filings for the specified form types.

```python
processor = SECFilingsProcessor()

# Download ALL 10-K and 10-Q filings from 2023
processor.process_all_filings_from_index(
    form_types=['10-K', '10-Q'],
    year=2023
    # No max_filings = download everything!
)
```

### Example 2: Download with Limits for Testing

```python
processor = SECFilingsProcessor()

# Download first 50 10-K filings for testing
processor.process_all_filings_from_index(
    form_types=['10-K'],
    year=2023,
    max_filings=50  # Limit to 50 filings
)
```

### Example 3: Download from Specific Quarters

```python
processor = SECFilingsProcessor()

# Download only from Q1 and Q2
processor.process_all_filings_from_index(
    form_types=['10-K'],
    year=2023,
    quarters=[1, 2]  # Only Q1 and Q2
)
```

### Example 4: Download Filings for Specific Companies

```python
processor = SECFilingsProcessor()

# Download all 10-K and 10-Q filings for Microsoft in 2023
processor.process_filings(
    form_types=['10-K', '10-Q'],
    year=2023,
    cik_list=['0000789019']  # Microsoft's CIK
)
```

### Example 5: Download for Multiple Companies

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

### Example 6: Custom Output Directory

```python
processor = SECFilingsProcessor(base_dir="./my_data")

processor.process_all_filings_from_index(
    form_types=['8-K'],
    year=2023,
    max_filings=100
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

### Index-Based Method (Complete Population)

1. **Download Indexes**: Downloads SEC quarterly index files (.idx) for the specified year
2. **Parse Indexes**: Extracts all filings matching the form types from the index
3. **Download Filings**: Fetches each filing from EDGAR
4. **Save Raw**: Stores the original HTML/XBRL file in the Raw folder
5. **Clean**: Uses BeautifulSoup to remove all HTML, XML, and XBRL tags
6. **Save Clean**: Stores the cleaned text in the Clean folder

### Company-Based Method (Specific Companies)

1. **Query EDGAR**: Fetches filings for specified CIKs, form types, and date range
2. **Parse**: Identifies the primary document from the filing index page
3. **Save Raw**: Stores the original HTML/XBRL file in the Raw folder
4. **Clean**: Uses BeautifulSoup to remove all HTML, XML, and XBRL tags
5. **Save Clean**: Stores the cleaned text in the Clean folder

## Class Reference

### SECFilingsProcessor

Main class for downloading and cleaning SEC filings.

#### Methods

- **`__init__(base_dir='.')`**: Initialize processor with optional base directory

- **`process_all_filings_from_index(form_types, year, max_filings=None, quarters=None)`**: Download ALL filings using quarterly index files (RECOMMENDED for complete population)
  - `form_types` (List[str]): List of form types (e.g., ['10-K', '10-Q'])
  - `year` (int): Year of filings to retrieve
  - `max_filings` (int, optional): Maximum number of filings to process (None = all)
  - `quarters` (List[int], optional): List of quarters to process (default: [1,2,3,4])

- **`process_filings(form_types, year, cik_list=None, max_filings=None)`**: Download filings for specific companies
  - `form_types` (List[str]): List of form types (e.g., ['10-K', '10-Q'])
  - `year` (int): Year of filings to retrieve
  - `cik_list` (List[str], optional): List of CIKs to filter by
  - `max_filings` (int, optional): Maximum number of filings to process

## Performance and Usage Notes

### Download Times

- **Per filing**: Approximately 1-2 seconds (download + cleaning)
- **100 filings**: ~5-10 minutes
- **1,000 filings**: ~45-90 minutes
- **Complete 10-K population** (4,000-5,000 filings): 2-3 hours

### Best Practices

1. **Test first**: Always use `max_filings` parameter to test with a small sample (10-50 filings) before downloading thousands
2. **Resumption**: The script automatically skips already downloaded files if interrupted, so you can safely stop and restart
3. **Rate limiting**: Built-in delays (0.15s between requests) respect SEC EDGAR guidelines
4. **Disk space**: A typical 10-K filing is 1-5 MB raw, 200-500 KB cleaned. Plan accordingly for large downloads
5. **Network**: Stable internet connection recommended for large downloads

### Technical Notes

- The tool implements rate limiting to respect SEC EDGAR server guidelines
- Large filings may take time to download and process
- The SEC EDGAR system requires a User-Agent header, which this tool provides
- Cleaned files may still contain some formatting artifacts depending on the original filing structure
- Index files are downloaded once per quarter and parsed in memory (not saved to disk)

## License

This tool is provided for educational and research purposes.

## Acknowledgments

- SEC EDGAR database: https://www.sec.gov/edgar
- BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
