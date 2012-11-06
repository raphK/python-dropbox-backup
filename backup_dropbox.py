import cmd
import locale
import os
import pprint
import shlex
import errno
import datetime
import json

from dropbox import client, rest, session

TOKEN_FILE = "token_store.txt"
ACCESS_TYPE = 'dropbox'  # should be 'dropbox' or 'app_folder' as configured for your app

class KeyStorage():

    KEY_FILE = "appkey_store.txt"

    def __init__(self):
        # try to read appkey and appsecret from previously stored settings file
        try:
            self.load_keystore()
            print '[loaded appkey and appsecret]'
        except (IOError, ValueError):
            self.read_appkey_from_user()
        while self.keystore['appkey'] == '' or self.keystore['appsecret'] == '':
            self.read_appkey_from_user()        

    def write_keystore(self):
        with open(self.KEY_FILE, 'w') as output:
            json.dump(self.keystore, output)

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

    def write_creds(self, token):
        f = open(TOKEN_FILE, 'w')
        f.write("|".join([token.key, token.secret]))
        f.close()

    def delete_creds(self):
        os.unlink(TOKEN_FILE)

    def link(self):
        try:
            # first try to load stored access token
            stored_creds = open(TOKEN_FILE).read()
            self.set_token(*stored_creds.split('|'))
            print '[loaded access token]'
        except:
            # otherwise try to get new access token
            request_token = self.obtain_request_token()
            url = self.build_authorize_url(request_token)
            print "url:", url
            print "Please authorize in the browser. After you're done, press enter."
            raw_input()

            self.obtain_access_token(request_token)
            self.write_creds(self.token)

    def unlink(self):
        self.delete_creds()
        session.DropboxSession.unlink(self)

class BackupUtils():
    """a tool collection to do a recursive download of the whole dropbox for backup usage""" 

    def __init__(self):
        key_storage = KeyStorage()
        self.sess = StoredSession(key_storage.get_appkey(), key_storage.get_appsecret(), ACCESS_TYPE)
        try:
            self.sess.link()
        except rest.ErrorResponse, e:
            # TODO exit here
            print 'Error. Connection to Dropbox could not be established: %s\n' % str(e)
        self.api_client = client.DropboxClient(self.sess)
        now = datetime.datetime.now()
        date_string = now.strftime('%Y-%m-%d_%H-%M')
        self.backup_folder_name = 'dropbox_backup_' + date_string

    def ensure_dir(self, path):
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
        # path to file
        file_path = os.path.expanduser(to_path)
        # directory that may have to be created
        (dir_path, tail) = os.path.split(to_path)
        self.ensure_dir(dir_path) # create if it does not exist
        # open the file to write to
        to_file = open(file_path, "wb")

        f = self.api_client.get_file(from_path)
        to_file.write(f.read())        

    def list_folder(self, folderPath):
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
        resp = self.api_client.metadata(folderPath)

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

    def backup_dropbox(self):
        self.download_folder('')

def main():
    backup_client = BackupUtils()
    backup_client.backup_dropbox()

if __name__ == '__main__':
    main()
