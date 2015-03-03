import os, sys
import errno
import argparse

# Command Line Interface
parser = argparse.ArgumentParser(
	prog="SITE_BUILDER", 
	formatter_class=argparse.ArgumentDefaultsHelpFormatter,
	description="Build Nick\'s prefered default project starting point for new websites."   +
	" The project will precompile sass files for css, and use bottle as the web framework." +
	" It will be geared towards deployment on a cherrypy server using a nginx reverse proxy.")
parser.add_argument("name", 
	type=str,
	metavar="NAME",
	nargs="?",
	default="untitled",
	help="the name of the project for the new website")
parser.add_argument("-p", "--path", 
	type=str,
	help="the path to the desired location of the new project")
args = parser.parse_args()



def fatal_exception(exception, message=""): #TODO: cleanup after failure?
	print("*******SCRIPT FAILED*******")
	if (message):
		print(message)
	print("Exception: ", exception)
	sys.exit(1)


# Create folder for new project
if not (args.path) is None:
	try:
		os.chdir(args.path)
	except OSError as exception:
		fatal_exception(exception, "Invalid path provided")

	try:
		os.makedirs(args.name)
		print("things")
	except OSError as exception:
		if (exception.errno == errno.EEXIST):
			while (response != "yes"): #regular expression here
				response = input("Folder already exists at", args.path, "with the desired project name.",
					"Do you wish to proceed (script will use this folder for the project)? [yes/no]")
			if (response)
		else:
			fatal_exception(exception, "Could not create project folder")
	os.chdir(args.name)

print(args.name)

