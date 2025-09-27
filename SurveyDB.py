from Units import UnitFactory
from bs4 import BeautifulSoup
import requests
import pandas as pd

class SurveyDB:
    def __init__(self, store_num='1040712'):
        self.base_url = 'http://1apebizsrv01.aafes.com/cgi-bin/find_pog_survey.pl?lkup='
        self.store_num = store_num

    def set_store(self, store_num: str):
        if len(store_num) != 7:
            raise RuntimeError('Store number must be 7 digits')
        self.store_num = store_num

    @staticmethod
    def _check_store_num(f):
        """Decorator to ensure reader is initialized before method call."""
        def wrapper(self, *args, **kwargs):
            if self.store_num == '':
                raise RuntimeError('Store number not set')
            return f(self, *args, **kwargs)
        return wrapper

    @_check_store_num
    def get_data(self):
        response = requests.get(f'{self.base_url}{self.store_num}')
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
    
    def size_of(self, pog_num):
        if 

    def _filter_trs(self, tag):
        return tag.name == 'tr' and tag.get('bgcolor') in ['azure', 'cornsilk']
    
