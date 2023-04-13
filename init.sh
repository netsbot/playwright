wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
python -m pip install -r requirements.txt
playwright install
playwright install-deps
sudo apt install build-essential
sudo apt install libcurl4-openssl-dev libsqlite3-dev pkg-config git curl
curl -fsS https://dlang.org/install.sh | bash -s dmd
git clone https://github.com/abraunegg/onedrive.git
cd onedrive
bash -c "source ~/dlang/dmd-2.103.0/activate;./configure;make clean;make;sudo make install"
