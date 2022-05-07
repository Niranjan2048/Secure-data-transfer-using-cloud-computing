import dropbox
from secret_filesystem.dropbox_token import token
from dropbox import DropboxOAuth2FlowNoRedirect

APP_KEY = "trbxejqrt11qk7x"
auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, use_pkce=True, token_access_type='offline')

auth_flow = DropboxOAuth2FlowNoRedirect(APP_KEY, use_pkce=True, token_access_type='offline')

authorize_url = auth_flow.start()
print("1. Go to: " + authorize_url)
print("2. Click \"Allow\" (you might have to log in first).")
print("3. Copy the authorization code.")
auth_code = input("Enter the authorization code here: ").strip()


oauth_result = auth_flow.finish(auth_code)

with dropbox.Dropbox(oauth2_refresh_token=oauth_result.refresh_token, app_key=APP_KEY) as dbx:
    def upload_image(img_str, id):
        dbx.files_upload(img_str, "/{}.bmp".format(id))


    def download_image(id, path):
        image_name = '{}.bmp'.format(id)
        r = dbx.files_download_to_file('{}{}'.format(path, image_name), '/{}'.format(image_name))


# dbx = dropbox.Dropbox(token)



