from gccutils.scraper_utils import ScraperUtils
from gccutils.components.course import Course
from gccutils.errors import UnauthorizedError
import traceback


class CourseScraper:

    def __init__(self, state: ScraperUtils):
        self.__state = state

    def fetch(self):
        self.nav_to_homepage()
        urls = self.get_course_urls()
        courses = []
        for url in urls:
            course = self.build_course(url)
            if course is not None:
                courses.append(course)
        return courses

    def nav_to_homepage(self):
        state = self.__state
        state.http_get(state.to_url('/ICS/'))

    def get_course_urls(self):
        state = self.__state

        all_links = []
        courses = self.__state.html.find('ul', id='myCourses')
        if courses is not None:
            for link_element in courses.find_all('a'):
                link_href = link_element.get('href')
                if link_href is not None:
                    all_links.append(state.to_url(link_href))

        return all_links

    def build_course(self, url):
        state = self.__state

        try:
            # navigate to the course information page
            state.http_get(url + 'Course_Information.jnz')

            # fetch course name and code
            course_name = state.html.find('div', id='TermInfo').find('b').get_text()
            course_code = state.html.find('div', id='TermInfo').find('p').get_text()\
                .replace(course_name, '').replace('(', '').replace(')', '').strip()
            course_section = url[-2]

            # fetch professor name
            professor_name = state.html.find('img', id='pg0_V_rptFaculty_ctl00_Photo').get('alt')
            # professor_email = state.html.find('a', id='pg0_V_rptFaculty_ctl00_EmailAddress').get_text()

            # fetch schedule information
            schedules, locations = [], []
            try:
                components = state.html.find('div', id='pg0_V_Schedule').find('p').get_text(separator='$$$', strip=True)
                components = components.replace(u'\xa0', '')
                for component in components.split('$$$'):
                    schedule, location = component.split('Location:')
                    if schedule not in schedules:
                        schedules.append(schedule)
                    if location not in locations:
                        locations.append(location)
            except AttributeError:
                pass

            # fetch course description
            description_element = state.html.find('div', id='CourseDescription')
            if description_element is not None:
                description_element = description_element.find('p')
            if description_element is not None:
                description = description_element.get_text(strip=True)
            else:
                description = None

            return Course(state, **dict(
                title=course_name,
                code=course_code,
                section=course_section,
                description=description,
                schedule=schedules,
                location=locations,
                professor=professor_name,
                url=url
            ))

        except Exception as e:
            if not isinstance(e, UnauthorizedError):
                traceback.print_exc()


if __name__ == '__main__':
    from getpass import getpass
    from main import pretty_print
    s = ScraperUtils()
    s.perform_login(input('Username: '), getpass())
    courses = CourseScraper(s).fetch()
    for course in courses:
        print(f'\nFETCHING HOMEWORK FOR {course.title.upper()}\n')
        coursework = course.fetch_coursework()
