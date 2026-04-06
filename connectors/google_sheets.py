from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json
import tempfile
import pandas as pd
from dotenv import load_dotenv
import numpy as np

load_dotenv()


class GoogleSheetsConnector:
    # Use read-only scope to limit what we can do
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    
    def __init__(self, sheet_id: str, sheet_range: str = "A1:Z1000"):
        self.sheet_id = sheet_id
        self.sheet_range = sheet_range
        
        # Find credentials (from env var or file)
        self.creds_path = self._get_credentials_path()
        self.service = self._connect_to_sheets()
        self.has_write_access = None
        self.sheet_title = None

    def _get_credentials_path(self):
        """Get credentials from environment variable or file"""
        
        # 🔥 NEW: Try to get credentials from environment variable first (for Render free tier)
        creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
        if creds_json:
            try:
                # Validate JSON
                json.loads(creds_json)
                # Write to temporary file
                temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
                temp_file.write(creds_json)
                temp_file.close()
                print(f"✅ Loaded Google credentials from environment variable")
                return temp_file.name
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in GOOGLE_CREDENTIALS_JSON: {e}")
        
        # Check environment variable for file path
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path and os.path.exists(creds_path):
            print(f"✅ Found credentials at: {creds_path}")
            return creds_path
        
        # Check common locations
        possible_paths = [
            "/app/credentials/google-credentials.json",  # Docker path
            "agentic-analyst-489012-a0aa86d33643.json",  # Project root
            "../agentic-analyst-489012-a0aa86d33643.json",  # One level up
            os.path.join(os.path.dirname(__file__), "../agentic-analyst-489012-a0aa86d33643.json"),
            os.path.join(os.path.dirname(__file__), "agentic-analyst-489012-a0aa86d33643.json"),
        ]
        
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                print(f"✅ Found credentials at: {abs_path}")
                return abs_path
        
        raise FileNotFoundError(
            "Google credentials not found. Please set GOOGLE_CREDENTIALS_JSON environment variable "
            "with the service account JSON content, or set GOOGLE_APPLICATION_CREDENTIALS to the file path."
        )

    def _connect_to_sheets(self):
        """Connect to Google Sheets with read-only credentials"""
        if not self.creds_path:
            raise ValueError("Google credentials file not found")
        
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.creds_path, 
                scopes=self.SCOPES
            )
            service = build('sheets', 'v4', credentials=creds)
            return service.spreadsheets()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Google Sheets API: {str(e)}")

    def _check_permissions(self):
        """Check if the service account has proper read access and detect write access"""
        try:
            # Get spreadsheet metadata - this works with both Viewer and Editor
            spreadsheet = self.service.get(spreadsheetId=self.sheet_id).execute()
            self.sheet_title = spreadsheet.get('properties', {}).get('title', 'Unknown')
            print(f"✅ Connected to sheet: {self.sheet_title}")
            
            # Try a different approach to detect write access
            try:
                # Try to get developer metadata - this requires edit access
                metadata = self.service.developerMetadata().get(
                    spreadsheetId=self.sheet_id,
                    metadataId=1
                ).execute()
                self.has_write_access = True
                print("⚠️ WARNING: Service account has EDITOR (write) access!")
            except HttpError as e:
                if e.resp.status == 403:
                    self.has_write_access = False
                    print("✅ Service account has VIEWER (read-only) access")
                elif e.resp.status == 404:
                    self._test_write_access_via_batch_update()
                else:
                    raise
                    
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(
                    f"Access denied. Please share your Google Sheet with the service account email "
                    f"and give it at least 'Viewer' (read-only) access.\n"
                    f"Sheet ID: {self.sheet_id}"
                )
            elif e.resp.status == 404:
                raise ValueError(f"Sheet not found. Please check the Sheet ID: {self.sheet_id}")
            raise
        
        return self.sheet_title

    def _test_write_access_via_batch_update(self):
        """Test write access using a batch update (won't actually modify anything)"""
        try:
            body = {
                'requests': [
                    {
                        'repeatCell': {
                            'range': {
                                'sheetId': 0,
                                'startRowIndex': 0,
                                'endRowIndex': 0,
                                'startColumnIndex': 0,
                                'endColumnIndex': 1
                            },
                            'cell': {
                                'userEnteredValue': None
                            },
                            'fields': 'userEnteredValue'
                        }
                    }
                ]
            }
            self.service.batchUpdate(
                spreadsheetId=self.sheet_id,
                body=body
            ).execute()
            self.has_write_access = True
            print("⚠️ WARNING: Service account has EDITOR (write) access!")
        except HttpError as e:
            if e.resp.status == 403:
                self.has_write_access = False
                print("✅ Service account has VIEWER (read-only) access")
            else:
                self.has_write_access = False
                print("✅ Assuming VIEWER (read-only) access")

    def fetch_sheet(self) -> pd.DataFrame:
        """Fetch sheet data with read-only permissions"""
        try:
            # First check permissions
            self._check_permissions()
            print(f"📊 Fetching data from sheet: {self.sheet_title}")
            print(f"📍 Range: {self.sheet_range}")
            
            # Fetch the data
            result = self.service.values().get(
                spreadsheetId=self.sheet_id,
                range=self.sheet_range
            ).execute()

            values = result.get('values', [])

            if not values:
                print("⚠️ No data found in sheet.")
                return pd.DataFrame()

            headers = values[0]
            data = values[1:]

            # Normalize row lengths
            normalized_data = []
            for row in data:
                if len(row) < len(headers):
                    row = row + [None] * (len(headers) - len(row))
                
                # Clean the row
                cleaned_row = []
                for cell in row:
                    if cell == '' or cell is None:
                        cleaned_row.append(None)
                    else:
                        # Try to convert to number if possible
                        try:
                            if isinstance(cell, str):
                                # Remove currency symbols and commas
                                cleaned = cell.replace('$', '').replace(',', '').strip()
                                if cleaned.replace('.', '').replace('-', '').isdigit():
                                    cleaned_row.append(float(cleaned))
                                else:
                                    cleaned_row.append(cell)
                            else:
                                cleaned_row.append(cell)
                        except:
                            cleaned_row.append(cell)
                normalized_data.append(cleaned_row)

            df = pd.DataFrame(normalized_data, columns=headers)
            
            # Replace NaN/Inf with None in the entire DataFrame
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.where(pd.notnull(df), None)
            
            print(f"✅ Loaded {len(df)} rows with {len(headers)} columns")
            
            return df
            
        except HttpError as e:
            if e.resp.status == 403:
                raise PermissionError(
                    "Access denied. Please ensure you've shared your Google Sheet with the service account email "
                    "and given it at least 'Viewer' (read-only) access.\n\n"
                    "1. Open your Google Sheet\n"
                    "2. Click 'Share'\n"
                    "3. Add the service account email\n"
                    "4. Choose 'Viewer' (recommended) or 'Editor'\n"
                    "5. Click 'Share'"
                )
            elif e.resp.status == 404:
                raise ValueError(f"Sheet not found. Please check the Sheet ID: {self.sheet_id}")
            else:
                raise ConnectionError(f"Google Sheets API error: {str(e)}")
        except Exception as e:
            raise

    def get_permission_warning(self) -> str | None:
        """Return warning if service account has write access"""
        if self.has_write_access:
            return "⚠️ Your service account has EDITOR (write) access to this sheet. For security, consider changing to 'Viewer' (read-only) access."
        return None
    
    def get_permission_status(self) -> str:
        """Return the permission status as a string"""
        if self.has_write_access is True:
            return "editor"
        elif self.has_write_access is False:
            return "viewer"
        else:
            return "unknown"