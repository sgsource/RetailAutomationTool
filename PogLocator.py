from Units import UnitFactory as T
from SurveyDB import SurveyDB
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import SurveyDB

class PogLocator:
    def __init__(self):
        self.url = "https://h5.aafes.com/POG/Search/ByPlanogram"

    # raises exception
    def get_pog_links(self, pog_num, survey_db: SurveyDB.SurveyDB, store_num: str, visible=False):
        chrome_options = Options()
        if not visible:
            chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(10) # waits up to seconds
        self.driver = driver

        self.driver.get(self.url)

        text_field = self.driver.find_element(By.ID, "mp_num")
        text_field.send_keys(pog_num)

        button = self.driver.find_element(By.NAME, "SubmitButton")
        button.click()

        table = self.driver.find_element(By.TAG_NAME, "table")
        rows = table.find_elements(By.TAG_NAME, "tr")

        size_href_pairs = []

        for i in range(len(rows)):
            row = rows[i]

            links = row.find_elements(By.TAG_NAME, "a")
            for j in range(0, len(links), 2):
                link = links[j]
                href = link.get_attribute('href')

                tds = row.find_elements(By.TAG_NAME, "td")
                size_str = tds[2].text

                size_href_pairs.append( [size_str, href] )

        self.driver.quit()

        # if not survey_db: url can be accessed so prompt dropdown
        # if survey_db cannot find pog_num: prompt dropdown
        try:
            pog_size = survey_db.size_of(pog_num=pog_num, store_num=store_num)
            return pog_size, size_href_pairs
        except Exception:
            return '', size_href_pairs

        # should return a status (pog found or not), sizes list (size, href pairing)
        # a followup will need to either get dropdown (should be handled in app)
        # -> then the app will have the link to feed to planogram.