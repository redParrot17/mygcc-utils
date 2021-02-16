from gccutils.scrapers.homework_scraper import HomeworkScraper


class Course(object):

    def __init__(self, state, **values):
        self.__state = state
        self.title = values.pop('title')
        self.code = values.pop('code')
        self.section = values.pop('section')
        self.description = values.pop('description')
        self.schedule = values.pop('schedule')
        self.location = values.pop('location')
        self.professor = values.pop('professor')
        self.url = values.pop('url')

    def fetch_coursework(self):
        return HomeworkScraper(self.__state, self).fetch()

    def fetch_grades(self):
        pass
