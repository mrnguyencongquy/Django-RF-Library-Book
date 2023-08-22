from projects.serializers import TaskSerializer, UpdateProjectSerializer
from projects.serializers import PredictingFileSerializer
from projects.models import Task, TrainingFile, Project, PredictingFile
from rest_framework import status
from celery import shared_task

from files.models import File
from django.conf import settings
from urllib.parse import urljoin
from django.utils import timezone
import csv
import json
import pandas as pd
import urllib3
import uuid
import logging
import os
from helpers import files_helper
from helpers import helper
from helpers import constant_var as CONSTANT_VAR

AWS_STORAGE_BUCKET_NAME = settings.S3_ACCESS_KEY['AWS_STORAGE_BUCKET_NAME']
logger = logging.getLogger(__name__)

datetime_helper = helper.MappingHelper()
directory_file = files_helper.DirectoryFile()
s3_initialize = files_helper.S3Initialize()


class ListProjectHelper(helper.MappingHelper):
    MAPPING_FILE = {
        'id': 'id',
        'projectName': 'project_name',
        'description': 'project_description',
        'creationDate': 'created_date',
        'lastUpdate': 'last_update'
    }
    def change_response_project(self, dataset):
        return super().change_response(dataset, self.MAPPING_FILE)


class ViewProjectHelper:
    def change_response(self, request):
        return {
            'projectName': request.data.get('project_name'),
            'createDate': datetime_helper.change_date_time(request.data.get('created_date')),
            'description': request.data.get('project_description')
        }
        
class FileProcessing:

    def read_header_from_csv_str(self, str_content):
        """
        :param file_name: str file path on local
        """
        if str_content:
            lines = str_content.splitlines()
            csvreader = csv.reader(lines)
            header_column = []
            header_column = next(csvreader)
            return header_column

    def read_header(self, file_name):
        """
        :param file_name: str file path on local
        """
        try:
            with open(file_name, 'r', encoding = 'shift_jis') as file:
                csvreader = csv.reader(file)
                header_column = []
                header_column = next(csvreader)
            return header_column
        except Exception as err:
            logger.error(err)
            try:
                with open(file_name, 'r', encoding = 'utf-8') as file:
                    csvreader = csv.reader(file)
                    header_column = []
                    header_column = next(csvreader)
                return header_column
            except Exception as err:
                logger.error(err)
                raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
    
    def read_label_file_header(self, file_name):
        """
        read a label file header file. these header is set as vertical line
        param: file_name str path local of the file
        return: list of str header of label file
        """
        try:
            with open(file_name, 'r', encoding = 'shift_jis') as file:
                headers = file.read().splitlines()
                headers.pop(0)
                return headers
        except Exception as err:
            logger.error(err)
            try:
                with open(file_name, 'r', encoding = 'utf-8') as file:
                    headers = file.read().splitlines()
                    headers.pop(0)
                    return headers
            except Exception as err:
                raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)

    def read_json(self, file_name):
        try:
            with open(file_name, encoding="shift_jis") as data_file:
                data_loaded_temp = json.load(data_file)
        except Exception as err:
            with open(file_name, encoding= "utf-8") as data_file:
                data_loaded_temp = json.load(data_file)
            logger.error(err)
        return data_loaded_temp

    def create_csv(self, data, file_name):
        try:
            df = pd.DataFrame(data)
            df.to_csv(file_name, encoding= "shift_jis",index=False, header=None)
            return file_name
        except Exception as err:
            logger.error(err)
            try:
                df = pd.DataFrame(data)
                df.to_csv(file_name, encoding= "utf-8",index=False, header=None)
                return file_name
            except Exception as err:
                logger.error(err)
                raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)

    def create_txt(self, data, map_name, map_file):
        try:
            data.insert(0,'Name')
            data.insert(1, map_name)
            with open(map_file, 'w', encoding = 'shift_jis') as f:
                for i in data:
                    f.write(i)
                    f.write('\n')
            return map_file
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                    status_code=status.HTTP_400_BAD_REQUEST)

    def create_json(self, data, file_name):
        try:
            with open(file_name, 'w', encoding='shift_jis') as file:
                json.dump(data, file, ensure_ascii=False)
            return file_name
        except Exception as err:
            logger.error(err)
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                    status_code=status.HTTP_400_BAD_REQUEST)


