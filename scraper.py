import logging
import os
import re
import sys
import time

import umsgpack
from playwright.sync_api import Playwright, expect, sync_playwright

base_directory = "/home/netsbit/OneDrive/files"


def remove_windows_prohibited_chars(str):
    return re.sub(r'[\\/*?:"<>|]', "", str)


def log_in(page):
    page.goto("https://www.championshipproductions.com/cgi-bin/champ/login.html")
    email = page.get_by_label("My email is:")
    email.fill("hoangminhlvt@gmail.com")
    password = page.get_by_label("Password:", exact=True)
    password.fill("htyqN5AbW494!*")
    page.get_by_role("button", name="Log In").click()
    # Get to film room
    page.get_by_role("link", name="☁ My Memberships").click()
    page.get_by_text("ChampCoach Basketball", exact=True).click()
    page.wait_for_url("https://videos.championshipproductions.com/members/categories/2100")


def get_video_title(page):
    h1_element = page.locator("xpath=/html/body/main/div[2]/article/div[2]/h1")
    return remove_windows_prohibited_chars(h1_element.inner_text().replace(" FAVORITE\n ADD TO", "").strip("\n"))


def get_mp4_url(page):
    iframe = page.frame_locator("xpath=/html/body/main/div[2]/article/div[1]/iframe")
    # Click button to load the video
    iframe.locator("xpath=/html/body/div[1]/div/button").click()
    # Gets the mp4 url
    return page.evaluate("() => window[1].mp4_url")


def get_video_urls_from_page(page, page_url):
    while True:
        try:
            print(f"Scrapping {page_url}", end="\r")
            logging.log(logging.INFO, f"Scrapping {page_url}")
            page.goto(page_url)
            page.wait_for_load_state("networkidle")
            videos_list = page.locator("xpath=/html/body/div[1]/div/div[2]/section/div/section/div/ul")
            videos = videos_list.get_by_title("Play At Current Position").all()
            # Convert to list of urls and make them absolute
            domain = "https://videos.championshipproductions.com"
            videos = [domain + video.get_attribute("href") for video in videos]
        except Exception as e:
            print(f"Error: {e}")
            print("Retrying...")
            time.sleep(5)
            continue
        break

    return [videos, get_playlist_name(page)]


def get_download_info(page, video_url):
    print(f"Getting info for {video_url}", end="\x1b[1K\r")
    logging.log(logging.INFO, f"Getting info for {video_url}")
    page.goto(video_url)
    title = get_video_title(page)
    mp4_url = get_mp4_url(page)
    # Workaround to get direct download url
    page.goto(mp4_url)
    mp4_url = page.url
    return [title, mp4_url]


def get_name_of_folder(page):
    title = page.locator("h1").inner_text()
    return remove_windows_prohibited_chars(title)


def get_all_download_info(page, urls):
    info = []
    for i, url in enumerate(urls):
        _ = get_download_info(page, url)
        _[0] = f"{i + 1}. {_[0]}"
        info.append(_)
    return info


def list_remove_duplicates(l):
    return list(dict.fromkeys(l))


def get_playlist_urls_from_page(page, page_url):
    while True:
        try:
            print(f"Scrapping {page_url}")
            logging.log(logging.INFO, f"Scrapping {page_url}")
            page.goto(page_url)
            page.wait_for_load_state("networkidle")
            a_elements = page.locator("xpath=/html/body/div[1]/div/section/div/section/div[2]/section[2]/div/ul")
            a_elements = a_elements.locator("a")
            domain = "https://videos.championshipproductions.com"
            playlists = [domain + a.get_attribute("href") for a in a_elements.all()]
            playlists = list_remove_duplicates(playlists)
        except Exception as e:
            print(f"Error: {e}")
            print("Retrying...")
            time.sleep(5)
            continue
        break

    return playlists


def get_playlist_name(page):
    return remove_windows_prohibited_chars(page.locator("h1").inner_text())


def run(playwright: Playwright, url):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    # browser = playwright.chromium.connect_over_cdp("http://localhost:1559")
    # default_context = browser.contexts[0]
    # page = default_context.pages[0]
    log_in(page)
    playlist_info = get_playlist_urls_from_page(page, url)
    download_info = []

    for playlist in playlist_info:
        videos = get_video_urls_from_page(page, playlist)
        _ = get_name_of_folder(page)
        folder = f"{base_directory}/{_}"
        if not os.path.exists(folder):
            os.makedirs(folder)
        download_info.append([get_all_download_info(page, videos[0]), folder])
    with open("download_info.msgpack", "wb") as f:
        f.write(umsgpack.packb(download_info))


def main(url):
    with sync_playwright() as playwright:
        run(playwright, url)


if __name__ == "__main__":
    logging.basicConfig(filename="scraper.log", level=logging.INFO, filemode="w")
    main(sys.argv[1])
