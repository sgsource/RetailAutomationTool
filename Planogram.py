import re
import pandas as pd
from pypdf import PdfReader
import urllib.request
import io

class Planogram:
    def __init__(self):
        self._reset()

    def get_pog(self, path: str) -> pd.DataFrame:
        """Main entry point: load PDF (local or URL), extract POG number, and parse item data."""
        try:
            # set up reader
            self._load_file(path)

            # check if file has pog number
            self.get_pog_num()

            # ensure file actually has an item listing
            start_page = self._get_start_page()

            # extract crc -> num
            self.df = self._parse_data(start_page)
            return self.df
        except Exception as e:
            self._reset()
            raise RuntimeError(f"Failed to load {path}: {e}")

    def _load_file(self, path: str):
        """Load PDF from URL (fail-safe)."""
        if path.endswith('.pdf'):
            if re.fullmatch(r'https?://\S+', path):
                # Fetch PDF from URL
                req = urllib.request.Request(path, headers={'User-Agent': "Mozilla/5.0"})
                remote_file_content = urllib.request.urlopen(req).read()
                remote_file_bytes = io.BytesIO(remote_file_content)
                self.reader = PdfReader(remote_file_bytes)
            else:
                self.reader = PdfReader(path)
        else:
            raise RuntimeError("Invalid file type: expected PDF.")

    def _reset(self):
        """Reset internal state."""
        self.reader = None
        self.df = pd.DataFrame()
    
    def get_num_items(self) -> int:
        return 0 if self.df.empty else len(self.df)

    @staticmethod
    def _check_reader(f):
        """Decorator to ensure reader is initialized before method call."""
        def wrapper(self, *args, **kwargs):
            if self.reader is None:
                raise RuntimeError("Reader not initialized")
            return f(self, *args, **kwargs)
        return wrapper

    @_check_reader
    def get_pog_num(self) -> int:
        """Extract POG number from the first page."""
        page = self.reader.pages[0]
        text = page.extract_text() or ''
        match = re.search(r'\b\d{5,6}\b', text)
        if match:
            return match.group(0)
        else:
            raise RuntimeError('Cannot find POG number in PDF.')

    @_check_reader
    def _get_start_page(self):
        """Find the first page that contains the item listing."""
        for pno, page in enumerate(self.reader.pages):
            text = page.extract_text() or ''
            if "Stock Assortment Listing" in text:
                return pno
        raise RuntimeError('Cannot find first page of item listing.')

    @_check_reader
    def _parse_data(self, start_page: int):
        """Parse item data into a DataFrame with string index (CRC) and integer NUM column."""
        nums = []
        crcs = []

        for page_num in range(start_page, len(self.reader.pages)):
            page = self.reader.pages[page_num]
            text = page.extract_text() or ''

            matches = re.findall(r"\b(\d{1,4})\s+(\d{7})\b", text)

            for num_str, crc in matches:
                nums.append(int(num_str))
                crcs.append(crc)

        df = pd.DataFrame({'NUM': nums}, index=pd.Index(crcs, name="CRC", dtype='str'))
        if not df.index.is_unique:
            raise RuntimeError("Duplicate CRC codes found in PDF.")
        return df