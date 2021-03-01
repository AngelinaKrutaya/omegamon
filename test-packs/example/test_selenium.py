from os.path import join
from time import sleep

import pytest
from selenium import webdriver
from taf import logging
from taf.af_support_tools import Config, IssueID, TafVars
from taf.selenium_helper import ScreenshotOnFailure

logger = logging.getLogger(__name__)
logger.setLevel('INFO')

c = Config().get_section('web_info')


@pytest.mark.example
@pytest.mark.parametrize('browser', [
                         pytest.param(webdriver.Chrome, id='browser: Chrome'),
                         pytest.param(webdriver.Firefox, id='browser: Firefox')])
@IssueID('ESTS-140410')
def test_selenium(browser):
    """
    Description : This sample test is designed to demonstrate some simple Selenium operations in Chrome and Firefox.
    This test also demonstrates a data driven test by reading properties from a configuration file.
    """
    my_url = c['url']
    my_title = c['title']

    s_driver = browser()
    s_driver.get(my_url)

    browser = s_driver.name
    logger.info('Test Browser In Use = %s' % browser)

    assert my_title.lower() in s_driver.title.lower(),\
        f"'{my_title.lower()}' not found within '{s_driver.title.lower()}'"
    s_driver.close()


@pytest.mark.xfail
def test_selenium_screenshot():
    def get_driver(obj):
        return obj.driver

    scr = ScreenshotOnFailure(logger=logger, get_driver_method=get_driver, path=join(TafVars.af_base_path, 'reports', 'all'))

    class MyClass:
        def __init__(self):
            self.driver = webdriver.Chrome()

        def __del__(self):
                try:
                    self.driver.quit()
                except:
                    logger.warning('driver is closed correctly, but unknown exception is raised. suppressing')
                    pass

        @scr
        def my_method(self):
            self.driver.get('https://ya.ru')
            sleep(2)
            self.driver.find_element_by_xpath('.//*[@id="12345"]')

    m = MyClass()
    m.my_method()


@pytest.mark.skip('requires external Windows VM with a Selenium Node having Edge')
def test_selenium_grid_edge(request):
    """
    see https://wiki.rocketsoftware.com/display/QE/Selenium+Grid
    """
    from taf.selenium_helper import selenium_node_check
    selenium_hub = 'http://x.x.x.x:4444/wd/hub'
    browser = 'MicrosoftEdge'
    os = 'WINDOWS'
    assert selenium_node_check(selenium_hub, browser, os)  # wait for the node to arrive online
    driver = webdriver.Remote(command_executor=selenium_hub, desired_capabilities={'browserName': browser, 'platform': os})
    driver.get('https://google.com')
    sleep(3)
    assert driver.title == 'Google'
    driver.quit()
