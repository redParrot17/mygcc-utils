from gccutils.asyncscrapers.scrapersession import AsyncScraperManager, AsyncScraperSession
import gccutils.errors as errors
import time
import re


class Course:

    def __init__(self, code, name, term, hours, requisites):
        self.code = code
        self.name = name
        self.term = term
        self.hours = hours
        self.requisites = requisites

    def __dict__(self):
        return {
            'code': self.code,
            'name': self.name,
            'term': self.term,
            'credits': self.hours,
            'requisites': self.requisites}

    def is_same(self, other):
        return self.code == other.code and self.term == other.term


class AsyncCourseScraperSession(AsyncScraperSession):
    COURSEURL = 'https://my.gcc.edu/ICS/Academics/Home.jnz'
    QUERYPARAMS = {
        'portlet': 'AddDrop_Courses',
        'screen': 'Advanced Course Search',
        'screenType': 'next'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.remaining_terms = []

    def run(self):
        """
        The primary method of this thread that controls the web-scraping of courses on https://my.gcc.edu/.

        Do not manually call this method. Use ScraperSession#start() instead.
        """

        start_time = time.time()
        callback = self.callback
        thread_num = self.thread_num
        num_threads = self.num_threads
        self.aborted = False

        print(f'scraper thread [{thread_num}|{num_threads}] starting')

        # perform initial setup
        self.nav_to_search()
        self.init_term_data()
        self.nav_to_first_term()

        while not self.aborted:
            while not self.aborted:

                table_rows = self.find_rows_to_parse()

                for table_row in table_rows:
                    if self.aborted: continue

                    try:
                        # build a course object from the row data
                        course = self.course_row_to_course(table_row)

                        # pass the course to the callback function
                        if course is not None:
                            callback(course)

                    except Exception as e:
                        # handle errors that occur during course creation or the callback
                        print(f'scraper thread [{thread_num}|{num_threads}] exception: {e}')

                # navigate to next page
                if not self.try_nav_next_page():
                    break  # stop if this was the last page

            # navigate to next term
            if not self.try_nav_next_term():
                break  # stop if this was the last term

        runtime = int(time.time() - start_time)
        print(f'scraper thread [{thread_num}|{num_threads}] stopping after {runtime} seconds')

    def nav_to_search(self):
        """
        Navigates to the course search page.

        This is a necessary first step prior to accessing any course.
        """
        self.dc.http_get(self.COURSEURL, params=self.QUERYPARAMS)

    def init_term_data(self):
        """
        Determines the course terms available for searching as well as which to start with.
        """

        html = self.dc.html
        if html is not None:
            term_selector_element = html.find('select', {'id': 'pg0_V_ddlTerm'})
            if term_selector_element is not None:
                for term_choice in term_selector_element.find_all('option'):
                    choice_value = term_choice.get('value')
                    selected = term_choice.get('selected', '') == 'selected'
                    if not selected:
                        self.remaining_terms.append(choice_value)

    def nav_to_first_term(self):
        search_btn = self.dc.html.find('input', {'id': 'pg0_V_btnSearch'})
        action, payload = self.dc.prepare_payload(nav_element=search_btn)
        post_url = self.dc.BASE_URL + action
        self.dc.http_post(post_url, data=payload)

    def find_rows_to_parse(self):
        """ Returns a list of HTML elements of rows this thread is responsible for. """

        row_index = 0
        thread_num = self.thread_num
        num_threads = self.num_threads
        return_value = []

        # find the table that contains the rows
        table = self.dc.html.find('tbody', {'class': 'gbody'})
        if table is None:
            raise errors.MissingElementError('Table element not found.')

        # find rows of the table
        table_rows = table.find_all('tr')

        # determine which rows we are responsible for
        for table_row in table_rows:

            # MyGCC includes hidden rows between each course displayed in the
            #   table. These rows are irrelevant and need to be skipped. This
            #   also checks whether or not the task has been manually aborted.
            if 'subItem' in table_row.get('class', ''):
                continue

            # determines if this thread is responsible for this row index
            should_handle = row_index % num_threads == thread_num
            if should_handle:
                return_value.append(table_row)
            row_index += 1

        return return_value

    def try_nav_next_page(self):
        navigator = self.dc.html.find('div', {'class': 'letterNavigator'})
        if navigator is not None:
            for nav_link in navigator.find_all('a')[::-1]:
                if nav_link.text == 'Next page -->':
                    action, payload = self.dc.prepare_payload(nav_element=nav_link)
                    post_url = self.dc.BASE_URL + action
                    self.dc.http_post(post_url, data=payload)
                    return True
        return False

    def try_nav_next_term(self):
        if self.remaining_terms:

            # navigate to next term
            next_term = self.remaining_terms.pop(0)
            search_btn = self.dc.html.find('input', {'id': 'pg0_V_btnSearch'})
            action, payload = self.dc.prepare_payload(nav_element=search_btn)
            payload['pg0$V$ddlTerm'] = next_term
            post_url = self.dc.BASE_URL + action
            self.dc.http_post(post_url, data=payload)

            # navigate to first page
            navigator = self.dc.html.find('div', {'class': 'letterNavigator'})
            if navigator is not None:
                nav_links = navigator.find_all('a')
                if len(nav_links) > 1 and nav_links[0].text == '<-- Previous page':
                    nav_element = nav_links[1]
                    action, payload = self.dc.prepare_payload(nav_element=nav_element)
                    post_url = self.dc.BASE_URL + action
                    self.dc.http_post(post_url, data=payload)

            return True
        return False

    def course_row_to_course(self, row):

        # find the navigation element
        nav_element = row.find('a')
        if nav_element is None:
            raise errors.MissingElementError('Course row navigation element missing.')

        # navigate to the course overview page
        action, payload = self.dc.prepare_payload(nav_element=nav_element)
        post_url = self.dc.BASE_URL + action
        self.dc.http_post(post_url, data=payload)

        # course code with section letters removed
        course_code = ' '.join(nav_element.text.strip().split(' ')[:2])

        # fetch data from this page
        details = self.dc.html.find('div', {'id': 'pg0_V_divCourseDetails'})

        if details is None:  # abort course parsing if the details element is missing
            self.nav_to_courses_from_course()  # ensure we return to the courses list
            raise errors.MissingElementError(f'details element could not be found for {course_code}')

        # fetch course title
        title_elem = details.find('b')
        if title_elem is None:  # abort course parsing if the title element is missing
            self.nav_to_courses_from_course()   # ensure we return to the courses list
            raise errors.MissingElementError(f'title element missing for {course_code}')
        course_title = title_elem.text.split('(', 1)[0].strip()

        # fetch course term
        term_elem = details.find('span', {'id': 'pg0_V_lblTermDescValue'})
        if term_elem is None:  # abort course parsing if the term element is missing
            self.nav_to_courses_from_course()   # ensure we return to the courses list
            raise errors.MissingElementError(f'term element missing for {course_code}')
        course_term = term_elem.text.strip().strip(',')

        # fetch course hours
        cred_elem = details.find('span', {'id': 'pg0_V_lblCreditHoursValue'})
        if cred_elem is None:  # abort course parsing if the credit element is missing
            self.nav_to_courses_from_course()   # ensure we return to the courses list
            raise errors.MissingElementError(f'credit element missing for {course_code}')
        course_credits = float(cred_elem.text.strip())

        # fetch course requisites
        course_requisites = []
        prereqlink = self.dc.html.find('a', {'id': 'pg0_V_lnkbCourseRequisites'})
        if prereqlink is not None:

            # navigate to the course requisites page
            action, payload = self.dc.prepare_payload(nav_element=prereqlink)
            post_url = self.dc.BASE_URL + action
            self.dc.http_post(post_url, data=payload)
            course_requisites = self.parse_course_requisites()

            self.nav_to_courses_from_requisites()
        else:
            self.nav_to_courses_from_course()

        # construct course class from data
        course = Course(course_code, course_title, course_term, course_credits, course_requisites)
        return course

    def parse_course_requisites(self):
        pattern = re.compile(r'([A-Z]{2,5})([0-9]{2,4}[A-Z]*)')

        def parse_req_type(_req_type: str) -> str:
            if _req_type.startswith('Prerequisite'):
                return 'prerequisite'
            if _req_type.startswith('Corequisite'):
                return 'corequisite'
            return 'other'

        def parse_req_name(_req_name: str) -> str:
            first_word = _req_name.split(' ', 1)[0]
            match = pattern.match(first_word)
            if match:
                first, second = match.groups()
                return first + ' ' + second
            return first_word

        requisites = {}
        table = self.dc.html.find('tbody', {'class': 'gbody'})
        if table is not None:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) != 5:
                    continue
                _, _, rgroup, rtype, rname = tuple(cells)
                rgroup_val = rgroup.text.strip()
                rtype_val = rtype.text.strip()
                rname_val = rname.text.strip()

                if rgroup_val != '':
                    try:
                        group_num = int(rgroup_val)
                        if group_num not in requisites:
                            requisites[group_num] = []
                        requisites[group_num].append((parse_req_type(rtype_val), parse_req_name(rname_val)))
                    except ValueError:
                        print('group number could not be converted to an int')
        return [v for _, v in requisites.items()]

    def nav_to_courses_from_course(self):
        """ Navigates back to the course list from a course overview page. """

        back_btn = self.dc.html.find('a', {'id': 'pg0_V_lnkBack'})
        action, payload = self.dc.prepare_payload(nav_element=back_btn)
        post_url = self.dc.BASE_URL + action
        self.dc.http_post(post_url, data=payload)

    def nav_to_courses_from_requisites(self):
        """ Navigates back to the course list from a course requisite page. """

        breadcrumbs = self.dc.html.find('span', {'id': 'portlet-breadcrumbs'})
        if breadcrumbs is None:
            raise Exception('failed to navigate to courses from requisite page')
        for bread in breadcrumbs.find_all('a'):
            if bread.text == 'Results':
                action, payload = self.dc.prepare_payload(nav_element=bread)
                post_url = self.dc.BASE_URL + action
                self.dc.http_post(post_url, data=payload)
                break


class AsyncCourseScraper(AsyncScraperManager):

    def __init__(self, username, password, callback):
        super().__init__(username, password, AsyncCourseScraperSession, callback)
