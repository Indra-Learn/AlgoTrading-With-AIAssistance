# Fetch data from NSE API
import os
import sys
from pathlib import Path
import requests
import pandas as pd
import numpy as np


sys.path.append(str(Path(os.getcwd()).parent.absolute()))


class NSE_API():
    """
    helps to fetch data from NSE API
    """
    base_nse_url = "https://www.nseindia.com/"
    nse_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    def __init__(self):
        self.nse_session = requests.Session()
        self.nse_session.headers.update(self.nse_headers)
        self.nse_session.get(self.base_nse_url, headers=self.nse_headers,  timeout=10)
        self.nse_session.get(self.base_nse_url+"/option-chain", headers=self.nse_headers,  timeout=10)

    def _get_data(self, api_url):
        full_nse_api_url = self.base_nse_url + api_url
        print(f"calling {full_nse_api_url} ..")
        output = dict()
        try:
            response = self.nse_session.get(full_nse_api_url)
            response.raise_for_status()
        except Exception as e:
            print(f"error from NSE_API.get_data(): {e}")
        else:
            if response.status_code == 200:
                output = response.json()
        return output


def get_nse_etf_data(symbol: str=None):
    """
    this function
    other nse api endpoints:
        - https://www.nseindia.com/api/etf
        - https://www.nseindia.com/api/quote-equity?symbol=GROWWDEFNC
        - https://www.nseindia.com/api/quote-equity?symbol=GROWWDEFNC&section=trade_info
    """
    nse_api = NSE_API()
    daily_nse_all_etfs_data = nse_api._get_data("api/etf").get('data')

    out = list()
    for item in daily_nse_all_etfs_data:
        if symbol is not None and item.get('symbol') != symbol:
            continue
        empty_dict = dict()
        etf_data = nse_api._get_data(f"api/quote-equity?symbol={item.get('symbol')}")

        # # imp: below code will be useful for further block deal and market depth data
        # etf_trade_info_data = nse_api._get_data(f"api/quote-equity?symbol={item.get('symbol')}&section=trade_info")
        # print(etf_trade_info_data)

        empty_dict['symbol'] = item.get('symbol')

        # empty_dict['symbol'] = etf_data.get('info').get('symbol')
        # empty_dict['company_name'] = etf_data.get('info').get('companyName')
        empty_dict['asset_company'] = etf_data.get('info').get('companyName').split('-')[0]
        empty_dict['listingDate'] = etf_data.get('info').get('listingDate')
        empty_dict['segment'] = etf_data.get('info').get('segment')
        # empty_dict['is_debt_sec'] = etf_data.get('info').get('isDebtSec')
        # empty_dict['is_etf_sec'] = etf_data.get('info').get('isETFSec')
        # empty_dict['identifier'] = etf_data.get('info').get('identifier')
        # empty_dict['is_top10'] = etf_data.get('info').get('isTop10')
        empty_dict['surveillance'] = etf_data.get('securityInfo').get('surveillance').get('surv')
        empty_dict['face_value'] = etf_data.get('securityInfo').get('faceValue')
        empty_dict['issued_size'] = etf_data.get('securityInfo').get('issuedSize')
        empty_dict['expense_ratio'] = np.nan

        empty_dict['toal_market_cap'] = round((etf_data.get('securityInfo').get('issuedSize') * etf_data.get('priceInfo').get('lastPrice')) / 10000000, 2)

        empty_dict['open'] = etf_data.get('priceInfo').get('open')
        empty_dict['high'] = etf_data.get('priceInfo').get('intraDayHighLow').get('max')
        empty_dict['low'] = etf_data.get('priceInfo').get('intraDayHighLow').get('min')
        empty_dict['close'] = etf_data.get('priceInfo').get('close')
        empty_dict['ltp'] = etf_data.get('priceInfo').get('lastPrice')

        empty_dict['trade_volume'] = item.get('qty')
        empty_dict['trade_value'] = item.get('trdVal')

        empty_dict['vwap'] = etf_data.get('priceInfo').get('vwap')
        empty_dict['previous_close'] = etf_data.get('priceInfo').get('previousClose')
        empty_dict['day_percentage_change'] = round(etf_data.get('priceInfo').get('pChange'),2)
        empty_dict['inav_value'] = etf_data.get('priceInfo').get('iNavValue')
        empty_dict['52week_high'] = etf_data.get('priceInfo').get('weekHighLow').get('max')
        empty_dict['52week_high_date'] = etf_data.get('priceInfo').get('weekHighLow').get('maxDate')
        empty_dict['52week_low'] = etf_data.get('priceInfo').get('weekHighLow').get('min')
        empty_dict['52week_low_date'] = etf_data.get('priceInfo').get('weekHighLow').get('minDate')

        empty_dict['yearly_percentage_change'] = item.get('perChange365d')
        empty_dict['monthly_percentage_change'] = item.get('perChange30d')

        empty_dict['last_update_time'] = etf_data.get('metadata').get('lastUpdateTime')
        	
        out.append(empty_dict)
    
    out_df = pd.DataFrame(out)
    return out_df.reset_index(drop=True)


