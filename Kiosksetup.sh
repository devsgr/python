sudo apt-get install unclutter
mkdir ~/.config/autostart
wget https://raw.githubusercontent.com/devsgr/python/main/www.tar.gz 
tar -xzf www.tar.gz
rm www.tar.gz
mv ~/www/run.desktop ~/.config/autostart
