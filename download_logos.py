import urllib.request
import os

urls = {
    "berg-b": "https://companieslogo.com/img/orig/BERG-B.ST_BIG-e8af3fac.png",
    "lagr-b": [
        "https://images.seeklogo.com/logo-png/8/1/lagercrantz-group-logo-png_seeklogo-81790.png",
        "https://www.lagercrantz.com/files//logo.png"
    ],
    "addt-b": "https://companieslogo.com/img/orig/ADDT-B.ST_BIG-4d0d96c7.png"
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'Referer': 'https://companieslogo.com/'
}

for name, url_list in urls.items():
    if isinstance(url_list, str): url_list = [url_list]
    success = False
    for url in url_list:
        print(f"Downloading {name} from {url}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = response.read()
                if len(data) > 8000:
                    print(f"  Received {len(data)} bytes.")
                    ext = ".svg" if ".svg" in url else ".png"
                    with open(f"resources/{name}_logo{ext}", "wb") as f:
                        f.write(data)
                    success = True
                    break
        except Exception as e:
            print(f"  Error downloading {name} from {url}: {e}")
    if not success:
        print(f"  FAILED to download {name}")
