
import requests
import requests_oauthlib

base_url = 'https://www.googleapis.com'
response = requests.get(f'{base_url}/drive/v3/about')
print(response.text)