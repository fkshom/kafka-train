#!/usr/bin/env bash

cd volumes

sudo rm -rf kafka{1,2,3}
sudo rm -rf zookeeper{1,2,3}_{data,log}
sudo mkdir kafka{1,2,3}
sudo chmod 777 kafka{1,2,3}
sudo mkdir zookeeper{1,2,3}_{data,log}
sudo chmod 777 zookeeper{1,2,3}_{data,log}
