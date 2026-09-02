import time
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import ElementClickInterceptedException #eklendi, click_when_ready icin gerekli
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException #şu işe yarar: nosuchelementexception, bir elementin sayfada bulunamadığını belirtmek için kullanılır. Bu exception, Selenium WebDriver tarafından bir elementin DOM'da bulunamadığı durumlarda fırlatılır.

@pytest.fixture(params=["firefox", "chrome", "edge"])
def driver(request):
    # request.param, parametrize listesindeki degerlerden birini tasir
    # ("firefox", "chrome" veya "edge") - pytest bu fixture'i her deger
    # icin ayri ayri calistirir, yani test toplamda 3 kez kosar.
    tarayici = request.param
    if tarayici == "firefox":
        drv = webdriver.Firefox()
    elif tarayici == "chrome":
        drv = webdriver.Chrome()
    elif tarayici == "edge":
        drv = webdriver.Edge()

    yield drv  # test fonksiyonuna burada devrediliyor

    drv.quit()  # test bittikten sonra (basarili da olsa basarisiz da) calisir



def click_when_ready(driver, wait, by, selector):
    element = wait.until(expected_conditions.element_to_be_clickable((by, selector)))
    time.sleep(0.3)
    try:
        element.click()
    except ElementClickInterceptedException:
        # tam o anda baska bir sey ustune gelmis olabilir -> kisa bekle, tekrar dene
        time.sleep(0.5)
        element.click()


def click_nth_visible_day(driver, n):
    elements = driver.find_elements(
        By.XPATH,
        "//div[contains(@class, 'day') and not(contains(@class, 'disabled'))]"
    )
    visible_days = [el for el in elements if el.is_displayed()]
    time.sleep(0.3)
    visible_days[n].click()

def close_datepicker_overlay(driver, wait):
    try:
        overlay = driver.find_element(By.CSS_SELECTOR, ".datepicker-overlay")
        if overlay.is_displayed():
            try:
                overlay.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", overlay)
            wait.until(expected_conditions.invisibility_of_element_located(
                (By.CSS_SELECTOR, ".datepicker-overlay")))
    except NoSuchElementException:
        pass
    except TimeoutException:
        driver.execute_script(
            "document.querySelectorAll('.datepicker-overlay').forEach(e => e.style.display='none');"
        )
        time.sleep(0.3)

def test_aracAramaTesti4(driver):
    wait = WebDriverWait(driver, 10)

    # 1 | siteyi ac
    driver.get("https://phptravels.net/")
    # 2 | pencere boyutunu ayarla
    driver.set_window_size(1550, 830)

    # 3 | demo uyari penceresi cikarsa kapat, cikmazsa sorun etme
    try:
        click_when_ready(driver, wait, By.ID, "acknowledgeDemoWarning")
    except TimeoutException:
        pass

    # 4 | Cars sekmesine gec
    click_when_ready(driver, wait, By.CSS_SELECTOR, ".py-4:nth-child(3) > .text-xs")

    # 5 | pick-up kutusuna tikla
    click_when_ready(driver, wait, By.CSS_SELECTOR, "#car_pick_t .text-\\[\\#98a2b3\\]")
    # 6 | "charles" yaz
    driver.find_element(By.ID, "car_pick_q").send_keys("charles")
    time.sleep(0.5)  # oneri listesinin gelmesini bekle
    # 7 | onerilen listeden sec
    click_when_ready(driver, wait, By.CSS_SELECTOR, ".gap-3:nth-child(3) > .text-sm")

    # 8 | drop-off kutusuna tikla
    click_when_ready(driver, wait, By.CSS_SELECTOR, "#car_drop_t .text-\\[\\#98a2b3\\]")
    # 9 | "brus" yaz
    driver.find_element(By.ID, "car_drop_q").send_keys("brus")
    time.sleep(0.5)
    # 10 | onerilen listeden sec
    click_when_ready(driver, wait, By.CSS_SELECTOR, ".gap-3:nth-child(3) > .text-sm")

    # 11 | tarih kutusuna tikla (takvim acilsin)
    click_when_ready(driver, wait, By.NAME, "pickup_date")
    time.sleep(1)
    # 12 | gidis gunu sec (ekranda gorunen ilk gun)(driver,0)
    click_nth_visible_day(driver, -3)
    # 13 | donus gunu sec (ekranda gorunen ikinci gun)(driver,1)
    time.sleep(0.5)
    click_nth_visible_day(driver, -2)

    # 13b | takvim overlay'ini kapat
    time.sleep(0.5)
    close_datepicker_overlay(driver, wait)


    # 14 | ara butonuna tikla
    click_when_ready(driver, wait, By.CSS_SELECTOR, ".col-span-1:nth-child(5) > .btn > svg:nth-child(1)")

    time.sleep(3)

    driver.save_screenshot(f"debug_{driver.name}.png")   # <- yeni eklenen: o anki ekranin fotografini kaydet

    
    # 15 | ilk sonuca tikla
    click_when_ready(driver, wait, By.CSS_SELECTOR, ".car-card-animate:nth-child(2) .block > .w-full")

    time.sleep(2)
    driver.save_screenshot(f"debug_after_click_{driver.name}.png")   # <- yeni: 15. adimdan sonra nerede oldugumuzu gorelim

        # 16 | "Book Now" butonuna tikla
    click_when_ready(driver, wait, By.XPATH, "//button[contains(., 'Book Now')] | //a[contains(., 'Book Now')]")
    time.sleep(3)
    driver.save_screenshot("f^debug_after_booknow_{driver.name}.png")

    