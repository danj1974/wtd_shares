import os

DATE_FORMAT = '%Y-%m-%d'

WTD_BASE_URL = 'https://www.worldtradingdata.com/'
WTD_API_URL = WTD_BASE_URL + 'api/v1/'
WTD_HISTORY_URL = WTD_API_URL + 'history/'
WTD_API_TOKEN = os.getenv('WTD_API_TOKEN')
