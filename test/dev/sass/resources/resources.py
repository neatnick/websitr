import urllib.request
import json, shutil, os


def populate_resource(resource_name, url):
	try:
		response = urllib.request.urlopen(url)
		f = open(resource_name + '.scss', 'wb')
		shutil.copyfileobj(response, f)
	except Exception as exception:
		if not (os.path.isfile(resource_name + '.scss')):
			print("Could not populate resource:", resource_name, "\n  from url:", url)
			print("Exception:", exception)
			return False
		print("Unable to update resource:", resource_name, "\n  from url:", url)
		print("Exception:", exception)
	return True

f = open('resources.json', 'r')
resources = json.loads(f.read())
resource_string = ""
for resource in resources:
	if not (populate_resource(resource['name'], resource['url'])):
		resource_string += "//"
	resource_string += "@import \"{}\";\n".format(resource['name'])

f = open('resources.scss', 'w')
f.write(resource_string)