# Assetto Corsa
**Assetto Corsa** is a racing simulation game that allows players to drive a variety of cars on different tracks. 

## Running the game

- We will be using a compatability tool called [Crossover](https://www.codeweavers.com/crossover) by the [CodeWeavers team](https://www.codeweavers.com/) as Assetto Corsa is a Windows only application.
- They offer a 14-day trial. A perpetual license is $74 USD at the time of writing, this licsense can be used for all operating systems according to their FAQ.
- Once the application is installed, go to the "Install" tab and search for "Assetto Corsa", and essentially click yes to everything. It will build a 'container' (this is called a "[bottle](https://news.ycombinator.com/item?id=29613303#:~:text=software%20on%20...-,Bottles%20are%20isolated%20Wine%20environments%2C%20similar%20to%20containers%20or%20VMs,%2C%202021%20%7C%20next%20%5B%E2%80%93%5D)", see [Wine](https://www.winehq.org/) for details) with steam, which then will prompt you to login, then you can launch Assetto Corsa. 
- If you do not have Assetto Corsa, then it is available via [Humble Bundle](https://www.humblebundle.com/store/assetto-corsa) or [Steam](https://store.steampowered.com/app/244210/Assetto_Corsa/).




## Game capture

**FFmpeg** is a free and open-source command-line tool for processing multimedia files. It can be used to capture and stream video from a variety of sources.

To capture the game window, we use the [PyAV library](https://github.com/PyAV-Org/PyAV) which provides a python wrapper for ffmpeg. 

To launch game capture, run the [pyav_capture.py](https://github.com/XDynames/assetto-corsa-interface/blob/main/src/game_capture/pyav_capture.py) file.
```bash
$ python src/game_capture/pyav_capture.py
```


