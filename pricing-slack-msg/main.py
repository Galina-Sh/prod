import datetime
import os
from tabulate import tabulate
import pandas as pd
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import pandas.io.sql as psql
import logging
import google_sheets
from sqlalchemy import create_engine, text

client = WebClient(token=os.environ['MA_SLACK_BOT_TOKEN'])
logger = logging.getLogger(__name__)
channels_id_to_write = ['GLJJ6R58B', 'G01F7RCTA5R'] # ['GLJJ6R58B', 'G01F7RCTA5R']  # 'GLJJ6R58B' - production-team, 'G01F7RCTA5R' - production-price, 'C02L1262NKZ' - test-bot-3


class sql_conn(object):
    def __init__(self):
        self.url_quotes = f"postgresql://{os.environ['USER']}:{os.environ['PASSWORD']}@{os.environ['QUOTES_HOSTNAME']}:{'5432'}/quotes"
        self.engine2 = create_engine(self.url_quotes, pool_size=50, echo=False)
        # self.url_prod = f"postgresql://{os.environ['USER']}:{os.environ['PASSWORD']}@{os.environ['MYJET_HOSTNAME']}:{'5432'}/myjet"
        # self.engine1 = create_engine(self.url_prod, pool_size=50, echo=False)

    # def get_view_1000_locations(self):
    #     data_set_from_sql_1000_parking_locations = psql.read_sql(
    #         """SELECT icao_code as Pricelist , cnt as airport FROM public.last_1000_parking_locations""",
    #         self.engine1)
    #     data_set_from_sql_1000_parking_locations.index += 1
    #     return data_set_from_sql_1000_parking_locations

    def get_view_300000_locations(self):
        data_set_from_sql_300000_legs_locations = psql.read_sql(
            sql=text("""SELECT icao as Pricelist, cnt as airport FROM public.last_300000_legs_locations WHERE this_month = 'true'"""), con=self.engine2.connect())
        data_set_from_sql_300000_legs_locations.index += 1
        return data_set_from_sql_300000_legs_locations

dict_month = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December"
}

now_month = datetime.datetime.now().month
now_year = datetime.datetime.now().year
# now_day = datetime.datetime.now().day
# number_of_week = (now_day - 1) // 7 + 1

sql_conn = sql_conn()
# view_to_send_1000_locations = sql_conn.get_view_1000_locations()
view_to_send_300000_locations = sql_conn.get_view_300000_locations()
final_view = pd.concat([view_to_send_300000_locations])
rename_final_view = final_view.rename(columns={"pricelist": "Pricelist"})
final_view_concat = rename_final_view.groupby(['Pricelist']).sum()
order_by_view = final_view_concat.sort_values(by=['airport'], ascending=False)
data_frame_to_merge = google_sheets.merge_dataframe()
merged_view = order_by_view.merge(data_frame_to_merge, how='left', on='Pricelist').reset_index(drop=True)
merged_view.loc[(merged_view['Status'] == 'In Request'), 'Status'] = 'Not Done'
merged_view.loc[(merged_view['Status'] == 'Checked'), 'Status'] = 'Done'
merged_view.loc[(merged_view['Status'] == 'Not Started'), 'Status'] = 'Not Done'
merged_view.fillna('Not Done', inplace=True)
merged_view_rename_column = merged_view.rename(columns={"airport": "Count"})

view_done = merged_view_rename_column.loc[merged_view_rename_column['Status'] == 'Done']
view_not_done = merged_view_rename_column.loc[merged_view_rename_column['Status'] == 'Not Done']
head_done = min(view_done.shape[0], 20)
head_not_done = min(view_not_done.shape[0], 20)
view_done_final = view_done[['Pricelist', 'Count']].head(head_done)
view_not_done_final = view_not_done[['Pricelist', 'Count']].head(head_not_done)
view_not_done_final.reset_index(drop=True, inplace=True)
view_done_final.reset_index(drop=True, inplace=True)
view_done_final.index += 1
view_not_done_final.index += 1
pd.set_option('display.max_rows', None)
table_done = tabulate(view_done_final, showindex=True, headers=view_done_final.columns, tablefmt='pipe')
table_not_done = tabulate(view_not_done_final, showindex=True, headers=view_not_done_final.columns, tablefmt='pipe')

print(table_done)
print(table_not_done)


for i in channels_id_to_write:

    def send_slack_messages():
        try:
            client.chat_postMessage(
                mrkdwn=True,
                channel=i,
                text="Top covered {} locations for {} {}:".format(head_done, dict_month[now_month],now_year)
                     + '```' + table_done + '```' + "\n"
                     "Top uncovered {} locations for {} {}:".format(head_not_done, dict_month[now_month],now_year)
                     + '```' + table_not_done + '```'
            )
        except SlackApiError as err:
            print("Error creating conversation: {}".format(err))
            logger.error("Error creating conversation: {}".format(err))

    send_slack_messages()