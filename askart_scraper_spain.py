import requests
from selenium import webdriver
from urllib.parse import urljoin
from requests_ip_rotator import ApiGateway, EXTRA_REGIONS
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import re
import json
import time
import pickle
import random
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import Select

def login(driver, u, p):
    driver.get('https://www.askart.com/')
    print("Log in on the browser. Return and enter any key to continue.")
    wait = input("Enter input to continue: ")
    driver.get("https://askart.com/")

def search(first, last, driver, firstid="MainPageContent_txtFirstName", lastid="MainPageContent_txtLastName"):
    # fill search bar and search
    fname = driver.find_element_by_id(firstid)
    fname.send_keys(first)
    # fill last
    lname = driver.find_element_by_id(lastid)
    lname.send_keys(last)
    # hit return
    lname.send_keys(Keys.ENTER)

def filter_search(select_id, select_val):
    # click filter/sort
    driver.find_element_by_id("FilterDescription").find_element_by_tag_name("span").click()
    # get selecter
    select = Select(driver.find_element_by_id(select_id))
    select.select_by_value(select_val)


def parse_lots(soup, artist, d):
    # iterate over each lot
    lots = soup.find_all("div", {"class":"LotDiv"})
    for lot in lots:

        title = lot.find("h3").text.strip()

        # try to get production year
        try:
            year = int(title.split(",")[-1])
        except:
            year = None

        # for each row, add info
        rows = lot.find_all("div", {"class":"LotRow"})

        # lot rows
        hammer = rows[0].findChildren()[1].text.strip()
        est = rows[1].findChildren()[-1].text.strip()

        # more rows
        flex = lot.find_all("div", {"class":"d-flex"})

        # a tags for flex rows have date and auction house
        sell_date = flex[0].find("a").text.strip()
        auction_house = flex[1].find("a")
        ah_name = auction_house.text.strip()
        ah_link = auction_house["href"]

        dims = flex[1].findChildren()[-1].text.strip()

        # store in dict
        d[artist].append((title, year, hammer, est, sell_date, ah_name, ah_link, dims))

options = Options()
options.page_load_strategy = 'normal'
driver = webdriver.Firefox(options=options)
driver.implicitly_wait(5)
BASE_URL = "https://www.askart.com/Search.aspx"
artists_path = "artists.txt"
prev_url = BASE_URL

# establish requests
gateway = ApiGateway(BASE_URL)
gateway.start()
session = requests.Session()
#passing the cookies generated from the browser to the session
#c = [session.cookies.set(c['name'], c['value']) for c in driver.get_cookies()]

session.mount(BASE_URL, gateway)

# load in artists into list, set, and dictionary
#artists = [a.strip() for a in open(artists_path, "r")]
a_info = {}
letters = ['c','d','e','f','g','h','i','j','k','l','m','n','o',
        'p','q','r','s','t','u','v','w','x','y','z']
ix = 0
driver.get(BASE_URL)

for start_let in letters:
    #if artist == "Pablo Picasso" or artist == "Salvador Dalí":
    #    print(f"Skipping {artist}")
    #    continue
    print(f"-----\nStarting {start_let}")
    ix += 1

    # go to artprice.com
    driver.get(BASE_URL)

    # filter to spain, 1909-1989, 500 results per page
    filter_search('MainPageContent_selectCountry', 'Spain')
    time.sleep(1)
    filter_search('MainPageContent_selectYearStart', '1910')
    time.sleep(1)
    filter_search('MainPageContent_selectYearEnd', '1989')
    time.sleep(1)
    select = Select(driver.find_element_by_id("MainPageContent_RecordsPerPage"))
    select.select_by_value("500")
    time.sleep(1)

    # search
    search("*", start_let, driver)
    time.sleep(1)

    # iterate over each artist
    # get all links
    links = driver.find_elements_by_class_name("blueLink")
    print(f"Parsing {len(links)} links")
    for i in range(len(links)):
        links[i] = links[i].get_attribute("href")

    for link in links:
        driver.get(link)
        artist = driver.find_element_by_tag_name("h1").text.split("\n")[-1]

        # check if has auction results
        try:
            driver.find_element_by_id("divAuctionRecords")
        except:
            print(f"No auction records for {artist}")
            continue

        # filter by paintings
        # click filter/sort
        time.sleep(.5)
        driver.find_element_by_id("FilterDescription").find_element_by_tag_name("a").click()
        time.sleep(.5)
        # get selecter
        select = Select(driver.find_element_by_id('MainPageContent_selectArtworkType'))
        try:
            select.select_by_value('Painting')
        except:
            print(f"No paintings for {artist}")
            continue

        # while there is still a show more records button to click, scroll to bottom, click, repeat
        while True:
            # scroll to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # try clicking the load more
            try:
                driver.find_element_by_id("ShowMoreRecords").click()
            except:
                break

            # wait while the spinner is still there
            while driver.find_element_by_id("spinner").value_of_css_property("display") == "block":
                continue


        soup = BeautifulSoup(driver.page_source, "html.parser")
        a_info[artist] = []

        parse_lots(soup, artist, a_info)

        # temporarily save results
        pickle.dump(a_info, open("a_z2.pkl", "wb"))

print(a_info)
