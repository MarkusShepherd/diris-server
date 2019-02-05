# Diris Server #

A mobile adaptation of the popular board game [Dixit](https://recommend.games/#/game/39856). Players submit photos either from their camera, from their gallery, or from a selection of publicly available images.

## Setup ##

```bash
git clone git@gitlab.com:mshepherd/diris-server.git
cd diris-server
./install_deps
./manage.py runserver
```
In the terminal you should see a URL. Use this to make HTTP requests, e.g., [`http://localhost:8000/images/`](http://localhost:8000/images/).

Note: you may need to wrap your directory in a [`virtualenv`](https://virtualenv.pypa.io/en/stable/).

## App ##

The frontend code is hosted in its own [repository](https://gitlab.com/mshepherd/diris-app).