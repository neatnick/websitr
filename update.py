from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileCreationHandler(FileSystemEventHandler):

    def __init__(self, path, callback):
        self.path = path
        self.callback = callback
        self.observer = Observer()
        self.observer.schedule(self, path, recursive=False)
        self.observer.start()
        self.observer.join()

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('www.zip'):
            self.observer.stop() # stop watching
            self.callback(self.path) # call callback

 
from subprocess import call, Popen
from zipfile import ZipFile
from time import sleep
from os.path import join

def deploy_site(site_name):
    port = sites[site_name]
    # stop site if process is running
    command = "python {0}/app.py --deploy -p {1}".format(site_name, port)
    call("kill -9 $( ps aux | grep \"%s\" | awk '{print $2}' )" % command, 
        shell=True )
    # replace old site with new
    with ZipFile(zip_location, 'r') as zip_file: 
        zip_file.extractall()
    shutil.rmtree(site_name)
    os.rename('www', site_name)
    open(join(site_name, 'log.txt'), 'w')
    # start site process
    sleep(1) # something funny was going on here
    Popen("nohup {} > /dev/null 2>&1 &".format(command), shell=True)

if __name__ == '__main__':
    sites = {
        'appswithstyle.net': '8000', 
          'nickbalboni.com': '8010'
    }

    for site in sites:
        FileCreationHandler(site, deploy_site)


