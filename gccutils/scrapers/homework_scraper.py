from gccutils.scraper_utils import ScraperUtils
from gccutils.components.homework import Homework, FileUpload
import traceback


class HomeworkScraper:

    def __init__(self, state: ScraperUtils, course):
        self.__state = state
        self.__course = course

    def fetch(self):
        self.nav_to_coursework()
        units = self.get_all_units()
        homeworks = []
        for unit_name, unit_elem in units:
            unit_homework = self.fetch_unit_homework(unit_name, unit_elem)
            for homework in unit_homework:
                homeworks.append(homework)
        return homeworks


    def nav_to_coursework(self):
        url = self.__course.url + 'Coursework.jnz'
        self.__state.http_get(url)

    def get_all_units(self):
        state = self.__state
        units = []
        panel = state.html.find('div', id='pg0_V__assignmentView__updatePanel')
        if panel is not None:
            for unit_element in panel.find_all('div', class_='drawer'):
                unit_name = unit_element.find('span', class_='unitName').get_text(strip=True)
                unit_container = unit_element.find('div', class_='assignmentView')
                units.append((unit_name, unit_container))
        return units

    def fetch_unit_homework(self, unit_name, unit_element):
        homeworks = []
        state = self.__state
        elements = self.get_all_homework_elements(unit_element)
        for name, link, status, is_open in elements:
            try:
                # navigate to the homework page
                state.http_get(link)

                assignment_element = state.html.find('div', class_='studentAssignmentDetailView')
                details = assignment_element.find('div', id='pg0_V__stuAssgnInfo__panInfo').get_text(separator=' ', strip=True)
                print(f'{name} {status} {details}')

            except:
                traceback.print_exc()

        return homeworks

    def get_all_homework_elements(self, unit_element):
        state = self.__state
        elements = []
        for assignment in unit_element.find_all('div', class_='assignmentDisplay'):
            name = assignment.find('a').get_text()
            link = state.to_url(assignment.find('a').get('href'))
            status = assignment.find('span', class_='assignmentStatusDisplay').get_text()
            is_open = 'open' in assignment['class']
            elements.append((name, link, status, is_open))
        return elements
