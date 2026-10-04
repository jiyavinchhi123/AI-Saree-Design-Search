import httpx
import re

url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=14d82eec-204b-4c2f-b7e8-296a70dab67e&response_type=code&redirect_uri=https%3A%2F%2Fai-saree-design-search.onrender.com%2Fapi%2Fdata-sources%2Fonenote%2Fauth%2Fcallback&scope=Notes.Read+User.Read&state=test'
r = httpx.get(url)
print("Title:", re.findall(r'<title>(.*?)</title>', r.text))
matches = re.findall(r'AADSTS\d+:[^<"\']+', r.text)
print("AADSTS matches:", matches)
if "Sign in to your account" in r.text:
    print("Microsoft displayed standard Sign-in page! Redirect URI was accepted by Microsoft!")
else:
    print("Microsoft rejected redirect URI!")
