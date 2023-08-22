from helpers import helper
from rest_framework import status
from pathlib import Path
import glob, shutil
import os
import boto3
import re
from helpers import constant_var as CONSTANT_VAR
import logging
from boto3.session import Session
from django.conf import settings

logger = logging.getLogger(__name__)

AWS_S3_REGION_NAME = settings.S3_ACCESS_KEY['AWS_S3_REGION_NAME']
AWS_S3_ACCESS_KEY_ID = settings.S3_ACCESS_KEY['AWS_S3_ACCESS_KEY_ID']
AWS_S3_SECRET_ACCESS_KEY = settings.S3_ACCESS_KEY['AWS_S3_SECRET_ACCESS_KEY']
AWS_STORAGE_BUCKET_NAME = settings.S3_ACCESS_KEY['AWS_STORAGE_BUCKET_NAME']

class ListFileHelper(helper.MappingHelper):
    MAPPING_FILE = {
        'id': 'id',
        's3Key': 's3key',
        'fileName': 'file_name',
        'formatFile': 'file_extension',
        'fileSize': 'file_size',
        'fileType': 'file_type',
        'uploadBy': 'upload_by',
        'uploadDate': 'upload_date'
    }

    def change_response_file(self, dataset):
        return super().change_response(dataset, self.MAPPING_FILE)

class S3Initialize:
    def s3_init(self):
        session = Session(region_name=AWS_S3_REGION_NAME,
                        aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
                        aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY)
        s3 = session.resource('s3')
        return s3
    
    def s3_client(self):
        s3_client = boto3.client(service_name='s3', 
                    aws_access_key_id=AWS_S3_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_S3_SECRET_ACCESS_KEY)
        return s3_client
    # get file name in S3key
    def get_file_name_from_s3(self, s3key):
        filename = os.path.basename(s3key)
        return filename
    
    def read_content_file_from_s3(self, s3_key, encoding):
        """
        read content file from s3 key
        :param s3_key: str s3 key
        :param encoding: str encoding to open file
        :return str: content of file
        """
        try:
            s3 = self.s3_init()
            obj = s3.Object(AWS_STORAGE_BUCKET_NAME, s3_key)
            return obj.get()['Body'].read().decode(encoding)
        except Exception as err:
            print(err)
            return None

    # Change bucket name after deploy
    def delete_file_from_s3(self, list_key):
        s3 = self.s3_init()
        s3_bucket = AWS_STORAGE_BUCKET_NAME
        try:
            objects_to_delete = [{'Key': key} for key in list_key]
            if len(objects_to_delete):
                s3.meta.client.delete_objects(Bucket=s3_bucket, Delete={'Objects': objects_to_delete})
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
    
    def download_from_s3_to_userid(self, user_id, s3key, file_name):
        file_path = Path(__file__).resolve().parent.parent
        s3_folder = os.path.dirname(s3key)
        local_dir = os.path.join(file_path, str(user_id))
        s3 = self.s3_init()
        bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)
        try:
            for obj in bucket.objects.filter(Prefix=s3_folder):
                target = obj.key if local_dir is None \
                    else os.path.join(local_dir, os.path.relpath(obj.key, s3_folder))
                if not os.path.exists(os.path.dirname(target)):
                    os.makedirs(os.path.dirname(target))
                if obj.key == s3key:
                    bucket.download_file(obj.key, target)
        except KeyError:
            pass        
        file_name_path = os.path.join(local_dir, file_name)
        return file_name_path, local_dir  

    # Delete folder in bucket
    def delete_folder_from_s3(self, folder):
        s3 = self.s3_init()        
        bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)
        try:
            bucket.objects.filter(Prefix= str(folder)).delete()                   
        except Exception as err:
            logger.error(err)
    
    # Copy temp_input to input    
    def copy_temp_input_to_input(self, user_id, project_id):
        s3 = self.s3_init()        
        file_path = Path(__file__).resolve().parent.parent
        key = str(user_id) + "/" + str(project_id) + CONSTANT_VAR.TEMP_INPUT
        s3_folder = os.path.dirname(key)
        local_dir = os.path.join(file_path, str(user_id))
        bucket = s3.Bucket(AWS_STORAGE_BUCKET_NAME)

        for obj in bucket.objects.filter(Prefix=s3_folder):
            target = obj.key if local_dir is None \
                else os.path.join(local_dir, os.path.relpath(obj.key, s3_folder))
            if not os.path.exists(os.path.dirname(target)):
                os.makedirs(os.path.dirname(target))
            if obj.key != None:
                bucket.download_file(obj.key, target)
                s3key_new =  re.sub(CONSTANT_VAR.TEMP_INPUT, CONSTANT_VAR.INPUT_PATH, obj.key) 
                
            if os.path.basename(obj.key) == CONSTANT_VAR.CONFIG_FILE:                    
                s3key_path = os.path.join(file_path, str(user_id) + "/" + os.path.basename(obj.key))
            elif os.path.basename(obj.key) == CONSTANT_VAR.USERMAP_FILE: 
                s3key_path = os.path.join(file_path, str(user_id) + "/" + os.path.basename(obj.key))
            else:
                s3key_path = os.path.join(file_path, obj.key)
                if re.search(CONSTANT_VAR.TEMP_INPUT_DATA_PATH, s3key_path):
                    s3key_path = re.sub(str(user_id) + "/" + str(project_id) + CONSTANT_VAR.TEMP_INPUT_DATA_PATH, 
                    str(user_id) + "/data/", s3key_path)
                else:                        
                    s3key_path = re.sub(str(user_id) + "/" + str(project_id) + CONSTANT_VAR.TEMP_INPUT_LABEL_PATH, 
                    str(user_id) + "/label/", s3key_path)
            s3.meta.client.upload_file(Filename=s3key_path, Bucket=AWS_STORAGE_BUCKET_NAME, 
            Key=s3key_new)

