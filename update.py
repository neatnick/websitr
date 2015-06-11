import os, subprocess, time
import zipfile, shutil, sys

sites = {'appswithstyle.net': '8000', 'nickbalboni.com': '8010'}

while True:
	time.sleep(5)
	for key, value in sites.items():
		zip_location = os.path.join(key, 'www.zip')
		if os.path.isfile(zip_location):
			try:
				# stop site if process is running
				command = "python {0}/app.py --deploy -p {1}".format(key, value)
				subprocess.call(
					"kill -9 $( ps aux | grep \"%s\" | awk '{print $2}' )" % command,
					shell=True )
				# replace old site with new
				with zipfile.ZipFile(zip_location, 'r') as zip_file: 
					zip_file.extractall()
				shutil.rmtree(key)
				os.rename('www', key)
				open(os.path.join(key, 'log.txt'), 'w')
				# start site process
				time.sleep(1) # something funny was going on here
				subprocess.Popen("nohup {} > /dev/null 2>&1 &".format(command), shell=True)
			except Exception as e:
				# dont know whats going on, just restart the script
				# (this is probably a very, very bad idea)
				subprocess.Popen("python watch.py &", shell=True)
				sys.exit(1)
			

