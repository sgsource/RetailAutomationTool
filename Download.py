from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import pathlib

class Download:
    def __init__(self): pass

    def _download(self, lan_id: str, visible=False):
        chrome_options = Options()
        if not visible:
            chrome_options.add_argument("--headless=new")  # headless mode

        driver = webdriver.Chrome(options=chrome_options)
        driver.implicitly_wait(30)

        # Go to Outlook
        driver.get('https://outlook.office365.com/mail/')

        # Sign in
        email_input = driver.find_element(By.ID, 'i0116')
        email_input.send_keys(f'{lan_id}@aafes.com')
        driver.find_element(By.ID, 'idSIButton9').click()

        # Wait briefly for inbox to load
        time.sleep(5)  # can replace with explicit wait if needed

        # Find email with attachments
        partial_text = 'Has attachments machine PCL Report from ASAP PMrpt'
        partial_match_element = driver.find_element(By.XPATH, f"//*[contains(@aria-label, '{partial_text}')]")
        partial_match_element.click()

        # Find PDF attachment
        partial_text = '.pdf'
        attachment_element = driver.find_element(By.XPATH, f"//*[contains(@aria-label, '{partial_text}')]")
        filename = attachment_element.text
        attachment_element.click()
        time.sleep(2)

        # Click download
        download_button_text = 'Download'
        download_element = driver.find_element(By.XPATH, f"//*[contains(@aria-label, '{download_button_text}')]")
        download_element.click()
        time.sleep(2)

        driver.quit()
        return filename.split('\n')[0]

    def _get_full_path(self, filename: str):
        home_directory = pathlib.Path.home()
        downloads_path = home_directory / "Downloads"
        return str(downloads_path / filename)

    def get_pdf(self, lan_id: str, visible=False):
        filename = self._download(lan_id=lan_id, visible=visible)
        return self._get_full_path(filename)