def get_nse_etf_data_ohlc(symbol: str, from_dt: str=None, to_dt: str=None):
    """
    this function
    other nse api endpoints:
        - https://www.nseindia.com/api/historicalOR/cm/equity?symbol=MODEFENCE
        - https://www.nseindia.com/api/historicalOR/generateSecurityWiseHistoricalData?from=17-11-2024&to=17-11-2025&symbol=MODEFENCE&type=priceVolumeDeliverable&series=ALL 
    """
    nse_api = NSE_API()
    if from_dt is None or to_dt is None:
        etf_data_monthly_ohlc = nse_api._get_data(f'api/historicalOR/cm/equity?symbol={symbol}')

        etf_data_monthly_ohlc_df = pd.DataFrame(etf_data_monthly_ohlc.get('data'))

        etf_data_monthly_ohlc_df.drop(columns=['CH_SERIES', 'TIMESTAMP', 'mTIMESTAMP', 'CH_TOT_TRADED_VAL', 'CH_52WEEK_HIGH_PRICE',	'CH_52WEEK_LOW_PRICE', 'SLBMH_TOT_VAL'], inplace=True)

        etf_data_monthly_ohlc_df.rename(columns={'CH_SYMBOL': 'symbol', 'CH_TIMESTAMP': 'timestamp', 'CH_PREVIOUS_CLS_PRICE': 'previous_close', 'CH_OPENING_PRICE': 'open', 'CH_TRADE_HIGH_PRICE': 'high', 'CH_TRADE_LOW_PRICE': 'low', 'CH_LAST_TRADED_PRICE': 'close', 'CH_CLOSING_PRICE': 'ltp', 'VWAP': 'vwap', 'CH_TOT_TRADED_QTY': 'volume', 'CH_TOTAL_TRADES': 'trades'}, inplace=True)

        etf_data_monthly_ohlc_df['timestamp'] = pd.to_datetime(etf_data_monthly_ohlc_df['timestamp'], format='%Y-%m-%d')

    elif from_dt is not None and to_dt is not None:
        etf_data_monthly_ohlc = nse_api._get_data(f'api/historicalOR/generateSecurityWiseHistoricalData?from={from_dt}&to={to_dt}&symbol={symbol}&type=priceVolumeDeliverable&series=ALL')

        etf_data_monthly_ohlc_df = pd.DataFrame(etf_data_monthly_ohlc.get('data'))

        etf_data_monthly_ohlc_df.drop(columns=['CH_SERIES', 'mTIMESTAMP', 'CH_TOT_TRADED_VAL', 'COP_DELIV_QTY', 'COP_DELIV_PERC'], inplace=True)

        etf_data_monthly_ohlc_df.rename(columns={'CH_SYMBOL': 'symbol', 'CH_TIMESTAMP': 'timestamp', 'CH_PREVIOUS_CLS_PRICE': 'previous_close', 'CH_OPENING_PRICE': 'open', 'CH_TRADE_HIGH_PRICE': 'high', 'CH_TRADE_LOW_PRICE': 'low', 'CH_LAST_TRADED_PRICE': 'close', 'CH_CLOSING_PRICE': 'ltp', 'VWAP': 'vwap', 'CH_TOT_TRADED_QTY': 'volume', 'CH_TOTAL_TRADES': 'trades'}, inplace=True)

    return etf_data_monthly_ohlc_df


def load_etf_data():
    final_etf_df_new = get_nse_etf_data().copy()

    final_etf_df_new_filtered = final_etf_df_new[(final_etf_df_new['asset_company'].str.contains('Motilal Oswal Mutual Fund', case=False, na=False)) | (final_etf_df_new['asset_company'].str.contains('DSP Mutual Fund', case=False, na=False)) | (final_etf_df_new['asset_company'].str.contains('ICICI Prudential Mutual Fund', case=False, na=False)) | (final_etf_df_new['asset_company'].str.contains('Nippon India Mutual Fund', case=False, na=False)) | (final_etf_df_new['asset_company'].str.contains('Aditya Birla Sun Life Mutual Fund', case=False, na=False)) | (final_etf_df_new['asset_company'].str.contains('AXIS MUTUAL FUND', case=False, na=False)) | (final_etf_df_new['asset_company'].str.contains('Mirae Asset Mutual Fund', case=False, na=False))]

    return final_etf_df_new_filtered.reset_index(drop=True)



if __name__ == '__main__':
    # out = get_nse_etf_data()
    # out = get_nse_etf_data(symbol='MODEFENCE')

    # out = get_nse_etf_data_ohlc(symbol='MODEFENCE')
    out = get_nse_etf_data_ohlc(symbol='MODEFENCE', from_dt='17-11-2024', to_dt='17-11-2025')

    print(out)

