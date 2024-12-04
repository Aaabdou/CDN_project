import subprocess

subprocess.run(["ip","addr","add","197.8.7.2/24","dev","eth0"])
subprocess.run(["route","add","default","gw","197.8.7.1"])