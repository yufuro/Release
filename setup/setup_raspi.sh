#Enable Japanease Localization
sudo raspi-config nonint do_change_locale ja_JP.UTF-8
sudo raspi-config nonint do_change_timezone Asia/Tokyo
#Enable i2c
sudo raspi-config nonint do_i2c 0
sudo reboot