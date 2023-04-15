sudo apt install -y python3 python-is-python3
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py
python -m pip install -r requirements.txt
~/.local/bin/playwright install
~/.local/bin/playwright install-deps
curl -o ~/.local/bin/wg-netns https://raw.githubusercontent.com/dadevel/wg-netns/main/wgnetns/main.py
chmod +x ~/.local/bin/wg-netns
sudo apt install -y build-essential expect tmux wireguard
sudo apt install -y libcurl4-openssl-dev libsqlite3-dev pkg-config git curl
curl -fsS https://dlang.org/install.sh | bash -s dmd
git clone https://github.com/abraunegg/onedrive.git
cd onedrive
bash -c "source ~/dlang/dmd-2.103.0/activate;./configure;make clean;make;sudo make install"
git clone https://github.com/Intika-Linux-Namespace/Netns-Exec.git
cd Netns-Exec
git submodule update --init
make
sudo make install