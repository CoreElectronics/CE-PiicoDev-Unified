#!/bin/bash

echo ""
echo "The script will run after 20 seconds. Press any key to continue immediately or CTRL+C to abort"
echo "This script will modify the .../config.txt file to enable I2C and set the correct baudrate (400kbps) for PiicoDev modules"
echo "If you want to view the contents of this script, save it to a file. Run: curl -L https://piico.dev/i2csetup > i2c-setup.sh"

# Hold for at most 20 seconds. Any key to continue
read -t 20 -n 1 -s

# Get RPi OS major version number
# Find the line starting with 'VERSION_ID', break line into two values, grab the second value and format for storage as an int
version_id=$(awk -F'=' '/^VERSION_ID/{gsub(/"/,"",$2);print $2}' /etc/os-release)

# Checking if the version_id call was successful
if [ $? -eq 0 ] && [ -z "$version_id" ]; then
    echo "Failed to identify the major software version"
    exit 10
else
    echo "Version_Id: $version_id"
fi

if [ "$version_id" -lt 12 ]; then
    echo "Legacy version detected (pre version 12)"
    config_file="/boot/config.txt"
else
    echo "Version 12 or higher detected"
    config_file="/boot/firmware/config.txt"
fi

echo "The script will now update I2C parameters in $config_file"

if [ ! -e "$config_file" ]; then
    echo "$config_file does not exist"
    exit 10
else
    # This will remove dtparam=i2c_arm=
    sudo sed -i.bak '/^dtparam=i2c_arm=/d' "$config_file"

    # This will remove dtparam=i2c_arm_baudrate=
    sudo sed -i '/^dtparam=i2c_arm_baudrate=/d' "$config_file"

    # This will remove comment
    sudo sed -i '/^# Added by PiicoDev:/d' "$config_file"

    # This will add dtparam=i2c_arm=on and dtparam=i2c_arm_baudrate=400000
    sudo sed -i '$a# Added by PiicoDev: require I2C and 400k baudrate\ndtparam=i2c_arm=on\ndtparam=i2c_arm_baudrate=400000' "$config_file"

    echo "Setup complete. The file $config_file has been updated. Please reboot."
fi
