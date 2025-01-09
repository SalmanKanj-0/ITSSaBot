import os
import json
import time
import logging
import threading
from cryptography.fernet import Fernet
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Encrypted JSON service account key (replace with your actual encrypted bytestring)
ENCRYPTED_JSON = b"gAAAAABnUFR7ASYkgf8nyLY06KKFTQpFDCc_MeaaTTKIKaue2Wg_6isIqfACtJ3Qtt4m7p57JwhaeShMVFgRlGB6_ccLjYDOAnqiXqSIw_PX6Y289UQPpLiJJ0B0w3vONlPH5f6qD_l4O-ymK92upYkRWxv7-Bw_szj6MUEsYXPQUZpcdGyS9itfn1Od1fp3D8irHX7zOBlRblg43wmrnk_u9imcx-Xtgwky_M3zb4TXx27aI9upGUYfq6FRG6-WwYrUclRkSk3TLMh5Eyv_hYYCRhqw_sgjjYnrmRDQETKUHfl1LObFPCOODDrpqChhWnEsd6FJHCzNdXVFU-UKBfYKvT4nTnm5r8_O7DeHPJV_H_YNT8VGrF_SJ2l6xRR8LJChAzaj03JBDBvGX3BAieU8iDAufjl7hJfAyUvPjS2Aka-hoXjd0mRrM3qs2uLwJO182XnoFUYVDy51EGiNkAjyLbmVqm5O5qdIIbXYzcicmQxWhhJdixq-ezh10yJfdxZQ2hv390xWFlpT27HMG4quFQ9FoMGIgUPJHxb_Ml03F2pE2JD3xORSJL01gGlWuZ6XV8fpQHghYlFxQH8M0Xl0eGMhsgjDUfcc8HD8ymFB5qTVZ7gWs4acLEERSkg6m64PhaPz1TXJsHjseCKtKolVBHMHxQeVf7jZqorZIBz3BQAXed2Gt7Yzc20L88J2P31kOfwV5Z75hcTMcjn_b7qXpKdhwvYWSCKEARcFEx438JVMxSBmJXdjO63ZMOfb4QCq7n3R2gw6L7LQAtL61WdQUu_igXJM7Jlm6VnBU_ZI7oeijQlmqc3NESjoPtHZHhw-qfY5A-K-L4tAIM34Fac4iH7sXLu3O4RE20gTcC0WzK5WZes0_mVwHG2B9LJbUIXp1ii5HyKj2W5lgQRtcue1nsRxWQl5Tth2RRFsIXIHJoudYRiF1Wjr8KSt-ABIVcSRsVP4-ag15TXWnm6G3d6oM9WUgRjTygBGKU_CElIpxv9xR-MMJ5-X_AZYTGLDuSaVAqbJO7kdZFrQdO8Qj6u_BTHphRSFRkXUnHcPorSmzBeyn1pMdWkQlw9hcdKg8aLKzjBbER2kjbtcJhRcEffS-AErosmo2ryEo-GwhyQiQ5tFdmX62GgDQJwMvMUVEZPHGbvG3AkN0b1AZz32L8iH0h3XTmqKRqjbb2LEacwWYlKNlMA6QWNkU2b4ujSzqClmJSTQs-BrVJ4k---bq7ETnbBEIUO4p7KexS52mzP8gYj822Bob5Wytg74yvNOVECDEK3utKcIUC3S-rSAr1XR2Aamh0SQtSBvnvwbOsWX6kp1s0O-iJZnicfhOUUFBSQHXGD9Q4SehGnxqTzISm_TGNBo09eHN6sHf7aKCv68uugNdFBRMoJVjs8IIA34OaizZzdf0cSZJj5nzcQTuBbo-Tl1d2spPn6AlV3HUmwHf71nGh7v5HpOc5kxf8TR25ArD1j6Ld-oq784Ei5nStEl8iry0reIV39Z3lNqG2DIrDa-9bXce0nLbCTT8eAHteomt6TETicI7Z6WEf7Og-W2m4t95VyDCmBdjxq0i0BiSz_tnFE3Uh9EZ3qv6MMt_ar5d0fWKE1CRkFaq7FODmLxH0uJ5unwLZGSwQ926VZovt-rsjyH1QmKpHE8wsa3lTJH6kLWf7ALPHnfcTpyn9Ganck6aSa5xcPBs3f1iwk441yDR2AZX0aDoGPkXimmu_FqOO0QJMnkhw30McDFxZ7l3VZjN1SZDAhtyVQCpE_wHHg7Xinrowc8iHwuinOSPxCIMjkrmbf45_a5Y2tEUsargdGyrYqUuXrpHiE_jLeaZ8Ptc_uZ4NBBooPQCBfHZu6Sa5byKgGj1VOGQMWgUVObi27Q-FtRbdVEf4z2wYpaO8cZRARfpSTX9sX4_oRIXcUWPTYDC1C2A4FZr43vGwxmi9pBX76fdur3QEIn2QUW-sa0JFlbAr1LVJ-cG6v5NCk-wjl__o6ybRyV5p3_3nqAAduOrasKRoCPmYngquhht9ZgfMVhiMWU-ro-2niLZvgZEscDVLIP7IU1yycH_Ty6_YVUQ_d9yaiBEuH_sKnzYpfBE6012EteK8vg7ozeDyz-z0YKH8QC_G40vxEF18IvZPx0aMvChETZDzUFNC093xsSYVZgmdp2utkhOEKdBuKFETkMaqNE7IKc-_gALNQJieQllI_jJudE7pvrk-_RCGARjl1qcmmxe5WAE6gwROsTWmKrxPxdaVJdQL64hWQc70cICaPi7UWCMVqCVy3Yhcs4tK_U5rpf2hq8oNCb-OWidjXUuNC42k6nWKH_I9O5uRVHu0zkFNsCswCje2cbTphl7xW1nx2UR22fBx5ioZONAEbvP1nQOPLc5wMenTm6cMXXNHT0ce-DvLYiHT_jEwm1NVwSt-1ElJFRkeLw8M2NMr4brV9ZVrkQlje8rs-ia7Qs_KcgCmKwNzYUbx6S5_TicUOk4kUyXQSmzJSEQpFeR0nYq3NMj3EdQ9ALpTIt34p8lC3Rxapiwr5bg1xsVj52Y2gVKBQtybBvUgajU7gQSD06Rh8L46Sjec0UC_BwkL5YO73R4TuJMgIrEDohG8PqHqob1yejJ5t3ZJcxIT0pRo1c_I823q4X3hotrTlHfIDhOhQnWpsR3l6zVHDUq7R1Sq9Av32A0QEwCfBJqKCRjR_1f4JmCdc_OByejZTU0AhU01sXnz_Z965dhy5_VkxCmea4E3tw23j6oB4Xk-kcAxUK5VwxSDFho97MNeo466u3MWwSJ-2fLsIrwXX5xkxmWZhKq9225MDm3NrVI6fYS_5DGHUWEhzxTpNnUUuDgwxDcAL5pkicAYZQsFmBIvgX5eccdv7vOYYMuNm4dc0g5qu0K4yYYkM6mWo1InWryJ5EGLM9n9gWeNfG-MN9RCC_QhHqjOzPijADJzlesVBF5N577z2c0-A85_cnFxaiiYvkGHuDSPZxuSu6olQlKeL7aYi-HgY_aXgzc3nZlO74w0Zf_dXSA_u6p2D3LNr3i3PzJA9OQqiTPA7OWMlUCAQQqvOC_PGYCCXhGVV7zv8SpfSfGbdjSnz6gAYc6PMoDo-n1UCTrZcxP6LwD4l2VI3hMbKp391XH4pymlOwk8Jv-j2-pl2XX1PUEQoIO114YslnEYJOlKZ60KlhjiOdhuAPcF5SvSw="  # Make sure to keep the 'b' prefix