class CallAPI:
    @shared_task(bind=True, time_limit=4800)
    def call_data_tool(self, data):
        logger.info('Start training data')
        headers = {
            'Content-Type': CONSTANT_VAR.APPLICATION_JSON
        }
        data_tool = json.dumps(data, ensure_ascii=False).encode("utf8")
        
        base_url = settings.DATA_TOOL_BASE_URL
        url = urljoin(base_url, 'api/process_training')
        
        http = urllib3.PoolManager()
        response = http.request('POST', url, headers=headers, body=data_tool)

        CallAPI().update_state_task(self, response.status)
        logger.info('Training data succeed')
        return response.status

    @shared_task(bind=True, time_limit=4800)
    def call_data_tool_update(self, data, update_project):
        logger.info('Start update training data')
        headers = {
            'Content-Type': CONSTANT_VAR.APPLICATION_JSON
        }
        data_tool = json.dumps(data, ensure_ascii=False).encode("utf8")
        
        base_url = settings.DATA_TOOL_BASE_URL
        url = urljoin(base_url, 'api/process_training')
        
        http = urllib3.PoolManager()
        response = http.request('POST', url, headers=headers, body=data_tool)
        if response.status == 200:
            # data_update_project
            user_id = update_project['user_id']
            project_id = update_project['project_id']
            training_file_list_del = update_project['training_file_list_del']
            project_name = update_project['project_name']
            project_description = update_project['project_description']
            user_email = update_project['user_email']
            
            CallAPI().update_project_function(user_id, project_id, project_name, project_description, 
            user_email, training_file_list_del)
        else:
            user_id = update_project['user_id']
            training_file_id_list = update_project['training_file_id_list']
            CallAPI().delete_specific_file(user_id, training_file_id_list)  
            
        CallAPI().update_state_task(self, response.status)
        logger.info('Update training data succeed')
        return response.status

    def save_task(self, task):
        data = {
            'task_id': task.id,
            'state': 'PENDING'
        }
        serializer = TaskSerializer(data=data)
        if not serializer.is_valid():
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        serializer.save()

    def update_state_task(self, task, status):
        data = {}
        data['task_id'] = task.request.id
        if status == 200:
            data['state'] = 'SUCCESS'
        else:
            data['state'] = 'FAILURE'
        task = Task.objects.filter(task_id=task.request.id).first()
        serializer = TaskSerializer(instance=task, data=data)
        if not serializer.is_valid():
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        serializer.save()

    def update_project_function(self, user_id, project_id, project_name, project_description,
    user_email, training_file_list_del):
        s3_initialize.copy_temp_input_to_input(user_id, project_id)
        # Update project
        project = Project.objects.filter(id=project_id).first()    
        create_project = {
            'project_name': project_name,
            'project_description': project_description,
            'created_by': user_email,
            'last_update': timezone.now()
        }
        serializer = UpdateProjectSerializer(instance=project, data=create_project)
        if not serializer.is_valid():            
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)                         
        serializer.save()     
        # remove local file
        directory_file.remove_folder(user_id)
        #delete DB       
        for file_del in training_file_list_del:
            file_del = TrainingFile.objects.filter(id=file_del).first()
            file_del.delete() 
    
    def delete_specific_file(self,user_id, training_file_id_list): 
        #remove db
        for file_del in training_file_id_list:
            file_del = TrainingFile.objects.filter(id=file_del).first()
            file_del.delete()                        
        # remove local file
        directory_file.remove_folder(user_id)

    def save_file_in_s3(self, input_file_path, user_id, project_id, file_id):
        """add predict file in db and s3
        + Check file predict are already exist or Not
            + Add predict file to S3
            + Add predict file to DB        
        Args:
            input_file_path (_type_): input_file_path
            user_id (_type_): user_id
            project_id (_type_): project_id
            file_id (_type_): file_id

        Raises:
            helper.WWAPIException: Failed to save
        """
        try:
            predict_files = PredictingFile.objects.filter(project_id=project_id)
            lst_current_predict_file = []
            for item in predict_files:
                serializer_id = PredictingFileSerializer(instance=item)            
                file_id_id = serializer_id.data.get('file_id')
                lst_current_predict_file.append(file_id_id)
        except Exception as err:
            logger.error(err)

        if not str(file_id) in lst_current_predict_file:
            uuid_file_id = uuid.UUID(file_id)
            file_name = File.objects.filter(id=uuid_file_id).first().file_name
            file_name_s3 = str(user_id) + '/' + str(project_id) + '/input/data/' + str(os.path.basename(input_file_path)) #user_id/project_id/input/data/file_predict.csv
            results = {
                's3key': file_name_s3,
                'project_id': project_id,
                'file_id': str(file_id),
                'file_name': str(file_name)
            }
            return results
    
    def create_display_option(self, data):
        logger.info('Start update display option data')
        headers = {
            'Content-Type': CONSTANT_VAR.APPLICATION_JSON
        }
        data_tool = json.dumps(data, ensure_ascii=False).encode("utf8")        
        base_url = settings.DATA_TOOL_BASE_URL
        url = urljoin(base_url, 'api/create_display_result')
        
        http = urllib3.PoolManager()
        response = http.request('POST', url, headers=headers, body=data_tool)
        return response.status


    def process_predicting(self, data, predict_file_paths, file_infos):
        logger.info('Start predicting data')
        headers = {
            'Content-Type': CONSTANT_VAR.APPLICATION_JSON
        }
        data_tool = json.dumps(data, ensure_ascii=False).encode("utf8")        
        base_url = settings.DATA_TOOL_BASE_URL
        url = urljoin(base_url, 'api/process_predicting')
        
        http = urllib3.PoolManager()
        response = http.request('POST', url, headers=headers, body=data_tool)
        # CallAPI().update_state_task(self, response.status)
        if response.status == 200:
            try:
                results = []
                for index, file_id in enumerate(file_infos):
                    results.append(self.save_file_in_s3(predict_file_paths[index], data["user_id"], 
                                                        data["project_id"], file_id))
                # save data:\
                for index, result in enumerate(results):
                    serializer = PredictingFileSerializer(data=result)
                    if serializer.is_valid():
                        try:                    
                            s3 = s3_initialize.s3_init()
                            s3_bucket = AWS_STORAGE_BUCKET_NAME
                            # Update to S3
                            s3.meta.client.upload_file(Filename=str(predict_file_paths[index]), Bucket=s3_bucket, 
                                                    Key=result['s3key'])
                            #save to DB                              
                            serializer.save()                    
                        except Exception as err:
                            # remove local file
                            logger.error(err)
                            directory_file.remove_local_file("CSV")                
                            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                                    status_code=status.HTTP_400_BAD_REQUEST)
            except Exception as err:
                # remove local file
                logger.error(err)
                directory_file.remove_local_file("CSV")                
                raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                        status_code=status.HTTP_400_BAD_REQUEST)
        else:
            # remove local file
            directory_file.remove_local_file("CSV")
            raise helper.WWAPIException(helper.MessageReturn.COMMON_ERROR_MESSAGE,
                                    status_code=status.HTTP_400_BAD_REQUEST)
        return response.status


