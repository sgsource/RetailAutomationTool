from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException
import time
import pandas as pd

class LabelGenerator:
    def __init__(self):
        # ft meade only for now
        self.start_url = 'https://prodasapapp1.aafes.com:7002/ords/ftmeade/f?p=ASAP_HH_BASE:LOGIN_DESKTOP:0::::P9999_EXCHANGE,P9999_PATH_VAR:FTMEADE,BETABASE'
        
        self.driver = None
        self._reset_driver()

    def _reset_driver(self, visibility=False):
        if self.driver:
            self.driver.quit()
        
        if visibility:
            self.driver = webdriver.Chrome()
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new") 
            self.driver = webdriver.Chrome(options=options)
        self.driver.implicitly_wait(120)

    def _click_button_by_id(self, id: str):
        self.driver.find_element(By.ID, id).click()
    
    def _fill_input_by_id(self, id: str, text: str, enter=False):
        input_field = self.driver.find_element(By.ID, id)
        input_field.send_keys(text)
        if enter:
            input_field.send_keys(Keys.ENTER)

    def _click_link_by_id_index(self, ul_id: str, li_index: int, verbose=False):
        ul_element = self.driver.find_element(By.ID, ul_id)

        li_elements = ul_element.find_elements(By.TAG_NAME, 'li')
        if verbose:
            for li in li_elements:
                print(f'li{li.text}')

        a_element = li_elements[li_index].find_element(By.TAG_NAME, "a")
        a_element.click()

    def _select_by_index(self, id: str, index: int):
        time.sleep(2)

        dropdown = self.driver.find_element(By.ID, id)
        select = Select(dropdown)
        select.select_by_index(index)

    def _scan_labels(self, df: pd.DataFrame):
        crcs = df.index.to_list()

        for _, crc in enumerate(crcs):
            self._fill_input_by_id('P127_LOOKUP_NBR', crc, enter=True)

            upc = df.loc[crc, 'UPC'][:-1] # trim last digit

            last_scanned_info = self.driver.find_element(By.ID, 'P127_INFO').text
            print(last_scanned_info)
            locator = (By.ID, 'P127_INFO_CONTAINER')
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.text_to_be_present_in_element(locator, upc)
                )
            except TimeoutException:
                print(f'timed out for {upc} but continuing...')
        # all done. click submit
        time.sleep(2)
        self._click_button_by_id('B4986078001920273596')
        time.sleep(2)

    def generate_labels(self, df: pd.DataFrame, credentials, visibility=False):
        self._reset_driver(visibility=visibility)

        self.driver.get(self.start_url)

        self._click_button_by_id('B5975482935189201124')

        # sign in
        yid, pwd = credentials

        self._fill_input_by_id('P9000_USERNAME', yid)
        self._fill_input_by_id('P9000_PASSWORD', pwd)

        self._click_button_by_id('B3766789551193137132')

        # navigating...
        self._click_link_by_id_index('3763435963668262110', 2)
        self._click_link_by_id_index('5702700700995105695', 1)

        # setting up generation
        self._fill_input_by_id('P127_BATCH_DESC', 'AutoLabelGen')
        self._select_by_index('P127_PRINT_PRICE_INDCT', 1)
        self._click_button_by_id('B4986085331857273610')

        self._select_by_index('P127_LOOKUP_TYPE', 1)
        time.sleep(2)

        self._scan_labels(df)
        self.driver.quit()
