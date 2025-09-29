from Units import UnitFactory
from bs4 import BeautifulSoup
import requests
import pandas as pd

class SurveyDB:
    def __init__(self, store_num):
        self.base_url = 'http://1apebizsrv01.aafes.com/cgi-bin/find_pog_survey.pl?lkup='
        self._get_data(store_num)

    def _get_data(self, store_num):
        self.store_num = store_num

        # if url does not exist, may raise exception
        # needs to be caught by caller
        response = requests.get(f'{self.base_url}{store_num}')
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        trs = soup(self._filter_trs)

        pog_nums = []
        sizes = []

        for tr in trs:
            tds = tr('td')
            size_str = tds[-2].get_text()

            pog_num = tds[-4].get_text()
            size = UnitFactory.create(size_str)

            pog_nums.append(pog_num)
            sizes.append(size)
        
        self.survey_df = pd.DataFrame({'Size': sizes}, index=pd.Index(pog_nums, name="PogNum", dtype='str'))
    
    def size_of(self, pog_num, store_num):
        if store_num != self.store_num:
            self._get_data(store_num)
        if pog_num not in self.survey_df.index:
            raise RuntimeError('Cannot find pog in survey db')
        return self.survey_df.loc[pog_num, 'Size']

    def _filter_trs(self, tag):
        return tag.name == 'tr' and tag.get('bgcolor') in ['azure', 'cornsilk']
    
