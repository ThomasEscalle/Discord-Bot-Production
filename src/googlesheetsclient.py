import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta


# Fonction pour convertir
def convert_google_sheet_date(serial_number):
    base_date = datetime(1899, 12, 30)
    return base_date + timedelta(days=float(serial_number))


class GoogleSheetsClient:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets'
        ]

        # Load credentials from the JSON file
        self.credentials = Credentials.from_service_account_file(
            'credentials/credentials_google_sheets.json', 
            scopes=self.scopes
        )

        # Authorize the client
        self.client = gspread.authorize(self.credentials)

        self.sheet_id = "1mpfqGK2wINPT3bQdNzNSCa91kNna2qWHdSwYDwtKYas"
        self.sheet = self.client.open_by_key(self.sheet_id)

        # Get the first worksheet
        self.worksheet = self.sheet.get_worksheet(1)  




    # Get the row that corresponds to the date
    def get_row_by_date(self, date):
        # Get the "B" column values
        column_values = self.worksheet.col_values(2, value_render_option='UNFORMATTED_VALUE')

        # Find the index of the date in the column values
        matin, apres_midi = None, None
        for i, value in enumerate(column_values):
            
            if value == "":
                continue

            # Convert the serial number to a date
            try:
                value = float(value)
            except ValueError:
                continue

            # Convert the serial number to a date
            value = convert_google_sheet_date(value).strftime('%m/%d/%Y')

            # Check if the value matches the date
            if value == date and matin == None:
                matin = i
            elif value == date and matin != None:
                apres_midi = i
                break


        #If the morning was found, get the values of the row
        if matin != None:
            matin = self.worksheet.row_values(matin + 1, value_render_option='UNFORMATTED_VALUE')

        #If the afternoon was found, get the values of the row
        if apres_midi != None:
            apres_midi = self.worksheet.row_values(apres_midi + 1, value_render_option='UNFORMATTED_VALUE')

        return [matin, apres_midi]
