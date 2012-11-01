#Python Dropbox Backup

## Why use this script?
This is a python2 script to backup your whole dropbox via the Dropbox REST-API. This is especially useful for environements without x-server to backup your dropbox.

## What are the requirements?

This script requires the Dropbox Python SDK. It can be downloaded here:

https://www.dropbox.com/developers/reference/sdk

You can also use the python package installer:

'pip install dropbox'

Sometimes you need to use pip2 for the python2 dependencies:

'pip2 install dropbox'

## How to use?

'python2 backup_dropbox.py'

When launched for the first time it will tell you to add APPKEY and APPSECRET to backup_dropbox.py. You'll need to register with Dropbox to get an API key:

https://www.dropbox.com/developers/apps

If you have done that you will be asked to open an URL in your browser to grant the backup script access to your dropbox.

You're done! The script will now create a new folder with the current date and download the whole dropbox into that folder. Time to get a coffee ;)

## What will be done in the future?

* interactive APPKEY setting
* store APPKEY in keystore too
* easy setup with setuptools

## Feature requests?

Please leave me a message!