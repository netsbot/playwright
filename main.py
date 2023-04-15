import subprocess

from downloader import main

with open("downloads.txt", "r") as f:
    urls = [url.strip() for url in f.readlines()]

for url in urls:
    subprocess.call(["netns-exec", "python3", "scraper.py", url])
    main()
