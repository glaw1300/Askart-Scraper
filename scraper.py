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

def login(driver, u, p):
    driver.get('https://www.artprice.com/identity')
    driver.find_element_by_id('login').send_keys(u)
    driver.find_element_by_id('pass').send_keys(p)
    driver.find_element_by_class_name('sln-submit-login').click()

def search(name, driver):
    # fill search bar and search
    search = driver.find_element_by_tag_name("form")
    search.find_element_by_id(searchid).send_keys(artist)
        # click twice for some reason :/
    search.find_element_by_id("sln_searchbar_commit").click()
    search.find_element_by_id("sln_searchbar_commit").click()

def parse_lots(soup, artist, d):
    # iterate over each lot
    lots = soup.find_all("div", {"class":"lot"})
    for lot in lots:
        try:
            # piece title
            title = lot.find_all("div", {"class":"lot-datas-title"})[0].text.strip().lstrip()
        except:
            title = None
        # each line of block
        lines = lot.find_all("div", {"class": "lot-datas-block"})
        # description
        try:
            desc = lines[0].text.lstrip().strip()
        except:
            desc = None
            print(f"Missing description for {title} - {artist}")
        # dimensions
        try:
            dim = lines[1].find("span").text.replace(u'\xa0', u' ')
        except:
            dim = None
            print(f"Missing dimensions for {title} - {artist}")
        # esitmated price
        try:
            est = lines[2].find_all("span")[1].text.replace(u'\xa0', u' ').lstrip().strip()
        except:
            est = None
            print(f"Missing estimate for {title} - {artist}")
        # hammer
        try:
            hammer = lines[3].find_all("span")[1].text.replace(u'\xa0', u' ').lstrip().strip()
        except:
            hammer = None
            print(f"Missing hammer for {title} - {artist}")
        # sell date
        try:
            date = lines[4].text.lstrip().strip()
        except:
            date = None
            print(f"Missing sell date for {title} - {artist}")
        # auciton house
        try:
            auctioneer = lines[5].text.lstrip().strip()
        except:
            auctioneer = None
            print(f"Missing auctioneer for {title} - {artist}")

        # get listing url
        try:
            link = json.loads(lot.find_all("div")[-1]["data-react-props"])['lotUrl']
        except:
            link = None
            print(f"Missing link for {title} - {artist}")

        # store in dict
        d[artist].append((title, desc, dim, est, hammer, date, auctioneer, link))

driver = webdriver.Firefox()
driver.implicitly_wait(5)
BASE_URL = "https://www.artprice.com/"
nextcls = "sln-next-page"
searchid = "sln_searchbar"
artists_path = "artists.txt"
prev_url = BASE_URL

# load in credentials
load_dotenv()
login(driver, os.environ.get("UNAME"), os.environ.get("PW"))

# establish requests
gateway = ApiGateway(BASE_URL)
gateway.start()
session = requests.Session()
#passing the cookies generated from the browser to the session
c = [session.cookies.set(c['name'], c['value']) for c in driver.get_cookies()]

session.mount(BASE_URL, gateway)

# load in artists into list, set, and dictionary
artists = [a.strip() for a in open(artists_path, "r")]
a_set = set(artists)
a_info = {a:[] for a in artists}

ix = 0
na = len(artists)
for line in artists:
    artist = line.strip()
    print(f"Starting {artist} – {ix}/{na}")
    ix += 1

    # go to artprice.com
    driver.get(BASE_URL)
    time.sleep(random.random()) # sleep short time (0-1)

    # search
    search(artist, driver)

    # select top option (maybe not most reliable, but should be good)
    artist_row = driver.find_elements_by_class_name("artist")[0]
    driver.get(artist_row.find_element_by_tag_name("a").get_attribute("href"))

    # go to auction results
    time.sleep(random.random()) # sleep at auction page for a short time
    try:
        driver.find_element_by_id("sln_ps").click()
    except:
        print(f"No auction results for {artist}")
        continue

    # while there is still a next button, loop and scrape (don't need selenium for this)
    url = driver.current_url
    pnum = 1
    while True:
        # get current page
        page = session.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        parse_lots(soup, artist, a_info)

        # if next exists, go to it
        nextbtn = soup.find_all("a", {"class": nextcls})

        if nextbtn:
            url = urljoin(BASE_URL, nextbtn[0]['href'])
            pnum += 1
        else:
            break
        time.sleep(random.random() + 1) # sleep ~ 1 second btw each page
        if pnum % 20 == 0: # sleep 5 seconds every 20 pages
            time.sleep(5)
    # temporarily save results
    pickle.dump(a_info, open("tmp2.pkl", "wb"))
    print("Waiting 10 before proceeding...")
    time.sleep(7)

print(a_info)
