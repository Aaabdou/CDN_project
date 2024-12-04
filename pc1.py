import subprocess

subprocess.run(["ip","addr","add","137.8.7.2/24","dev","eth0"])
subprocess.run(["route","add","default","gw","137.8.7.1"])