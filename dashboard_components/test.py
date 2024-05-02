from botocore.config import Config as botoConfig
from decouple import config
import boto3
import pandas as pd

s3_client = boto3.client('s3',aws_access_key_id=config('AWS_ACCESS_KEY_ID'),
                                     aws_secret_access_key=config('AWS_SECRET_ACCESS_KEY'),
                                     region_name='eu-north-1')
"""
pythonusecase = s3_resource.Bucket(name = 'iclimabuilt')
for object in pythonusecase.objects.all():
          print(object.key)
s3_resource.Object('iclimabuilt', 'iclimabuilt_all.csv').download_file('iclimabuilt_all.csv')
"""

response = s3_client.get_object(Bucket='iclimabuilt', Key="iclimabuilt_all.csv")

status = response.get("ResponseMetadata", {}).get("HTTPStatusCode")

if status == 200:
    print(f"Successful S3 get_object response. Status - {status}")
    climadf = pd.read_csv(response.get("Body"))
    print(climadf.head())
else:
    print(f"Unsuccessful S3 get_object response. Status - {status}")