# Get decryption key from environment variable
DECRYPTION_KEY ="ZRDNAJbZi394lmgW4Tqpb_jteSu5Rdx8rX08YNDkmhk="
if not DECRYPTION_KEY:
    raise ValueError("Decryption key not found in environment variables.")

# Initialize global variables for credentials and service
decrypted_json = None
service = None

def initialize_service():
    global decrypted_json, service
    if decrypted_json is None or service is None:
        try:
            # Decrypt the JSON credentials
            fernet = Fernet(DECRYPTION_KEY)
            decrypted_json = json.loads(fernet.decrypt(ENCRYPTED_JSON).decode())

            # Authenticate with Google Sheets API
            credentials = Credentials.from_service_account_info(
                decrypted_json,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            service = build('sheets', 'v4', credentials=credentials)
            logger.info("Google Sheets service initialized.")
        except Exception as e:
            logger.error(f"Error initializing Google Sheets service: {e}")
            raise

# Google Sheets details
SPREADSHEET_ID = '176Qo1lKMwSwFi84HomyfGLs5CNwL1ADf1WMVOOoYsy8'  # Replace with your actual spreadsheet ID
RANGE_NAME = 'Sheet1!A1:D'  # Adjust the range as needed

def append_to_sheet(ticket_number, feedback, user_email):
    """
    Appends feedback to the Google Sheet.
    """
    try:
        initialize_service()

        # Prepare the data to append
        values = [
            [ticket_number, feedback, user_email, time.strftime("%Y-%m-%d %H:%M:%S")]
        ]
        body = {"values": values}

        # Append the data to the sheet
        sheet = service.spreadsheets()
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=RANGE_NAME,
            valueInputOption='RAW',
            body=body
        ).execute()

        logger.info(f"{result.get('updates').get('updatedCells')} cells appended to the Google Sheet.")
    except Exception as e:
        logger.error(f"Error appending to Google Sheet: {e}")

def append_to_sheet_async(ticket_number, feedback, user_email):
    """
    Runs append_to_sheet in a separate thread to make it asynchronous.
    """
    def task():
        try:
            append_to_sheet(ticket_number, feedback, user_email)
        except Exception as e:
            logger.error(f"Error in asynchronous append_to_sheet: {e}")

    thread = threading.Thread(target=task)
    thread.start()