In order to create a gym compliant environment out of Assetto Corsa there are three main hurdles: collecting game state, sending actions and compatibility.
These three issues will shape the implementation of an adapter that enables gym compliance.
I use compatibility to refer to Assetto Corsa being a Windows native application and my preference if to develop control systems on Linux.
At fist I tried to use Proton and WINE to enable the program to run on Ubunutu.
This ended up being a time sink with no significant headway after a few days work and many different tutorials.
Instead I have opted to change the design of the adapter to enable Assetto Corsa to be executed in Windows and forward game state via sockets to our control system.
By doing this we are able to run Assetto Corsa or control in virtual machines or other physical machines each with there own different OS.

Assetto Corsa provides three main ways to inference with game state.
The most convenient appears to be the [python ac package](https://www.assettocorsa.net/forum/index.php?threads/python-doc-update-25-05-2017.517/), however this can only be used in applications executed inside Assetto Corsa.
This provided immediate friction when installing additional packages into the version of python used by Assetto Corsa so was abandoned.
Out of the box Assetto Corsa also provides [UPD network telemetry](https://www.assettocorsa.net/forum/index.php?threads/ac-udp-remote-telemetry-update-31-03-2016.222/) that seemed as though it was exactly what we set out to build ourselves.
Although many vehicle types of telemetry data are forwarded to clients some aspects are not disclosed and these details are provided in bulk, indiscriminately.
For these reasons I will be using the final method Assetto Corsa provides, which is [accessing the games shared memory directly](https://www.assettocorsa.net/forum/index.php?threads/acc-shared-memory-documentation.59965/).
This exposes every aspect of the vehicle's current state used by the game's vehicle dynamics model.
Instead of building a socket server from scratch to aggregate and broadcast game state, we will use ROS2 to handle message passing of vehicle telemetry, camera feeds and control inputs.
For these control inputs to be applied to the game environment a virtual controller will be emulated using the [vgamepad](https://pypi.org/project/vgamepad/) python package.
To gather segmentation and depth data from Assetto Corsa we will follow two previous works that use DirectX rendering data to automatically create these labels. ([Work 1](https://download.visinf.tu-darmstadt.de/data/from_games/), [Work 2](https://openaccess.thecvf.com/content_cvpr_2018/papers/Krahenbuhl_Free_Supervision_From_CVPR_2018_paper.pdf))



