# Ping Summary

Ping Summary consists of four parts:
* The ping summariser. This pings the target (default 8.8.8.8) every second and every minute generates a summary of min, average and max ping times along with the number of pings dropped.
* Image creation utility. Creates an image for the passed date
* Summaries are saved to pingtest-summ.sqlite.  
Optionally the mkimage utility is also called to create a Ping summary graph image for the current day
* The summary web app. This simple webapp runs on port 2233 and displays the ping summary image for the selected day.  
The graph image is refreshed every minute.

## Commands
### startenv
This has two modes:
1. Run by itself it will configure the environment and return you to the set environment in a bash subshell. Use `exit` to exit.
1. Prepended to another command (eg: `./startenv ./mkimage -h`) it will set up the environment and run the command and arguments

```shell
$ ./startenv ./mkimage.py -h
usage: mkimage.py [-h] date
```

### startapp.sh
Starts the webapp.

```shell
$ ./startenv ./startwebapp.sh -h
Usage: startwebapp.sh: [-h]
```

### pingsumm.py
The ping summary process. It needs to run continuously. Does not daemonise as it is likely to be run by things like systemd, launchd, etc that do not require daemonisation.

```shell
$ ./startenv ./pingsumm.py -h
usage: pingsumm.py [-h] [-v] [-d] [-i] [target]

Pings a target and every minute generates a summary of min, average and max ping times along with the number of pings dropped.
Summaries are saved to pingtest-summ.sqlite

positional arguments:
  target         Target to ping

optional arguments:
  -h, --help     show this help message and exit
  -v, --verbose  Display individual ping returns and 1 minutes summaries to stderr
  -d, --debug    Display debug information
  -i, --image    Dump today's summary graph every 5 minutes
  ```

  ### mkimage.py
  Creates a ping summary graph image in `./data/images`

  ```shell
  $ ./startenv ./mkimage.py -h
usage: mkimage.py [-h] date

Generates a Graph for the requested date and outputs it to a file

positional arguments:
  date        Date to graph in the format YYYY-MM-DD

optional arguments:
  -h, --help  show this help message and exit
  ```

  ![Ping Summary Graph](https://raw.githubusercontent.com/NZJourneyMan/pingsummary/main/misc/README.png "Ping Summary Graph")

  ### install.sh
  Install script. Requires root privs. 

 ```shell
 $ ./install.sh -h
install.sh: [-h] [install dir]

Install dir defaults to /usr/local/pingsumm
This script is idempotent, so can be rerun without causing problems
```

### mkreqs
Using `pip freeze > requirements.txt` is way too noisy (but  manages to miss `wheel`) and includes too many packages, so I used `pipreqs`. However `pipreqs` misses some required libraries, so this wrapper uses `pipreqs` and manually adds in the missing libraries.