"""
SEC Filings Downloader and Cleaner

This script downloads SEC filings for specified form types and years,
then cleans them by removing all HTML, XBRL, and XML tags.

Usage:
    from sec_filings_downloader import SECFilingsProcessor

    processor = SECFilingsProcessor()
    processor.process_filings(
        form_types=['10-K', '10-Q'],
        year=2023,
        cik_list=['0000320193']  # Optional: specific companies
    )
"""

import os
import re
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import warnings

warnings.filterwarnings('ignore')


class SECFilingsProcessor:
    """
    A class to download and clean SEC filings from EDGAR.
    """

    BASE_URL = "https://www.sec.gov"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (compatible; Academic Research)',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }

    def __init__(self, base_dir: str = "."):
        """
        Initialize the SEC filings processor.

        Args:
            base_dir: Base directory for storing filings (default: current directory)
        """
        self.base_dir = Path(base_dir)
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def create_folders(self, year: int) -> tuple:
        """
        Create Raw and Clean folders for the specified year.

        Args:
            year: The year for which to create folders

        Returns:
            Tuple of (raw_folder_path, clean_folder_path)
        """
        year_folder = self.base_dir / str(year)
        raw_folder = year_folder / "Raw"
        clean_folder = year_folder / "Clean"

        raw_folder.mkdir(parents=True, exist_ok=True)
        clean_folder.mkdir(parents=True, exist_ok=True)

        print(f"Created folders:")
        print(f"  Raw: {raw_folder}")
        print(f"  Clean: {clean_folder}")

        return raw_folder, clean_folder

    def get_company_filings(self, cik: str, form_types: List[str],
                           year: int) -> List[dict]:
        """
        Get filings for a specific company, form type, and year.

        Args:
            cik: Central Index Key (CIK) of the company
            form_types: List of form types (e.g., ['10-K', '10-Q'])
            year: Year of filings to retrieve

        Returns:
            List of filing dictionaries with metadata
        """
        # Pad CIK with leading zeros to 10 digits
        cik_padded = cik.zfill(10)

        # Build the submissions URL
        submissions_url = f"{self.BASE_URL}/cgi-bin/browse-edgar"

        filings = []

        for form_type in form_types:
            params = {
                'action': 'getcompany',
                'CIK': cik,
                'type': form_type,
                'dateb': f'{year}1231',  # End date
                'datea': f'{year}0101',  # Start date
                'owner': 'exclude',
                'output': 'xml',
                'count': '100'
            }

            try:
                response = self.session.get(submissions_url, params=params, timeout=10)
                response.raise_for_status()

                # Parse XML response
                soup = BeautifulSoup(response.content, 'xml')

                for entry in soup.find_all('filing'):
                    filing_date = entry.find('filingDate')
                    filing_href = entry.find('filingHREF')
                    form = entry.find('type')

                    if filing_date and filing_href and form:
                        filing_date_str = filing_date.text
                        filing_year = int(filing_date_str.split('-')[0])

                        if filing_year == year:
                            filings.append({
                                'cik': cik,
                                'form_type': form.text,
                                'filing_date': filing_date_str,
                                'url': filing_href.text
                            })

                # Be respectful to SEC servers
                time.sleep(0.1)

            except Exception as e:
                print(f"Error fetching filings for CIK {cik}, form {form_type}: {e}")

        return filings

    def search_filings_by_form_type(self, form_types: List[str],
                                    year: int,
                                    max_filings: Optional[int] = None) -> List[dict]:
        """
        Search for filings by form type and year using EDGAR full-text search.

        Args:
            form_types: List of form types to search for
            year: Year of filings
            max_filings: Maximum number of filings to retrieve (None for all)

        Returns:
            List of filing dictionaries
        """
        filings = []

        for form_type in form_types:
            print(f"Searching for {form_type} filings in {year}...")

            # Use the EDGAR search interface
            search_url = f"{self.BASE_URL}/cgi-bin/browse-edgar"

            params = {
                'action': 'getcompany',
                'type': form_type,
                'dateb': f'{year}1231',
                'datea': f'{year}0101',
                'owner': 'exclude',
                'output': 'xml',
                'count': '100' if max_filings is None else str(min(max_filings, 100))
            }

            try:
                response = self.session.get(search_url, params=params, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'xml')

                for entry in soup.find_all('filing'):
                    filing_date = entry.find('filingDate')
                    filing_href = entry.find('filingHREF')
                    form = entry.find('type')
                    cik = entry.find('companyName')

                    if filing_date and filing_href and form:
                        filing_date_str = filing_date.text
                        filing_year = int(filing_date_str.split('-')[0])

                        if filing_year == year:
                            filings.append({
                                'cik': entry.find('CIK').text if entry.find('CIK') else 'unknown',
                                'company_name': cik.text if cik else 'Unknown',
                                'form_type': form.text,
                                'filing_date': filing_date_str,
                                'url': filing_href.text
                            })

                            if max_filings and len(filings) >= max_filings:
                                break

                time.sleep(0.1)

            except Exception as e:
                print(f"Error searching for {form_type} filings: {e}")

        print(f"Found {len(filings)} filings")
        return filings

    def download_filing(self, filing_url: str, output_path: Path) -> bool:
        """
        Download a single filing from EDGAR.

        Args:
            filing_url: URL to the filing
            output_path: Path where to save the filing

        Returns:
            True if successful, False otherwise
        """
        try:
            # First, get the index page
            response = self.session.get(filing_url, timeout=10)
            response.raise_for_status()

            # Parse the index page to find the main document
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for the main filing document (usually ends with .htm or .txt)
            # Priority: .htm files in the table
            doc_url = None

            # Find all links in the document table
            for row in soup.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Check if this is a document row
                    for cell in cells:
                        link = cell.find('a', href=True)
                        if link:
                            href = link['href']
                            # Look for primary document (usually the first .htm or .txt)
                            if href.endswith('.htm') or href.endswith('.html') or href.endswith('.txt'):
                                doc_url = urljoin(self.BASE_URL, href)
                                break
                    if doc_url:
                        break

            # If we found a document URL, download it
            if doc_url:
                doc_response = self.session.get(doc_url, timeout=10)
                doc_response.raise_for_status()

                # Save the content
                with open(output_path, 'wb') as f:
                    f.write(doc_response.content)

                return True
            else:
                # Fallback: save the index page itself
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True

        except Exception as e:
            print(f"Error downloading filing from {filing_url}: {e}")
            return False

    def clean_filing(self, input_path: Path, output_path: Path) -> bool:
        """
        Remove all HTML, XBRL, and XML tags from a filing.

        Args:
            input_path: Path to the raw filing
            output_path: Path where to save the cleaned filing

        Returns:
            True if successful, False otherwise
        """
        try:
            # Read the file
            with open(input_path, 'rb') as f:
                content = f.read()

            # Try to decode with different encodings
            text = None
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if text is None:
                print(f"Could not decode {input_path}")
                return False

            # Remove XBRL and XML tags using BeautifulSoup
            soup = BeautifulSoup(text, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'meta', 'link']):
                script.decompose()

            # Get text
            cleaned_text = soup.get_text()

            # Additional cleaning with regex
            # Remove excessive whitespace
            cleaned_text = re.sub(r'\n\s*\n', '\n\n', cleaned_text)
            cleaned_text = re.sub(r' +', ' ', cleaned_text)

            # Remove any remaining XML/SGML tags that might have been missed
            cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text)

            # Remove special XBRL namespace declarations
            cleaned_text = re.sub(r'xmlns:\w+="[^"]*"', '', cleaned_text)

            # Clean up lines
            lines = [line.strip() for line in cleaned_text.split('\n')]
            cleaned_text = '\n'.join(line for line in lines if line)

            # Save cleaned content
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)

            return True

        except Exception as e:
            print(f"Error cleaning filing {input_path}: {e}")
            return False

    def process_filings(self, form_types: List[str], year: int,
                       cik_list: Optional[List[str]] = None,
                       max_filings: Optional[int] = None):
        """
        Main method to download and clean filings.

        Args:
            form_types: List of form types (e.g., ['10-K', '10-Q'])
            year: Year of filings to retrieve
            cik_list: Optional list of CIKs to limit search to specific companies
            max_filings: Optional maximum number of filings to process
        """
        print(f"\n{'='*60}")
        print(f"SEC Filings Processor")
        print(f"{'='*60}")
        print(f"Form types: {', '.join(form_types)}")
        print(f"Year: {year}")
        if cik_list:
            print(f"Companies (CIKs): {', '.join(cik_list)}")
        print(f"{'='*60}\n")

        # Create folder structure
        raw_folder, clean_folder = self.create_folders(year)

        # Get filings
        all_filings = []

        if cik_list:
            # Download filings for specific companies
            for cik in cik_list:
                print(f"\nProcessing company CIK: {cik}")
                filings = self.get_company_filings(cik, form_types, year)
                all_filings.extend(filings)
        else:
            # Search for all filings of the specified types
            all_filings = self.search_filings_by_form_type(
                form_types, year, max_filings
            )

        if not all_filings:
            print("\nNo filings found matching the criteria.")
            return

        # Limit number of filings if specified
        if max_filings:
            all_filings = all_filings[:max_filings]

        print(f"\n{'='*60}")
        print(f"Downloading {len(all_filings)} filings...")
        print(f"{'='*60}\n")

        # Download filings
        downloaded_files = []
        for i, filing in enumerate(all_filings, 1):
            # Create filename
            cik = filing['cik']
            form_type = filing['form_type'].replace('/', '_')
            filing_date = filing['filing_date'].replace('-', '')
            filename = f"{cik}_{form_type}_{filing_date}.html"

            raw_path = raw_folder / filename

            print(f"[{i}/{len(all_filings)}] Downloading {filename}...")

            if self.download_filing(filing['url'], raw_path):
                downloaded_files.append((raw_path, filename))
                print(f"  ✓ Saved to {raw_path}")
            else:
                print(f"  ✗ Failed to download")

            # Be respectful to SEC servers
            time.sleep(0.15)

        print(f"\n{'='*60}")
        print(f"Cleaning {len(downloaded_files)} filings...")
        print(f"{'='*60}\n")

        # Clean filings
        cleaned_count = 0
        for i, (raw_path, filename) in enumerate(downloaded_files, 1):
            clean_filename = filename.replace('.html', '.txt')
            clean_path = clean_folder / clean_filename

            print(f"[{i}/{len(downloaded_files)}] Cleaning {filename}...")

            if self.clean_filing(raw_path, clean_path):
                cleaned_count += 1
                print(f"  ✓ Saved to {clean_path}")
            else:
                print(f"  ✗ Failed to clean")

        print(f"\n{'='*60}")
        print(f"Processing Complete!")
        print(f"{'='*60}")
        print(f"Downloaded: {len(downloaded_files)} filings")
        print(f"Cleaned: {cleaned_count} filings")
        print(f"Raw files: {raw_folder}")
        print(f"Clean files: {clean_folder}")
        print(f"{'='*60}\n")


def main():
    """
    Example usage of the SEC Filings Processor.
    """
    processor = SECFilingsProcessor()

    # Example 1: Download 10-K filings for Apple (CIK: 0000320193) in 2023
    # processor.process_filings(
    #     form_types=['10-K'],
    #     year=2023,
    #     cik_list=['0000320193']
    # )

    # Example 2: Download first 10 10-K and 10-Q filings from 2023
    processor.process_filings(
        form_types=['10-K', '10-Q'],
        year=2023,
        max_filings=10
    )


if __name__ == "__main__":
    main()
