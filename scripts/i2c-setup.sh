echo This script will modify the /boot/config.txt file to enable I2C and set the correct baudrate of 400kbps. 
echo if you want to view the contents of this script, save it to a file. Run: curl -L https://piico.dev/i2csetup >> i2c-setup.sh
while true
do
      read -r -p "Do you want to procees? [y/n]" input
 
      case $input in
            [yY][eE][sS]|[yY])
                  sed -i.bak '/^dtparam=i2c_arm=' /boot/config.txt                                                                                # remove dtparam=i2c_arm=
                  sed -i '/^dtparam=i2c_arm_baudrate=/d' /boot/config.txt                                                                         # remove dtparam=i2c_arm_baudrate=
                  sed -i '$a# Added by PiicoDev: require I2C 400k baudrate\ndtparam=i2c_arm=on\ndtparam=i2c_arm_baudrate=400000' /boot/config.txt # add dtparam=i2c_arm=on and dtparam=i2c_arm_baudrate=400000
                  echo Setup complete. Please reboot.
                  break
                  ;;
            [nN][oO]|[nN])
                  echo "Bye"
                  break
                  ;;
            *)
                  ;;
      esac      
done
