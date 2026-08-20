import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException


class TestAracAramaTesti4():
    def setup_method(self, method):
        self.driver = webdriver.Firefox()
        self.wait = WebDriverWait(self.driver, 10)

    def teardown_method(self, method):
        self.driver.quit()

    def click_when_ready(self, by, selector):
        # Eleman tiklanabilir hale gelene kadar (en fazla 10 saniye) bekler, sonra tiklar.
        element = self.wait.until(expected_conditions.element_to_be_clickable((by, selector)))
        element.click()

    def test_aracAramaTesti4(self):
        # 1 | siteyi ac
        self.driver.get("https://phptravels.net/")
        # 2 | pencere boyutunu ayarla
        self.driver.set_window_size(1550, 830)

        # 3 | demo uyari penceresi cikarsa kapat, cikmazsa sorun etme
        try:
            self.click_when_ready(By.ID, "acknowledgeDemoWarning")
        except TimeoutException:
            pass

        # 4 | Cars sekmesine gec
        self.click_when_ready(By.CSS_SELECTOR, ".py-4:nth-child(3) > .text-xs")

        # 5 | pick-up kutusuna tikla
        self.click_when_ready(By.CSS_SELECTOR, "#car_pick_t .text-\\[\\#98a2b3\\]")
        # 6 | "charles" yaz
        self.driver.find_element(By.ID, "car_pick_q").send_keys("charles")
        time.sleep(0.5)  # oneri listesinin gelmesini bekle
        # 7 | onerilen listeden sec
        self.click_when_ready(By.CSS_SELECTOR, ".gap-3:nth-child(3) > .text-sm")

        # 8 | drop-off kutusuna tikla
        self.click_when_ready(By.CSS_SELECTOR, "#car_drop_t .text-\\[\\#98a2b3\\]")
        # 9 | "brus" yaz
        self.driver.find_element(By.ID, "car_drop_q").send_keys("brus")
        time.sleep(0.5)
        # 10 | onerilen listeden sec
        self.click_when_ready(By.CSS_SELECTOR, ".gap-3:nth-child(3) > .text-sm")

        # 11 | tarih kutusuna tikla (takvim acilsin)
        self.click_when_ready(By.NAME, "pickup_date")
        # 12 | gidis gunu sec
        self.click_when_ready(By.CSS_SELECTOR, ".p-0\\.2:nth-child(5) > .active")
        # 13 | donus gunu sec
        self.click_when_ready(By.CSS_SELECTOR, ".p-0\\.2:nth-child(6) > .active")

        # 14 | ara butonuna tikla
        self.click_when_ready(By.CSS_SELECTOR, ".col-span-1:nth-child(5) > .btn > svg:nth-child(1)")

        # 15 | ilk sonuca tikla
        self.click_when_ready(By.CSS_SELECTOR, ".car-card-animate:nth-child(2) .block > .w-full")