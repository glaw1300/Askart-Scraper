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

def login(driver, u, p):
    driver.get('https://www.askart.com/')
    print("Log in on the browser. Return and enter any key to continue.")
    wait = input("Enter input to continue: ")
    driver.get("https://askart.com/")

def search(name, driver, searchid="txtSearchHomepage"):
    # fill search bar and search
    search = driver.find_element_by_id(searchid)
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
BASE_URL = "https://www.askart.com/"
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
artists = ["Pablo Picasso", "Salvador Dalí"]
a_set = set(artists)
a_info = {a:[] for a in artists}

ix = 0
na = len(artists)
for line in artists:
    artist = line.strip()
    #if artist == "Pablo Picasso" or artist == "Salvador Dalí":
    #    print(f"Skipping {artist}")
    #    continue
    print(f"-----\nStarting {artist} – {ix}/{na}")
    ix += 1

    # go to artprice.com
    driver.get(BASE_URL)

    # search
    search(artist, driver)

    # either takes you to search results or directly to artist
    # this is a hack and should be done better, but wait for page to load before getting url
    time.sleep(1)
    if "Search.aspx" in driver.current_url:
        # if in search results, navigate to artist (for popular artists like picasso)
        # select top option (maybe not most reliable, but should be good)
        artist_table = driver.find_elements_by_tag_name("table")[1]

        # if can get link, click it
        try:
            artist_table.find_element_by_tag_name("a").click()
        except:
            print(f"No artists found for {artist} - continuing")
            continue

    # if doing picasso and dali, wait to filter by only paintings
    if input("Enter here when filtered by paintings: "):
        pass

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

    parse_lots(soup, artist, a_info)

    # temporarily save results
    pickle.dump(a_info, open("picasso_dali.pkl", "wb"))

print(a_info)
