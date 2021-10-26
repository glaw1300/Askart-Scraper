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
import tqdm

def login(driver, u, p):
    driver.get('https://www.askart.com/')
    print("Log in on the browser. Return and enter any key to continue.")
    wait = input("Enter input to continue: ")
    driver.get("https://askart.com/")

def search(name, driver, searchid="MainPageContent_txtAuctionHouse"):
    # fill search bar and search
    search = driver.find_element_by_id(searchid)
    search.clear()
    search.send_keys(name)
    # hit return
    search.send_keys(Keys.ENTER)

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
        hammer = rows[0].findChildren()[-1].text.strip()
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

driver = webdriver.Firefox()
driver.implicitly_wait(5)
BASE_URL = "https://www.askart.com/Search_Auction_Houses.aspx"

# load in artists into list, set, and dictionary
data = pickle.load(open("master.pkl", "rb"))

# get set of auction houses
ahs = set()
for vals in data.values():
    for v in vals:
        ahs.add(v[5])

# have to do this twice for some reason
driver.get(BASE_URL)
driver.get(BASE_URL)

ahmap = {}

for ah in tqdm.tqdm(ahs):
    fail = True
    while fail:
        try:
            # search
            search(ah, driver)
            time.sleep(2)

            info = driver.find_element_by_css_selector(".sticky-top-filtercount~div").text

            if "No records match the filter criteria" in info:
                print(ah)
                print("BAD!")
                info = None
            fail = False
        except:
            print("trying again")

    ahmap[ah] = info

pickle.dump(ahmap, open("auction_houses_fin.pkl", "wb"))