class DirectoryFile:
    def rename_version_file_name(self, old_file_name, new_file_name):
        old_file_name = old_file_name + CONSTANT_VAR.NEW_CSV
        new_file_name = new_file_name + CONSTANT_VAR.NEW_CSV
        BASE_DIR = Path(__file__).resolve().parent.parent
        file_folder = os.listdir(BASE_DIR)
        if old_file_name in file_folder:
            os.rename(os.path.join(BASE_DIR, old_file_name),  os.path.join(BASE_DIR, new_file_name))
            return new_file_name
        else:
            return old_file_name
    
    def get_path(self, join_path):
        BASE_DIR = Path(__file__).resolve().parent.parent
        glob.glob(os.path.join(BASE_DIR, join_path))
        return glob.glob(os.path.join(BASE_DIR, join_path))

    def file_path(self, file_name):
        BASE_DIR = Path(__file__).resolve().parent.parent
        dir_file = os.path.join(BASE_DIR, file_name)
        return glob.glob(dir_file)
        
    def remove_local_file(self, file_extension):        
        BASE_DIR = Path(__file__).resolve().parent.parent
        try:
            if re.search(CONSTANT_VAR.SEARCH_CSV, file_extension):
                # remove csv
                dir_file = os.path.join(BASE_DIR, CONSTANT_VAR.CSV)
                files = glob.glob(dir_file)
                for file in files:
                    os.remove(file)
            elif re.search(CONSTANT_VAR.SEARCH_JSON, file_extension):
                # remove json
                dir_file = os.path.join(BASE_DIR, CONSTANT_VAR.JSON)
                files = glob.glob(dir_file)
                for file in files:
                    os.remove(file)
            elif re.search(CONSTANT_VAR.SEARCH_TXT, file_extension):
                # remove txt
                dir_file = os.path.join(BASE_DIR, CONSTANT_VAR.TXT)
                files = glob.glob(dir_file)
                for file in files:
                    if os.path.basename(file) != "requirements.txt":
                        os.remove(file)
            elif re.search(CONSTANT_VAR.SEARCH_PNG, file_extension):
                # remove png
                dir_file = os.path.join(BASE_DIR, CONSTANT_VAR.PNG)
                files = glob.glob(dir_file)
                for file in files:
                    os.remove(file)
        except KeyError:
            pass

    def is_duplicate_file_name(self, file_name):
        file_version = re.search(r"\(\d+\)$", file_name)
        if file_version != None: # if duplicate file_name has version
            file_version = file_version.group()
            version_number = file_version.replace("(", "")
            version_number = version_number.replace(")", "")
            version_number = int(version_number)
            version_number = str(version_number + 1) # create new version
            position= file_name.rfind("(")
            file_name = file_name[:position] + "(" + version_number + ")"
        else:
            file_name = file_name + "(1)" # new file
        return file_name # return new file name

    def remove_folder(self, user_id): 
        BASE_DIR = Path(__file__).resolve().parent.parent
        path = os.path.join(BASE_DIR, str(user_id))
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)  # remove the file
            elif os.path.isdir(path):
                shutil.rmtree(path)  # remove dir and all contains
        except Exception as err:
            logger.error(err)
    
    def remove_file(self, path): 
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.remove(path)  # remove the file
            elif os.path.isdir(path):
                shutil.rmtree(path)  # remove dir and all contains
        except Exception as err:
            logger.error(err)

class FileConfig:
    def file_size_in_kb(self, file_size):
        result = ''
        file_size_in_kb = file_size/1024
        number = float(file_size_in_kb) - int(file_size_in_kb)
        if(number > 0.499):
            file_size_in_kb = int(file_size_in_kb) + 1
        else:
            file_size_in_kb = int(file_size_in_kb)

        while file_size_in_kb >= 1000:
            file_size_in_kb, r = divmod(file_size_in_kb, 1000)
            result = ",%03d%s" %(r, result)
        return "%d%s" %(file_size_in_kb, result)