class ListProjectInfoHelper:
    def change_response(self, request):
        return {
            's3Key': request.data.get('s3key'),
            'mapName': request.data.get('map_name'),
            'mapSize': request.data.get('map_size'),
            'relationToUsermap': request.data.get('relation_to_usermap'),
            'fileIndex': request.data.get('file_index'),
            'id': request.data.get('file_id'), # file_id from TraningFile
            'isEdited': request.data.get('is_edited'),
        }
    def get_file_info(self, file):
        return {
            'fileName': file.file_name,
            'fileSize': file.file_size,
            'formatFile': file.file_extension
        }        

    def training_file(self, request):
        return {
            's3key': request.data.get('s3key'),
            'relation_to_usermap': request.data.get('relation_to_usermap')
        }


class ViewProjectInfoHelper:
    def change_response(self, request):
        return {
            'projectName': request.data.get('project_name'),
            'description': request.data.get('project_description')
        }


class CreateProjectHelper:
    def change_response_db_training_file(self, project_id, s3_project_key_data, file, file_id):
        return {
            's3key': s3_project_key_data,
            'map_size': file['mapSize'],
            'map_name': file['mapName'],
            'relation_to_usermap': file['relationToUsermap'],
            'project_id': project_id,
            'file_index': file['fileIndex'],
            'file_id': str(file_id),
            'is_edited': file['isEdited']
        }
    def list_user_data(self, request):
        user_map = request.data.get('userMap', None)
        return [user_map['mapName'], user_map['mapSize'], user_map['displayOption']]
