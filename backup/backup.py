import cmd
import locale
import os
import pprint
import shlex

from dropbox import client, rest, session

# XXX Fill in your consumer key and secret below
# You can find these at http://www.dropbox.com/developers/apps
APP_KEY = ''
APP_SECRET = ''
ACCESS_TYPE = 'dropbox'  # should be 'dropbox' or 'app_folder' as configured for your app

class StoredSession(session.DropboxSession):
    """a wrapper around DropboxSession that stores a token to a file on disk"""
    TOKEN_FILE = "token_store.txt"

    def write_creds(self, token):
        f = open(self.TOKEN_FILE, 'w')
        f.write("|".join([token.key, token.secret]))
        f.close()

    def delete_creds(self):
        os.unlink(self.TOKEN_FILE)

    def link(self):
        try:
            # first try to load stored access token
            stored_creds = open(self.TOKEN_FILE).read()
            self.set_token(*stored_creds.split('|'))
            print "[loaded access token]"
        except IOError:
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

class BackupUtils:
    """a wrapper around DropboxSession that stores a token to a file on disk"""

    def __init__(self):
        self.current_path = ''
        if APP_KEY == '' or APP_SECRET == '':
            exit("You need to set your APP_KEY and APP_SECRET!")
        self.sess = StoredSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
        try:
            self.sess.link()
        except rest.ErrorResponse, e:
            stdout.write('Error: %s\n' % str(e))    
        self.api_client = client.DropboxClient(self.sess)

    def list_folder(self):
        resp = self.api_client.metadata(self.current_path)

        if 'contents' in resp:
            for f in resp['contents']:
                name = os.path.basename(f['path'])
                encoding = locale.getdefaultlocale()[1]
                print ('%s\n' % name).encode(encoding)

    def do_get(self, from_path, to_path):
        """Copy file from Dropbox to local file."""
        to_file = open(os.path.expanduser(to_path), "wb")

        f = self.api_client.get_file(self.current_path + "/" + from_path)
        to_file.write(f.read())

def main():
    backup_client = BackupUtils()
    backup_client.list_folder()
    backup_client.do_get('Subscriptions-i42n.opml', 'Subscriptions-i42n.opml')

if __name__ == '__main__':
    main()