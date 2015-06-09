import gdata
import gdata.gauth
import gdata.photos.service
import httplib2
import os.path
import PIL.Image
import sys
import time
import webbrowser

from oauth2client import client
from oauth2client.file import Storage

def _authorize(self, client):
    client.auth_token = self
    request_orig = client.http_client.request
    
    def new_request(*args, **kwd):
        response = request_orig(*args, **kwd)
        if response.status == 401:
            refresh_response = self._refresh(request_orig)
            if self._invalid:
                return refresh_response
            else:
                self.modify_request(*args, **kwd)
                return request_orig(*args, **kwd)
        else:
            return response

    client.http_client.request = new_request
    return client

gdata.gauth.OAuth2Token.authorize = _authorize

def _get_credentials(http):
    storage = Storage('/home/btsai/.ftp-to-picasaweb-bridge/credentials')
    credentials = storage.get()

    if (credentials is not None and
        credentials.refresh_token is not None):
        if credentials.access_token_expired:
            credentials.refresh(http)
        return credentials

    flow = client.flow_from_clientsecrets(
        '/home/btsai/.ftp-to-picasaweb-bridge/client_secrets.json',
        scope='https://picasaweb.google.com/data/',
        redirect_uri='urn:ietf:wg:oauth:2.0:oob')
    
    auth_uri = flow.step1_get_authorize_url()
    
    sys.stdout.write("Opening window for authorization...\n")
    sys.stdout.flush()
    
    # webbrowser.open_new(auth_uri)
    print auth_uri
 
    sys.stdout.write("Authorization Code: ")
    sys.stdout.flush()

    auth_code = sys.stdin.readline()
    auth_code = auth_code[:-1]

    credentials = flow.step2_exchange(auth_code)
    storage.put(credentials)

    return credentials

http = httplib2.Http()
credentials = _get_credentials(http)
http_auth = credentials.authorize(http)
auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
gd_client = gdata.photos.service.PhotosService(
    email="default",
    additional_headers={'Authorization' : 'Bearer %s' % credentials.access_token}) # For example.
gd_client = auth2token.authorize(gd_client)

albums = gd_client.GetUserFeed()

def _get_album(client, name, refresh=False):
    global albums
    if refresh:
        albums = client.GetUserFeed()

    for album in albums.entry:
        if album.title.text == name and int(album.numphotos) < int(albums.maxPhotosPerAlbum):
            return album

    if refresh:
        print "Creating album %s" % name
        return client.InsertAlbum(title=name, summary='', access='private')
    else:
        return _get_album(client, name, True)

def _upload_photo(client, path):
    image = PIL.Image.open(path)
    datetime = str(image._getexif()[306]) # 306 is DateTime
    del image

    parsed_datetime = time.strptime(datetime, "%Y:%m:%d %H:%M:%S")

    album_name = time.strftime("%m-%Y (auto)", parsed_datetime)

    album = _get_album(client, album_name)
    
    album_url = '/data/feed/api/user/default/albumid/%s' % (album.gphoto_id.text)
    photo = client.InsertPhotoSimple(
        album_url, os.path.basename(path), None, path, content_type='image/jpeg')

def upload_photo(path):
    global auth2token
    global credentials
    global gd_client
    global http

    attempts = 0
    while True:
        try:
            if credentials.access_token_expired:
                credentials = _get_credentials(http)
                http_auth = credentials.authorize(http)
                auth2token = gdata.gauth.OAuth2TokenFromCredentials(credentials)
                gd_client = gdata.photos.service.PhotosService(
                    email="default",
                    additional_headers={'Authorization' : 'Bearer %s' % credentials.access_token}) # For example.
                gd_client = auth2token.authorize(gd_client)

            _upload_photo(gd_client, path)
            break
        except:
            print "Unexpected error:", sys.exc_info()[0]
            print "Sleeping for", (attempts * 10)
            time.sleep(attempts * 10)

# filename = "/shared/iss/photos/2015-04-07/BU2A4400.JPG"
