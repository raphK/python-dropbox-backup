import cmd
import locale
import os
import pprint
import shlex
import errno
import datetime
import json
import time
import logging

from dropbox import client, rest, session
from dropbox.rest import ErrorResponse

ACCESS_TYPE = 'dropbox'  # should be 'dropbox' or 'app_folder' as configured for your app

class KeyStorage():

    KEY_FILE = "appkey_store.txt"

    def __init__(self):
        # try to read appkey and appsecret from previously stored settings file
        try:
            self.load_keystore()
            print '[loaded appkey and appsecret]'
            logging.debug('[loaded appkey and appsecret]')
        except (IOError, ValueError):
            self.read_appkey_from_user()
        while self.keystore['appkey'] == '' or self.keystore['appsecret'] == '':
            self.read_appkey_from_user()        

    def write_keystore(self):
        with open(self.KEY_FILE, 'w') as output:
            json.dump(self.keystore, output)
            print 'new keystore saved]'
            logging.debug('new keystore saved]')

    def load_keystore(self):
        with open(self.KEY_FILE, 'r') as input:
            self.keystore = json.load(input)

    def read_appkey_from_user(self):
        # it is not set yet, so read in from user
        print 'You need to set your APP_KEY and APP_SECRET!\nYou can find these at http://www.dropbox.com/developers/apps'
        self.keystore = json.loads('{ "appkey":"", "appsecret":"" }') # create json data structure to fill new data in
        print 'APPKEY:'
        self.keystore['appkey'] = raw_input()
        print 'APPSECRET:'
        self.keystore['appsecret'] = raw_input()
        # now store that data for later usage
        self.write_keystore()  

    def get_appkey(self):
        return self.keystore['appkey']

    def get_appsecret(self):
        return self.keystore['appsecret']

class StoredSession(session.DropboxSession):
    """a wrapper around DropboxSession that stores a token to a file on disk"""

    TOKEN_FILE = "token_store.txt"

    def write_tokenstore(self):
        with open(self.TOKEN_FILE, 'w') as output:
            json.dump(self.keystore, output)
            print '[new tokenstore saved]'
            logging.debug('[new tokenstore saved]')

    def load_tokenstore(self):
        with open(self.TOKEN_FILE, 'r') as input:
            self.keystore = json.load(input)

    def link(self):
        """establish link with dropbox"""
        try:
            # first try to load stored access token
            self.load_tokenstore()
            self.set_token(self.keystore['key'], self.keystore['secret'])
            print '[loaded access token]'
            logging.debug('[loaded access token]')
        except:
            # otherwise try to get new access token
            request_token = self.obtain_request_token()
            url = self.build_authorize_url(request_token)
            print "url:", url
            print "Please authorize in the browser. After you're done, press enter."
            raw_input()

            self.obtain_access_token(request_token)
            self.keystore = json.loads('{ "key":"", "secret":"" }') # create json data structure to fill new data in
            self.keystore['key'] = self.token.key
            self.keystore['secret'] = self.token.secret
            self.write_tokenstore()

class BackupUtils():
    """a tool collection to do a recursive download of the whole dropbox for backup usage""" 

    def __init__(self):
        key_storage = KeyStorage()
        self.sess = StoredSession(key_storage.get_appkey(), key_storage.get_appsecret(), ACCESS_TYPE)
        try:
            self.sess.link()
        except rest.ErrorResponse, e:
            print 'Error. Connection to Dropbox could not be established: %s\n' % str(e)
            logging.debug('Error. Connection to Dropbox could not be established: %s\n', str(e))
            return # exit backup process - without connection with dropbox that can not work
        self.api_client = client.DropboxClient(self.sess)
        now = datetime.datetime.now()
        date_string = now.strftime('%Y-%m-%d_%H-%M')
        self.backup_folder_name = 'dropbox_backup_' + date_string

    def ensure_dir(self, path):
        """ensure that the given path exists in local filesystem. if not create the directory"""
        # check if there is actually a folder that has to be created
        if path != '':
            try:
                # try to create it
                os.makedirs(path)
            except OSError as exception:
                # raise all errors except of the error that shows us that the dir already exists already
                if exception.errno != errno.EEXIST:
                    raise

    def download_file(self, from_path, to_path):
        """Copy file from Dropbox to local file."""
        print 'Downloading %s' % from_path
        logging.debug('Downloading %s', from_path)
        # path to file
        file_path = os.path.expanduser(to_path)
        # directory that may have to be created
        (dir_path, tail) = os.path.split(to_path)
        self.ensure_dir(dir_path) # create if it does not exist
        # open the file to write to
        to_file = open(file_path, "wb")

        # try to download 5 times to handle http 5xx errors from dropbox
        for attempts in range(5):
            try:
                f = self.api_client.get_file(from_path)
                to_file.write(f.read())
                return
            except rest.ErrorResponse:
                print 'An error occured while downloading. Will try again in some seconds.'
                logging.debug('An error occured while downloading. Will try again in some seconds.')
                time.sleep(attempts*10+5) # sleep some secs

    def list_folder(self, folderPath):
        """list a given directory on dropbox"""
        print '# LISTING: %s' % folderPath
        resp = self.api_client.metadata(folderPath)

        if 'contents' in resp:
            for f in resp['contents']:
                name = os.path.basename(f['path'])
                encoding = locale.getdefaultlocale()[1]
                if f['is_dir']:                
                    print ('[D] %s' % name).encode(encoding)
                else:
                    print ('[F] %s' % name).encode(encoding)

    def download_folder(self, folderPath):
        """download a given dropbox folder recursively"""

        # try to download 5 times to handle http 5xx errors from dropbox
        for attempts in range(5):
            try:
                resp = self.api_client.metadata(folderPath)
                # also ensure that response includes content
                if 'contents' in resp:
                    for f in resp['contents']:
                        name = os.path.basename(f['path'])
                        complete_path = os.path.join(folderPath, name)
                        if f['is_dir']:            
                            # do recursion to also download this folder
                            self.download_folder(complete_path)
                        else:
                            # download the file
                            self.download_file(complete_path, os.path.join(self.backup_folder_name, complete_path))
                else:
                    raise ValueError
            except (rest.ErrorResponse, ValueError):
                print 'An error occured while listing a directory. Will try again in some seconds.'
                logging.debug('An error occured while listing a directory. Will try again in some seconds.')
                time.sleep(attempts*10+5) # sleep some secs

    def backup_dropbox(self):
        """backup the whole dropbox recursively"""
        self.download_folder('')

def main():
    init_logging()
    backup_client = BackupUtils()
    backup_client.backup_dropbox()


def init_logging():
    """setup logfile name"""
    now = datetime.datetime.now()
    date_string = now.strftime('%Y-%m-%d_%H-%M')
    logfile_name = 'dropbox_backup_' + date_string + '.log'
    logging.basicConfig(filename=logfile_name,level=logging.DEBUG)    

if __name__ == '__main__':
    main()
