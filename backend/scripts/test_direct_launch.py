import subprocess
import time
import os

def test_launch():
    # URL 1: The malformed URL without parameters
    url1 = "onenote:https://d.docs.live.net/b6ecec459b998637/OneNote%20Notebooks/My%20Notebook/New%20Section%202.one#Saree%20designs"
    print("Testing direct launch of URL 1:", url1)
    subprocess.run(f'cmd /c start "" "{url1}"', shell=True)
    time.sleep(5)
    
    # Check what window opened
    out = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq ONENOTE.EXE']).decode()
    print("Process status:\n", out)

if __name__ == "__main__":
    test_launch()
