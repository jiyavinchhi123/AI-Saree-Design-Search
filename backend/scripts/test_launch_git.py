import subprocess
import time

url_git = "onenote:https://d.docs.live.net/b6ecec459b998637/OneNote%20Notebooks/My%20Notebook/Quick%20Notes.one#Difference%20between%20Git%20and%20GitHub&section-id={a2760d1e-79bd-48ac-85fd-3f084ee70322}&page-id={7bd5e942-9e4d-466c-87a5-025e3479e304}&end"

print("Launching URL with Quick Notes / Git page:")
print(url_git)
subprocess.run([r"C:\Program Files\Microsoft Office\Root\Office16\ONENOTE.EXE", "/hyperlink", url_git])

time.sleep(3)
out = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq ONENOTE.EXE']).decode()
print("Process status:\n", out)
