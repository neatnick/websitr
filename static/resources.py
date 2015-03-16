import urllib.request
import json, shutil, os


def populate_resource(resource_name, resource_url):
	try:
		with urllib.request.urlopen(resource_url) as response, open(resource_name, 'wb') as f:
			shutil.copyfileobj(response, f)
	except Exception as e:
		message = "Could not populate resource" if not (os.path.isfile(resource_name)) else "Unable to update resource"
		print("{}: {}\n  from url: {}\nException: {}".format(message, resource_name, resource_url, e))
	return os.path.isfile(resource_name)


with open('resources.json', 'r') as f_data, open('resources.scss', 'w') as f_out:
	resources = json.loads(f_data.read())
	for resource in resources:
		if not (populate_resource(resource['name'], resource['url'])):
			f_out.write("//")
		f_out.write("@import \"{}\";\n".format(resource['name']))