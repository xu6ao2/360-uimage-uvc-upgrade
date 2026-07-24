#!/bin/sh

echo 81 > /sys/class/gpio/export
echo "out" > /sys/class/gpio/gpio81/direction



while true; do
        #GREEN ON
        echo 0 > /sys/class/gpio/gpio81/value
        sleep 0.2
        echo 1 > /sys/class/gpio/gpio81/value
	sleep 0.2

done

