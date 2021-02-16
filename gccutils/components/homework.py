
class FileUpload(object):

    def __init__(self, state, **values):
        self.__state = state
        self.name = values.pop('name')
        self.type = values.pop('type')
        self.size = values.pop('size')
        self.url = values.pop('url')

    def download_file(self):
        pass


class Homework(object):

    def __init__(self, state, **values):
        self.__state = state
        self.title = values.pop('title')
        self.unit = values.pop('unit')
        self.due = values.pop('due')
        self.grade = values.pop('grade')
        self.instructions = values.pop('instructions')
        self.provided_files = values.pop('provided_files')
        self.uploaded_files = values.pop('uploaded_files')

    def upload_file(self, file, comment=None):
        pass

    def add_a_comment(self, comment):
        pass

    def submit_homework(self):
        pass
