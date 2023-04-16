import logging
import os.path
import subprocess
import umsgpack
import requests
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from tqdm import tqdm


def request_download_file(mp4_url, name, folder):
    response = requests.get(mp4_url, stream=True)
    total_size_in_bytes = int(response.headers.get('content-length', 0))
    block_size = 1024
    with tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True, leave=False) as pbar:
        with open(f'{folder}/{name}.mp4', 'wb') as file:
            for data in response.iter_content(block_size):
                pbar.update(len(data))
                file.write(data)
    tqdm.write(f"Downloaded {name}.mp4")
    logging.log(logging.INFO, f"Downloaded {name}.mp4")


def request_download_file_no_tqdm(mp4_url, name, folder):
    response = requests.get(mp4_url, stream=True)
    block_size = 1024
    with open(f'{folder}/{name}.mp4', 'wb') as file:
        for data in response.iter_content(block_size):
            file.write(data)
    tqdm.write(f"Downloaded {name}.mp4")


def upload_to_onedrive():
    subprocess.call(["onedrive", "--synchronize", "--upload-only", "--no-remote-delete"])
    logging.log(logging.INFO, "Uploaded to OneDrive")


def delete_from_local(folder):
    subprocess.call(["rm", "-rf", f"{folder}"])
    logging.log(logging.INFO, f"Deleted {folder}")


def download_playlist(playlist_info):
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = []
        for info in playlist_info[0]:
            future = pool.submit(request_download_file, info[1], info[0], playlist_info[1])
            futures.append(future)
        wait(futures, return_when=ALL_COMPLETED)


def download_all_threaded(download_info):
    for playlist_info in download_info:
        download_playlist(playlist_info)
        upload_to_onedrive()
        delete_from_local(playlist_info[1])


def main():
    logging.basicConfig(filename="downloader.log", level=logging.INFO)
    with open("download_info.msgpack", "rb") as f:
        download_info = umsgpack.unpackb(f.read())
        download_all_threaded(download_info)
