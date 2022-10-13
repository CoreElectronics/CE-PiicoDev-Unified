echo ""
echo "This script will modify the /boot/config.txt file to enable I2C and set the correct baudrate (400kbps). "
echo "if you want to view the contents of this script, save it to a file. Run: curl -L https://piico.dev/i2csetup > i2c-setup.sh"
echo "The script will run in 10 seconds.  Hit CTRL+C to abort"

sleep 10

# remove dtparam=i2c_arm=
sudo sed -i.bak '/^dtparam=i2c_arm=/d' /boot/config.txt
# remove dtparam=i2c_arm_baudrate=
sudo sed -i '/^dtparam=i2c_arm_baudrate=/d' /boot/config.txt
# remove comment
sudo sed -i '/^# Added by PiicoDev:/d' /boot/config.txt
# add dtparam=i2c_arm=on and dtparam=i2c_arm_baudrate=400000
sudo sed -i '$a# Added by PiicoDev: require I2C and 400k baudrate\ndtparam=i2c_arm=on\ndtparam=i2c_arm_baudrate=400000' /boot/config.txt
echo Setup complete. Please reboot.
