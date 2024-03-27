# Assetto Corsa, a new racing benchmark
![](https://imgs.xkcd.com/comics/standards_2x.png)

**Assetto Corsa** is a racing simulation game that allows players to drive a variety of cars on different tracks. 



## Creating the bottle
We will be using a compatability tool called [Crossover](https://www.codeweavers.com/crossover) by the [CodeWeavers team](https://www.codeweavers.com/) as Assetto Corsa is a Windows only application. They offer a 14-day trial. A perpetual license is $74 USD at the time of writing, this licsense can be used for all operating systems according to their FAQ.




## Running the game

- Do not install Steam if you see it, installing Assetto Corsa will install steam in it's own bottle.
- Once the application is installed, go to the "Install" tab and search for "Assetto Corsa". You should see the image below.
	- Click yes to everything. .NET 2.0 does not install correctly so just skip this step when prompted. 
	- It will build a 'container' (this is called a "[bottle](https://news.ycombinator.com/item?id=29613303#:~:text=software%20on%20...-,Bottles%20are%20isolated%20Wine%20environments%2C%20similar%20to%20containers%20or%20VMs,%2C%202021%20%7C%20next%20%5B%E2%80%93%5D)", see [Wine](https://www.winehq.org/) for details).
	- **IMPORTANT** when prompted to start steam during the install, click yes and sign in. Not doing this step will result in installation being broken. Once you have signed in it will prompt you to install AC.
- If you do not have Assetto Corsa, then it is available via [Humble Bundle](https://www.humblebundle.com/store/assetto-corsa) or [Steam](https://store.steampowered.com/app/244210/Assetto_Corsa/).

![Install Assetto Cora](imgs/crossover_assetto-corsa.png)

Open AC and drive with a car checking that everything is working as expected.

## Additional Setup

<details>
	<summary>Linux</summary>


### Game State
AC has to run in WINE which means we cannot directly access the game state via shared memory.
To get around this we use a python script running inside the same WINE instance as the game to access the game state which it then makes available to the host OS via a socket.
Crossover doesn't come with python so first we need to install that using the `Install an unlisted application` button in the `Install` tab.
When installing python select to install it for all users in the Advanced Menu.

![image](https://user-images.githubusercontent.com/26395770/223075507-2eed5cd2-5ce6-4bcd-a991-a8301265386a.png)


Now we should be able to call python and its related packages from the bottle's command line.
To verify this, in crossover click `Run Commnad` and in the `Command` field type `python`, this should launch your Python (version 3.11 in our example) interactive terminal. 


Navigate to the root directory of the package and run:
```
/opt/cxoffice/bin/wine --bottle Assetto_Corsa --cx-app cmd.exe
```
To access the command line inside the bottle.
Then install ac interface it into the bottle by running:
```
pip install loguru numpy
pip install -e .
```
	
In linux, do this to make sure the python uinput module has access to the kernel uinput module. 
```bash
sudo modprobe uinput
sudo chmod a+r+w /dev/uinput
```

Additionally, if the game resolution is set to be the same as your windowed resolution, i.e. you have a 1920x1080 screen, and in AC you disable fullscreen mode (enabling windowed mode) and set the resolution to be 1920x1080, AC will ignore your windowed mode request and thus our scripts won't be able to do game capture. So you will need to set the game resolution to something smaller than your display, i.e. 1920x1080 screen, so 1600x900 game resolution. 
You will need to go into `src/aci/config/capture/game_capture.yaml` and change the resolution to the one chosen in game.

### Recording
To write out image files faster we need to make sure an additional package is installed by running `sudo apt-get install libturbojpeg` prior to running `make build`.


</details>

<details>
	<summary>Content Manager and Mods</summary>
[Content Manager](https://acstuff.ru/app/) (CM) replaces the original game launching menu with a much better one with many additional features. CM gives the ability to easily install mods such as new cars, tracks, visual improvements, and python apps to the game. Although it is possible to do this without CM there is a free version with many features. CM also makes it easy to install two important visual improvement mods [Custom Shaders Patch](https://acstuff.ru/patch/) and [Sol](https://www.racedepartment.com/downloads/sol.24914/). These two mods update the games graphics, textures, and functionality to include more weather and times of day. You can find more information on [Custom Shaders Patch (CSP) discord](https://discord.gg/QwXVEFM) and [Sol-Pure discord](https://discord.gg/m2Vbsgz). There are two versions of CM and CSP, free and paid. Both are relatively cheap for the amount of work that has gone into them only being a few dollars each. You can get away with free CSP but RainFX will not be available.


### Installing Content Manager
I have tested the install in the Assetto Corsa bottle with Windows 10 64-bit. First you will need to install all the dependencies of CM in the crossover bottle. This includes [Visual C++ Redistributable x86](https://www.microsoft.com/en-us/download/details.aspx?id=48145), [DirectX Runtime June 2010](https://www.microsoft.com/en-us/download/confirmation.aspx?id=8109), and [DirectX 10/11 for 3D-related functions](https://www.microsoft.com/en-us/download/details.aspx?id=35). I didn't have any success getting DirectX 10/11 installed but this didn't seem to effect the rest of the installation.

Next we want to download CM from [here](https://acstuff.ru/app/). Extract the .exe file and rename it `Content Manager Safe.exe`. This stops CM from using hardware acceleration for the GUI. In Crossover select the bottle and then `Install Application into Bottle` then `Install unlisted application`. Select `Content Manager Safe.exe` as the installed file and click install. A menu should pop-up, I didn't need to select anything on this menu at all, just click 'OK' down the bottom. Don't click on `Make desktop icon` as this closes the menu without finishing the install. CM should then open up. In CM go to the Settings tab and navigate to `Settings->Content Manager->Appearance->System` and tick 'Disable windows transparency' and 'Disable hardware acceleration for UI'. Once this is done we no longer need to have 'Safe' in the `.exe` file to run. You can now close CM, beware that the install doesn't finish. This is fine you can cancel the install.

Next we want to navigate to the Assetto Corsa root folder which should be something like this: `~/.cxoffice/Assetto_Corsa/drive_c/Program Files (x86)/Steam/steamapps/common/assettocorsa`. Rename the original launcher `AssettoCorsa.exe` to `AssettoCorsa_original.exe`. Then copy in the `Content Manager Safe.exe` and rename it `AssettoCorsa.exe`. Now when launching Assetto Corsa it will launch CM as the default launcher.

We are now ready to install CSP and Sol. Open Crossover and go to the Assetto Corsa bottle. Go to `Control Panels->Wine Configuration->Libraries` and add in `dwrite.dll` (it should be in the drop down menu). This is needed for CSP to work. Open Assetto Corsa (which should open with CM as the launcher now) and go to `Settings->Custom Shaders Patch` and install it. I have tested with both 0.1.79 and [0.1.80-preview115](https://www.patreon.com/x4fab/posts) (paid version). With this installed we can also install [Sol](https://www.racedepartment.com/downloads/sol.24914/), you will need to signup to Racedepartment and download the instructions. Make sure to follow the instructions in the pdf.

To check if this is working go into a practice race and set the time to 22:00. If the track is dark and the time doesn't default to 18:00 all should be good to go.

</details>

# AC Interface
## Defining an Agent
To define your own and allow it to control a car in the game create a class that inherits from `aci.interface.AssettoCorsaInterface` and define a function named `behaviour(self, observation: Dict) -> np.array`.
To test your agent create a main method that instances your new Agent class and calls `agent.run()`.
As an example here is an agent that does nothing:
```
from aci.interface import AssettoCorsaInterface

class MyCoolAgent(AssettoCorsaInterface):
	def behaviour(self, observation: Dict) -> np.array:
		return np.array([0.0, 0.0, 0.0])

if __name__=="__main__":
	agent = MyCoolAgent()
	agent.run()
```
More examples of how to do this can be found in the /examples folder.

## Record A Game Session
An example of using our interface to record a game session is:
```
from aci.recorder import AssettoCorsaRecorder


if __name__ == "__main__":
    save_path = "./test/monza_audi_r8_lms_1"
	recorder = AssettoCorsaRecorder()
    recorder.run(save_path)
```
To finish recording use a keyboard interrupt (crt+c) on the terminal running the script.