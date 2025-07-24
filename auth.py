#!/usr/bin/env python3

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def selenium_login(driver, email, password, base_host):
    """
    Log into the UCalgary cards system using Selenium
    """
    login_url = f"{base_host}/login"
    driver.get(login_url)
    time.sleep(2)

    driver.find_element(By.NAME, "username").send_keys(email)
    driver.find_element(By.NAME, "password").send_keys(password)
    driver.find_element(By.NAME, "password").send_keys(Keys.RETURN)
    time.sleep(3)

    if "Logout" not in driver.page_source:
        raise RuntimeError("Login failed – check credentials")
