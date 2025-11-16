# Fetch data from NSE API
import os
import sys
from pathlib import Path
import requests
import pandas as pd

sys.path.append(str(Path(os.getcwd()).parent.absolute()))


class NSE_API():
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


def load_etf_data():
    # Call NSE API for ETF analysis
    nse = NSE_API()
    daily_nse_etf_data = nse._get_data("api/etf")

    # Process ETFs Data
    df_daily_etf_data = pd.DataFrame(daily_nse_etf_data.get('data'))

    # 'nav', 'ypc', 'mpc', 'xdt', 'cact', 'nearWKH', 'nearWKL'
    df_daily_etf_data_new = df_daily_etf_data.loc[:, ['symbol', 'assets', 'open', 'high', 'low', 'ltP', 'per', 'prevClose', 'qty', 'trdVal', 'wkhi', 'wklo', 'perChange365d', 'perChange30d']].copy()

    df_daily_etf_data_new['company_name'] = df_daily_etf_data['meta'].apply(lambda x: x.get('companyName'))

    df_daily_etf_data_new.rename(columns={'assets': 'underlying_asset', 
                                        'ltp': 'last_traded_price', 
                                        'per': 'percentage_change',
                                        'prevClose': 'previous_close',
                                        'qty': 'volume',
                                        'trdVal': 'value', 
                                        'wkhi': '52_week_high', 
                                        'wklo': '52_week_low',
                                        'perChange365d': 'yearly_percentage_change',
                                        'perChange30d': 'monthly_percentage_change'}, inplace=True)
    
    df_daily_etf_data_filtered = df_daily_etf_data_new[(df_daily_etf_data_new['underlying_asset'].str.contains('Nifty', case=False, na=False)) & ((df_daily_etf_data_new['company_name'].str.contains('Motilal Oswal Mutual Fund', case=False, na=False)) | (df_daily_etf_data_new['company_name'].str.contains('DSP Mutual Fund', case=False, na=False)) | (df_daily_etf_data_new['company_name'].str.contains('ICICI Prudential Mutual Fund', case=False, na=False)) | (df_daily_etf_data_new['company_name'].str.contains('Nippon India Mutual Fund', case=False, na=False)) | (df_daily_etf_data_new['company_name'].str.contains('Aditya Birla Sun Life Mutual Fund', case=False, na=False)) | (df_daily_etf_data_new['company_name'].str.contains('AXIS MUTUAL FUND', case=False, na=False)) | (df_daily_etf_data_new['company_name'].str.contains('Mirae Asset Mutual Fund', case=False, na=False)))]

    return df_daily_etf_data_filtered.reset_index(drop=True)


def get_nse_etf_data():
    nse_api = NSE_API()
    daily_nse_all_etfs_data = nse_api._get_data("api/etf").get('data')

    out = list()
    for item in daily_nse_all_etfs_data:
        # if item.get('symbol') != 'MODEFENCE':
        #     break
        empty_dict = dict()
        etf_data = nse_api._get_data(f"api/quote-equity?symbol={item.get('symbol')}")
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


if __name__ == '__main__':
    df_daily_etf_data_filtered = get_nse_etf_data()
