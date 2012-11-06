#Python Dropbox Backup

## Why use this script?
This is a python2 script to backup your whole dropbox via the Dropbox REST-API. This is especially useful for environements without x-server to backup your dropbox.

## What are the requirements?

This script requires the Dropbox Python SDK. It can be downloaded here:

https://www.dropbox.com/developers/reference/sdk

You can also use the python package installer:

`pip install dropbox`

Note: Sometimes you need to use pip2 or pip2.7 (you get the idea) for the python2 dependencies.

## How to use?

`python2 backup_dropbox.py`

When launched for the first time it will ask you to enter an APPKEY and an APPSECRET. You'll need to register with Dropbox to get an API key:

https://www.dropbox.com/developers/apps

If you have done that you will be asked to open an URL in your browser to grant the backup script access to your dropbox.

You only have to do all this for the first time. All keys will be stored in a keyfile. If you need to do changes to this data later either edit the files manually or remove the file and run through the setup process of the script again.

_Please note:_ The keystorage file format changed (and will change) several times as this part is under heavy developement right now. If you experience problems with your old keystorage files, please delete them and run again through the setup process. That will generate the keystorage files with the current format.

You're done! The script will now create a new folder with the current date and download the whole dropbox into that folder. Time to get a coffee ;)

## What will be done in the future?

* easy setup with setuptools
* create only one single keystorage file

## Feature requests?

Please leave me a message!
