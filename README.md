# AndroidGameBot
Create a bot that can play an Android game through scrcpy

The basic idea is to simulate user actions from outside the Android phone.

Developped & tested on Ubuntu + Samsung Android phone

## Dependencies

scrcpy  https://github.com/Genymobile/scrcpy
v4l2loopback

## Help

If scrcpy was installed from snap, grant camera access using :
    sudo snap connect scrcpy:camera

Start scrcpy with
scrcpy -w --v4l2-sink=/dev/video0
