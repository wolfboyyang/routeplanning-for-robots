# How to run
1. `pip install flet paho-mqtt`
1. `python d_star_lite_main.py`

### Hot Reload

1. `flet -d d_star_lite_main.py`
1. modify code and check


### Build & run in Docker
1. `docker build -t dstarlite .`
1. `docker run -d -p 8550:8550 dstarlite`
1. open `http://127.0.0.1:8550`

### Launch Fly.io app
1. `flyctl auth login`
1. `flyctl apps create --name dstarlite`
1. `flyctl deploy`
1. open `https://dstarlite.fly.dev/`

## Referrences
1. [flet.dev](https://flet.dev/docs/)
1. [Interactive D Start Lite (Tkinter)](https://github.com/robodhhb/Interactive-D-Star-Lite.git)