import os
import pandas as pd
import requests
import zipfile
import io

try:
    os.system("rm -rf iclimabuilt")
except:
    pass
r = requests.get('https://datashare.tu-dresden.de/s/eGiQYya35onSAt5/download')
print(r)
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("")

dfs = []
for f in os.listdir('iclimabuilt'):
    if f.endswith('.xlsx'):
        dfs.append(pd.read_excel(os.path.join('iclimabuilt',f)))
df=pd.concat(dfs)
df.to_csv('iclimabuilt_all.csv')
os.system("rm -rf iclimabuilt")

r = requests.get('https://datashare.tu-dresden.de/s/TcytZEeF9izWRSd/download')
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("")
