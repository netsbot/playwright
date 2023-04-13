import os
import re
import subprocess
import sys
import time
import requests
import threading
from playwright.sync_api import Playwright, expect, sync_playwright
from tqdm import tqdm

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
            print(f"Scrapping {page_url}")
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


def request_download_file(mp4_url, name, folder):
    response = requests.get(mp4_url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024
    progress_bar = tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, leave=False)
    with open(f'{folder}/{name}.mp4', 'wb') as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()
    print(f"Downloaded {name}.mp4")
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")


def request_download_file_no_tqdm(mp4_url, name, folder):
    response = requests.get(mp4_url, stream=True)
    block_size = 1024
    with open(f'{folder}/{name}.mp4', 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)
    print(f"Downloaded {name}.mp4")


def get_download_info(page, video_url):
    print(f"Getting info for {video_url}")
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


def upload_to_onedrive():
    subprocess.call(["onedrive", "--synchronize", "--upload-only", "--no-remote-delete"])


def delete_from_local(folder):
    subprocess.call(["rm", "-rf", f"{folder}"])


def list_remove_duplicates(l):
    return list(dict.fromkeys(l))


def get_playlist_urls_from_page(page, page_url):
    while True:
        try:
            print(f"Scrapping {page_url}")
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


def category_handler(page, category_url):
    playlists = get_playlist_urls_from_page(page, category_url)

    return playlists


def download_all_no_threads(download_info):
    for playlist_info in download_info:
        for info in playlist_info[0]:
            request_download_file_no_tqdm(info[1], info[0], playlist_info[1])


def run(playwright: Playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    # browser = playwright.chromium.connect_over_cdp("http://localhost:1559")
    # default_context = browser.contexts[0]
    # page = default_context.pages[0]
    option = sys.argv[1]
    if option == "u":
        url = sys.argv[2]
        log_in(page)
        urls = get_video_urls_from_page(page, url)
        folder = f"{base_directory}/{get_name_of_folder(page)}"
        if not os.path.exists(folder):
            os.makedirs(folder)
        download_info = get_all_download_info(page, urls)
        download_all_no_threads(download_info)
        upload_to_onedrive()
        delete_from_local()
    elif option == "p":
        with open("downloads.txt", "r") as f:
            category_urls = [line.strip() for line in f]
        log_in(page)
        playlist_info = [category_handler(page, url) for url in category_urls]
        download_info = []

        for info in playlist_info:
            for playlist in info:
                videos = get_video_urls_from_page(page, playlist)
                _ = get_name_of_folder(page)
                folder = f"{base_directory}/{_}"
                if not os.path.exists(folder):
                    os.makedirs(folder)
                download_info.append([get_all_download_info(page, videos[0]), folder])
                download_all_no_threads(download_info)
                download_info.remove(download_info[0])
                upload_to_onedrive()
                delete_from_local(base_directory)
    elif option == "a":
        # Reduces overhead by logging in once and get all video info
        urls = []
        all_videos_info = []
        with open("downloads.txt", "r") as f:
            for line in f:
                urls.append(line.strip())
        log_in(page)
        for url in urls:
            page.goto(url)
            folder = f"{base_directory}/{get_name_of_folder(page)}"
            if not os.path.exists(folder):
                os.makedirs(folder)
            all_videos_info.append([get_all_download_info(page, get_video_urls_from_page(page, url)), folder])
        page.close()
        context.close()
        browser.close()
        for info in all_videos_info:
            download_all_videos(info[0], info[1])
        upload_to_onedrive()
        delete_from_local(base_directory)


with sync_playwright() as p:
    run(p)
