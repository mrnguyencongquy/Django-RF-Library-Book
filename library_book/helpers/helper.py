from rest_framework import exceptions
from rest_framework import status
from datetime import datetime

class MessageReturn:
    COMMON_ERROR_MESSAGE = 'common error'
    LOGIN_MESSAGE = 'Incorrect email address or password. Please check again.'
    CURRENT_PASSWORD_FAILED = '現在のパスワードが一致しません。もう一度お試しください。'
    EMAIL_EXISTED_MESSAGE = 'Current passwords do not match. Please try again.'
    # Uploaded file cannot exceed 100000KB. Please upload another file.
    UPLOAD_FILE_SIZE = 'Uploaded files cannot exceed 10,240KB. Please upload another file.'
    # Missing file type
    MISSING_FILE_TYPE = "Missing file type"
    # The files relating to this project have been deleted, so you cannot edit the project".    
    FILE_HAS_BEEN_REMOVED = "The project cannot be edited because the files related to this project have been deleted."
    # Validate user map label
    ERROR_USER_MAP_LABEL = "Incorrect file. Please select another file."
    
class WWAPIException(exceptions.APIException):
	def __init__(self, detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR):
		self.status_code = status_code
		self.detail = detail

class MappingHelper:
    def change_response(self, dataset, mapping_object):
        result = []
        for data in dataset:
            temp = {}
            for key, val in mapping_object.items():
                if val in self.get_list_datetime_to_format():
                    data[val] = self.change_date_time(data[val])
                if isinstance(val, str):
                    temp[key] = data[val]
                else:
                    temp[key] = val(data)
            result.append(temp)
        return result

    def get_list_datetime_to_format(self):
        return ['register_date', 'upload_date', 'created_date', 'last_update']

    def change_date_time(self, date_time):
        date_time = datetime.strptime(date_time, '%Y-%m-%dT%H:%M:%S.%fZ')
        return date_time.strftime('%Y/%m/%d %H:%M:%S')