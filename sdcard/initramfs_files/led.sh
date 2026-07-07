#!/bin/sh

echo 51 > /sys/class/gpio/export
echo 54 > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio51/direction
echo "out" > /sys/class/gpio/gpio54/direction



while true; do

	#BLUE ON
	echo 0 > /sys/class/gpio/gpio51/value
	sleep 0.2
	echo 1 > /sys/class/gpio/gpio51/value

	#GREEN ON
	echo 0 > /sys/class/gpio/gpio54/value
	sleep 0.2
	echo 1 > /sys/class/gpio/gpio54/value

	#CYAN
	echo 0 > /sys/class/gpio/gpio54/value
	echo 0 > /sys/class/gpio/gpio51/value
	sleep 0.2
	echo 1 > /sys/class/gpio/gpio51/value
	echo 1 > /sys/class/gpio/gpio54/value
	sleep 0.2

done

