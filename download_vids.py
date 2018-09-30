from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import requests
import sys
from threading import Thread
import time, random
from bs4 import BeautifulSoup
from urllib.parse import urljoin

maxthreads = 2  # maximum number of concurrent threads
total_episodes = 2  # hold total number of operations
total_seasons = 2
all = {}  # global holding the current running threads


def main(season, episode):
    setup(season, episode)


def setup(season, episode):
    path = 'C:/Games/chromedriver.exe'
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(executable_path=path, chrome_options=chrome_options)
    url = 'https://sdarot.world/watch/204-%D7%96%D7%94%D7%95%D7%AA-%D7%91%D7%93%D7%95%D7%99%D7%94-alias/season/{}/episode/{}'.format(
        season, episode)
    driver.get(url)
    timeout = 33
    element_present = EC.presence_of_element_located((By.CLASS_NAME, 'vjs-tech'))
    found = WebDriverWait(driver, timeout).until(element_present)
    val = found.get_attribute('src')
    print(val)
    download_url(val, season, episode)


def seasons_discovery(url):
    response = requests.get(url)
    html_content = response.text
    soup = BeautifulSoup(html_content, 'lxml')
    links = soup.find_all('a')
    seasons = []
    episodes = []
    for link in links:
        if link['href'].find("watch/") is not -1:
            if link['href'].find("/season") is not -1:
                if link['href'].find("/episode") is -1:
                    seasons.append(link)
                else:
                    episodes.append(link)
    print("Seasons found: %s" % len(seasons))
    return seasons


def episodes_discovery(url, seasons):
    # response = requests.get(url)
    # html_content = response.text
    # soup = BeautifulSoup(html_content, 'lxml')
    # links = soup.find_all('a')
    seasons_dict = dict()
    for season in seasons:
        episodes = []
        new_url = urljoin(url, season['href'])
        response = requests.get(new_url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        links = soup.find_all('a')
        for link in links:
            if link['href'].find("watch/") is not -1:
                if link['href'].find("/episode") is not -1:
                    episodes.append(link)
        seasons_dict[season] = episodes
    for k, v in seasons_dict.items():
        print("In season %s, found %d episodes" % (k.text, len(v)))



def download_url(url, season, episode):
    file_name = "alias_season%d_episode_%d.mp4" % (season, episode)
    download_path = r'F:\TV Shows\alias\season 1\\'
    with open(download_path + file_name, "wb") as f:
        print("Downloading %s" % file_name)
        response = requests.get(url, stream=True)
        total_length = response.headers.get('content-length')

        if total_length is None:  # no content length header
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content(chunk_size=4096):
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50 - done)))
                sys.stdout.flush()


class Worker(Thread):
    global all

    def __init__(self, season, episode):
        Thread.__init__(self)
        self.all = all
        self.episode = episode
        self.season = season

    def run(self):
        time.sleep(random.randint(10, 100) / 1000.0)
        main(self.season, self.episode)
        print("id %d: " % self.episode, all.keys())
        del all[self.episode]




# ToDo: First version, next version to get input from user
# for s in range(1, total_seasons):
#     for e in range(19, 20):
#         while (len(all) > maxthreads):
#             time.sleep(.1)
#
#         all[e] = 1
#         w = Worker(s, e)
#         w.start()
url = 'https://sdarot.world/watch/43-prison-break-%D7%A0%D7%9E%D7%9C%D7%98%D7%99%D7%9D'
seasons = seasons_discovery(url)
episodes_discovery(url, seasons)
