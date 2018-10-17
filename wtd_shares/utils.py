from datetime import datetime, timedelta
import json
import requests

from pandas import DataFrame

from wtd_shares import settings


def date_format(date):
    """
    Return a string representation of the date in the preferred format.

    Default format is defined by settings.py.DATE_FORMAT

    :param datetime date: the date to format
    :return: str
    """
    return date.strftime(settings.DATE_FORMAT)


def get_wtd_query_params(symbol="UKX", start_date=None, end_date=None, previous_days=300, sort='oldest'):
    """
    Return a set of query params for WTD stock query.

    The `end_date` will default to today if not provided.
    If a `start_date` is provided then `previous_days` will be ignored.

    :param str symbol: the stock symbol to fetch (default = 'UKX')
    :param datetime start_date: the start_date
    :param datetime end_date: the end date
    :param int previous_days: number of previous days data to fetch
    :param str sort: the sort key (default='oldest')
    :return: dict
    """
    # if an end date isn't provided, assume it should be today
    # TODO - or this could default to the most recent Friday (or Saturday) to ensure only full weeks are processed
    if not end_date:
        end_date = datetime.today()

    # if an explicit start date is not provided then we calculate it using the 'previous_days' argument (default=300)
    if not start_date:
        start_date = end_date - timedelta(days=previous_days)

    params = {
        'symbol': symbol,
        'sort': sort,
        'date_from': date_format(start_date),
        'date_to': date_format(end_date),
        'api_token': settings.WTD_API_TOKEN,
    }

    return params


def get_atr_dataframe(symbol='UKX', start_date=None, end_date=None, previous_days=300, sort='oldest'):
    """
    Return a `pandas.DataFrame` object with calculated ATR data for a stock.

    :param str symbol: the stock symbol to fetch (default = 'UKX')
    :param datetime start_date: the start_date
    :param datetime end_date: the end date
    :param int previous_days: number of previous days data to fetch
    :param str sort: the sort key (default='oldest')
    :return:
    """

    # get a dictionary representing the query parameters for the request
    query_params = get_wtd_query_params(
        symbol=symbol, start_date=start_date, end_date=end_date, previous_days=previous_days, sort=sort
    )

    # send an http GET request to the WTD api (the 'params'
    response = requests.get(settings.WTD_HISTORY_URL, params=query_params)

    data = json.loads(response.text)

    # example response:
    # data = {
    #     "name": "UKX",
    #     "history": {
    #         "2018-10-16": {
    #             "open": "7029.22",
    #             "close": "7059.40",
    #             "high": "7062.08",
    #             "low": "6998.93",
    #             "volume": "0"
    #         }
    #     }
    # }

    # read the history section of the response
    history = json.dumps(data['history'])

    # load into a DataFrame and transpose the row/columns axes
    df = DataFrame(history).transpose()

    # add columns and calculate values for new data derived from the OHLC data
    # today's high-low difference
    df['TH-TL'] = df['high'] - df['low']
    # when using yesterday's values we can use the .shift() method to refer to the previous row
    df['TH-YC'] = abs(df['high'] - df['low'].shift(1))
    df['TL-YC'] = abs(df['low'] - df['close'].shift(1))
    # to get the maximum
    # df[['TH-TL', 'TL-YC']] creates a new dataframe using only the values from the column headers provided
    # .max then returns the maximum value in the dataframe across each column (axis=1)
    df['True Range'] = df[['TH-TL', 'TL-YC']].max(axis=1)

    # to calculate values from a rolling window we follow these steps:
    #   - get the column of data to be used:  df['True Range'], which is a pandas.Series object
    #   - use the .rolling() method to perform a rolling window calculation, the first argument
    #     is the size of the moving window, 14.
    #   - to each window apply an anonymouse (lambda) function to sum the data in the window and divide by 14
    df['ATR (sma)'] = df['True Range'].rolling(14).apply(lambda x: sum(x) / 14)

    return df
