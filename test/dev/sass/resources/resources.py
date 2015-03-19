import urllib.request
import shutil, os


RESOURCES = [ { "name": "flex-box_mixins.scss",
        		"url": "https://raw.githubusercontent.com/mastastealth/sass-flex-mixin/master/flex.scss" },

    		  { "name": "media-query_mixins.scss",
        		"url": "https://raw.githubusercontent.com/paranoida/sass-mediaqueries/master/_media-queries.scss" },

    		  { "name": "general_mixins.scss",
        		"url": "https://raw.githubusercontent.com/SwankSwashbucklers/some-sassy-mixins/master/mixins.scss" } ]


def populate_resource(resource_name, resource_url):
	try:
		with urllib.request.urlopen(resource_url) as response, open(resource_name, 'wb') as f:
			shutil.copyfileobj(response, f)
	except Exception as e:
		message = "Could not populate resource" if not (os.path.isfile(resource_name)) else "Unable to update resource"
		print("{}: {}\n  from url: {}\nException: {}".format(message, resource_name, resource_url, e))
	return os.path.isfile(resource_name)


with open('resources.scss', 'w') as f:
	for resource in RESOURCES:
		if not (populate_resource(resource['name'], resource['url'])):
			f.write("//")
		f.write("@import \"{}\";\n".format(resource['name']))