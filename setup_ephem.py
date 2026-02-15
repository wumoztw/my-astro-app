import os
import urllib.request

EPHEM_DIR = 'ephem'
FILES_TO_DOWNLOAD = {
    'sepl_18.se1': 'https://www.astro.com/ftp/swisseph/ephe/sepl_18.se1',
    'semo_18.se1': 'https://www.astro.com/ftp/swisseph/ephe/semo_18.se1',
    'seas_18.se1': 'https://www.astro.com/ftp/swisseph/ephe/seas_18.se1',
}

def download_ephem():
    if not os.path.exists(EPHEM_DIR):
        print(f"Creating directory: {EPHEM_DIR}")
        os.makedirs(EPHEM_DIR)
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    for filename, url in FILES_TO_DOWNLOAD.items():
        target_path = os.path.join(EPHEM_DIR, filename)
        if not os.path.exists(target_path):
            print(f"Downloading {filename} from {url}...")
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req) as response, open(target_path, 'wb') as out_file:
                    out_file.write(response.read())
                print(f"Successfully downloaded {filename}")
            except Exception as e:
                print(f"Failed to download {filename}: {e}")
        else:
            print(f"{filename} already exists.")

if __name__ == "__main__":
    download_ephem()
