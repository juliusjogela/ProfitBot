import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.driver_setup import setup_driver
from selenium.webdriver.chrome.webdriver import WebDriver

def test_driver_starts_and_quits():
    driver: WebDriver = setup_driver()
    assert isinstance(driver, WebDriver)
    driver.quit()
