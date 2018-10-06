import argparse
import requests
import sys
import os
import queue
import time
import threading
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


class SdarotDownloader():
    def __init__(self, **kwargs):
        self._TIMEOUT = 35
        self.episode = 0
        self.url = kwargs.get('url')
        self._chrome_driver_path = kwargs.get('chrome_driver_path')
        if self._chrome_driver_path is None:
            self._chrome_driver_path = 'chromedriver'
        self.season_to_download = kwargs.get('season_to_download')
        self.download_path = kwargs.get("download_path")
        self.seasons_count = 0
        self.episodes_for_season = 0

    def runner(self):
        episodes = self.get_episodes_for_season()
        print('Downloading TV show %s season %s total episodes %d' % (self.get_tv_show_name(), self.season_to_download, len(episodes)))
        work = queue.Queue()
        for k, v in episodes.items():
            work.put(k)

        threads = []
        for i in range(5):
            t = threading.Thread(target=self.worker, args=(i, work))
            t.start()
            threads.append(t)

        for thread in threads:
            thread.join()

    def worker(self, id, work):
        print(f"worker {id} started!")
        while work:
            self.downloader(work.get())
        return

    def get_download_link(self, episode):
        link = urljoin(self.url, episode['href'])
        chrome_driver_options = Options()
        chrome_driver_options.add_argument("--headless")
        print(link)
        driver = webdriver.Chrome(executable_path=self._chrome_driver_path, chrome_options=chrome_driver_options)
        driver.get(link)
        element_present = EC.presence_of_element_located((By.CLASS_NAME, 'vjs-tech'))
        element = WebDriverWait(driver, self._TIMEOUT).until(element_present)
        download_link_url = element.get_attribute('src')
        return download_link_url

    def get_seasons(self):
        response = requests.get(self.url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        links = soup.find_all('a')
        seasons = []
        for link in links:
            if link['href'].find("watch/") is not -1:
                if link['href'].find("/season") is not -1:
                    if link['href'].find("/episode") is -1:
                        seasons.append(link)
        print("Seasons found: %s" % len(seasons))
        for season in seasons:
            if season.text == self.season_to_download:
                return season

    def get_episodes_for_season(self):
        sleep_before_download = 30
        seasons_dict = dict()
        episodes = dict()
        season_to_download = self.get_seasons()
        new_url = urljoin(self.url, season_to_download['href'])
        response = requests.get(new_url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        links = soup.find_all('a')
        for link in links:
            if link['href'].find("watch/") is not -1:
                if link['href'].find("/episode") is not -1:
                    episodes[link] = link['href']
            seasons_dict[season_to_download] = episodes

        for k, v in seasons_dict.items():
            print("In season %s, found %d episodes" % (k.text, len(v)))

        print('Sleeping for %d due to server limitations' % sleep_before_download)
        time.sleep(sleep_before_download)
        return episodes

    def get_episodes_for_seasons(self, seasons):
        seasons_dict = dict()
        for season in seasons:
            episodes = []
            new_url = urljoin(self.url, season['href'])
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

    def get_tv_show_name(self):
        response = requests.get(self.url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')
        links = soup.find_all('section', {'class': "background rounded"})
        for link in links:
            names = link.find_all('h1')
            for name in names:
                return name.text.split(" / ")[1]

    def downloader(self, episode):
        download_path = os.path.join(self.download_path, "%s_season_%s" % (self.get_tv_show_name(), self.season_to_download))
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        file_name = os.path.join(download_path, r"%s_s%se%s.mp4" % (self.get_tv_show_name(), self.season_to_download, episode.text))
        with open(file_name, "wb") as f:
            print("Downloading %s" % file_name)
            response = requests.get(self.get_download_link(episode), stream=True)
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


def parse_args():
    args_parser = argparse.ArgumentParser(description="Sdarot TV auto Downloader")
    args_parser.add_argument("-u", "--url", help="TV show to download URL", type=str, required=True)
    args_parser.add_argument("-c", "--chrome-driver-path", help="Executable Chrome driver path (only if it's not in PATH)", type=str)
    args_parser.add_argument("-s", "--season-to-download", help="Season number to download", type=str, required=True)
    args_parser.add_argument("-d", "--download-path", help="Season download path", type=str, required=True)
    return args_parser.parse_args()

parsed_args = parse_args()
sd = SdarotDownloader(**parsed_args.__dict__)
sd.runner()
