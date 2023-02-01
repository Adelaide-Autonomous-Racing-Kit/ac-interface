# Assetto Corsa
**Assetto Corsa** is a racing simulation game that allows players to drive a variety of cars on different tracks. 

## Creating the bottle
We will be using a compatability tool called [Crossover](https://www.codeweavers.com/crossover) by the [CodeWeavers team](https://www.codeweavers.com/) as Assetto Corsa is a Windows only application. They offer a 14-day trial. A perpetual license is $74 USD at the time of writing, this licsense can be used for all operating systems according to their FAQ.



## Running the game

- Once the application is installed, go to the "Install" tab and search for "Assetto Corsa", and essentially click yes to everything. It will build a 'container' (this is called a "[bottle](https://news.ycombinator.com/item?id=29613303#:~:text=software%20on%20...-,Bottles%20are%20isolated%20Wine%20environments%2C%20similar%20to%20containers%20or%20VMs,%2C%202021%20%7C%20next%20%5B%E2%80%93%5D)", see [Wine](https://www.winehq.org/) for details) with steam, which then will prompt you to login, then you can launch Assetto Corsa. 
- If you do not have Assetto Corsa, then it is available via [Humble Bundle](https://www.humblebundle.com/store/assetto-corsa) or [Steam](https://store.steampowered.com/app/244210/Assetto_Corsa/).


## Game capture

<details>
	<summary>Linux</summary>

### Video
**FFmpeg** is a free and open-source command-line tool for processing multimedia files. It can be used to capture and stream video from a variety of sources.

To capture the game window, we use the [PyAV library](https://github.com/PyAV-Org/PyAV) which provides a python wrapper for ffmpeg. 

To launch game capture, run the [pyav_capture.py](https://github.com/XDynames/assetto-corsa-interface/blob/main/src/game_capture/pyav_capture.py) file.
```bash
$ python src/game_capture/pyav_capture.py
```

### State
AC/C have to run in WINE which means we cannot directly access the game state via shared memory.
To get around this we use a python script running inside the same WINE instance as the game to access the game state which it then makes available to the host OS via a socket.
Crossover doesn't come with python so first we need to install that using the `Install an unlisted application` button in the `Install` tab.
When installing python select to install it for all users.
Once python is installed, go to your bottle with Python and AC in Crossover and click the `Run Command` button.
To use python from the command line we need to add it to the bottle's path.
In the command field type `regedit` and hit `Run`.
Navigate to `HKEY_LOCAL_MACHINE` > `System` > `CurrentControlSet` > `Control` > `Session Manager` > `Environment`.
Then modify the data field of `PATH` by appending 
```
%SystemRoot%\users\crossover\AppData\Local\Programs\Python\Python311
```
*Note: you may need to modify the terminal folder name depending on the version of python you have installed, in this example we used 3.11.*
Now we should be able to call python and its related packages from the bottle's command line.
To access the command line inside the bottle run:
```
/opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app cmd.exe
```
Navigate to the root directory of the package and run 
```
pip install -e .
```
To install it into the bottle.
You can then run
```
python src/gamecapture/state/server.py
```
to start a listener that will send game state to those that connect.
On your host machine you should now be able to run
```
python src/game_capture/state/client.py
```
to receieve game state from AC/C outside the bottle.


</details>


<details>
	<summary>Windows</summary>
