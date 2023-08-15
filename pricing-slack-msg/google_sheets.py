from __future__ import print_function
import os
import gspread
import os.path
import pandas as pd


def merge_dataframe():
    gs = gspread.service_account_from_dict({
        "type": os.environ['TYPE'],
        "project_id": os.environ['PROJECT_ID'],
        "private_key_id": os.environ['PRLIST_PRIVATE_KEY_ID'],
        "private_key": os.environ['PRLIST_PRIVATE_KEY'].replace('\\n', '\n'),
        "client_email": os.environ['PRLIST_CLIENT_EMAIL'],
        "client_id": os.environ['PRLIST_CLIENT_ID'],
        "auth_uri": os.environ['AUTH_URI'],
        "token_uri": os.environ['TOKEN_URI'],
        "auth_provider_x509_cert_url": os.environ['AUTH_PROVIDER'],
        "client_x509_cert_url": os.environ['PRLIST_CLIENT_URL']
    })
    sheet = gs.open_by_key(os.environ['PIPELINE_SPREADSHEET_ID'])
    worksheet = sheet.sheet1
    result = worksheet.get_all_values()
    dataframe = pd.DataFrame(result).drop(labels=None, axis=0, index=[0, 1])
    dataframe = dataframe.reset_index(drop=True)
    dataframe = dataframe.loc[:, [1, 4]]
    dataframe.columns = ['Pricelist', 'Status']
    return dataframe
