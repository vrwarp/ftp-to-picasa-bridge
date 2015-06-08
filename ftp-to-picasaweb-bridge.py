import base64
import hashlib
import os
import pyftpdlib.handlers
import pyftpdlib.servers
import picasaweb
import tempfile

class MyHandler(pyftpdlib.handlers.FTPHandler):

    def on_connect(self):
        print "%s:%s connected" % (self.remote_ip, self.remote_port)

    def on_disconnect(self):
        # do something when client disconnects
        pass

    def on_login(self, username):
        # do something when user login
        pass

    def on_logout(self, username):
        # do something when user logs out
        pass

    def on_file_sent(self, file):
        # do something when a file has been sent
        pass

    def on_file_received(self, file):
        # do something when a file has been received
        picasaweb.upload_photo(file)
        os.remove(file)
        pass

    def on_incomplete_file_sent(self, file):
        # do something when a file is partially sent
        pass

    def on_incomplete_file_received(self, file):
        # remove partially uploaded files
        os.remove(file)

class DummyHashAuthorizer(pyftpdlib.handlers.DummyAuthorizer):

    def validate_authentication(self, username, password, handler):
        hashed_password = base64.b64encode(hashlib.sha512(password).digest())
        return self.user_table[username]['pwd'] == hashed_password

temp_dir = tempfile.mkdtemp()
print "Temp directory: %s" % temp_dir
authorizer = DummyHashAuthorizer()
authorizer.add_user(
    'btsai', '0LLO0HtbyAoXnFtIEbDol+ZsL/zi91ZlMNse0RtiMsLI36HX8nNdrGtwK07yW6bFee2/VP/hQr+K6JW/xuP+Vw==',
    homedir=temp_dir,
    perm='elradfmw')
# authorizer.add_anonymous(homedir='.')

handler = MyHandler
handler.authorizer = authorizer
server = pyftpdlib.servers.FTPServer(('', 2121), handler)
server.serve_forever()

