from gccutils.scraper_utils import ScraperUtils
import gccutils.errors as errors
import traceback


__all__ = ('AdviseeScraper',)


class AdviseeOverviewParser:
    """A helper class for parsing data from an advisee overview page."""

    def __init__(self, html_soup):
        """Constructor

        :param html_soup: the BeautifulSoup instance for the page
        """
        self.html = html_soup

    def parse(self):
        """Parses the HTML for important data relevant to the student.

        :return: dictionary containing the data from the page
        """
        values = {}

        table = self.get_table('pg0_V_tblSummaryLeft')

        for row in table.find_all('tr'):
            try:
                name, value = self.fetch_value(row)
                values[name] = value
            except errors.ScraperError:
                traceback.print_exc()

        table = self.get_table('pg0_V_tblSummaryRight')

        for row in table.find_all('tr'):
            try:
                name, value = self.fetch_value(row)
                values[name] = value
            except errors.ScraperError:
                traceback.print_exc()

        return values

    def get_table(self, table_id):
        """Finds and returns a table with the specified element id.

        :param table_id: the unique identifier of the table to find
        :return: the table element if found
        :raises MissingElementError: if the table could not be found
        """

        table = self.html.find('table', {'id': table_id})
        if table is None:
            raise errors.MissingElementError(f'Table {table_id} not found.')
        return table

    @staticmethod
    def fetch_value(entry):
        """Returns the text value of an element's inner <td> child.

        :param entry: a table element with an inner <td> child
        :return: the value associated with the element's inner <td> child
        :raises MissingElementError: if the element does not contain a <td> tag
        """

        name_element = entry.find('th')
        value_element = entry.find('td')

        if name_element is None:  # raise an exception if no name element was found
            raise errors.MissingElementError('Overview table row contains no name element <th></th>')

        if value_element is None:  # raise an exception if no value element was found
            raise errors.MissingElementError('Overview table row contains no value element <td></td>')

        name = name_element.get_text(strip=True)\
            .replace(u'\xa0', '').lower()\
            .replace(' ', '_').replace(':', '')
        value = value_element.get_text(separator=' ', strip=True)\
            .replace(u'\xa0', '')

        return name, value


class AdviseeScraper:
    STUDENT_TO_ROSTER_EVENT_TARGET = 'sb00bc534cd-3ee3-4fc5-be95-b3850319f0b8'

    def __init__(self, username, password):
        self.scraper = ScraperUtils()
        self.__username = username
        self.__password = password

    def fetch(self):
        # navigate to the first roster page
        self.scraper.perform_login(
            self.__username, self.__password)
        self.navigate_to_roster()

        new_page = True
        all_students = []

        while new_page:
            try:
                student_rows = self.get_all_student_rows()
                for student_row in student_rows:
                    student = self.build_student_dict(*student_row)
                    if student is not None:
                        all_students.append(student)
                        print(student)
            except errors.ScraperError:
                traceback.print_exc()

            # navigate to the next page
            if not self.try_nav_to_next_page():
                new_page = False

        return all_students

    def navigate_to_roster(self):
        scraper = self.scraper

        # navigate to advising tab
        scraper.http_get(scraper.to_url('/ICS/Advising'))

        # create the payload to be sent
        search_btn = scraper.html.find('input', id='pg0_V_btnSearch')
        self.perform_navigation(search_btn)

    def get_all_student_rows(self):
        scraper = self.scraper

        table = scraper.html.find('tbody', class_='gbody')
        if table is None:
            raise errors.MissingElementError('Roster table is missing.')

        rows = table.find_all('tr')
        row_index = 0
        results = []

        for row in rows:
            try:
                email, name, user_id, nav_element = self.parse_table_row(row, row_index)
                results.append((email, name, user_id, nav_element))
            except errors.ScraperError:
                traceback.print_exc()
            row_index += 1

        return results

    @staticmethod
    def parse_table_row(row, index):
        expected_column_count = 6
        columns = row.find_all('td')

        if len(columns) != expected_column_count:
            raise errors.UnexpectedElementPropertyError(
                f'Expected roster row[{index}] to have {expected_column_count} '
                f'columns but found {len(columns)}.')

        _, email_col, name_col, id_col, _, _ = columns

        # get email
        email = email_col.find('input', type='image')
        if email is None:
            raise errors.MissingElementError(f'Roster row[{index}] has no email column.')
        email = email.get('title')

        # get name
        name = name_col.find('a')
        if name is None:
            raise errors.MissingElementError(f'Roster row[{index}] has no name column.')
        name = name.get_text()

        # get student id
        user_id = id_col.get_text()
        if not user_id:
            raise errors.UnexpectedElementPropertyError(
                f'Roster row[{index}] has no value associated with the user id column.')

        # get href
        nav_element = name_col.find('a')
        if nav_element is None:
            raise errors.MissingElementError(f'Roster row[{index}] has no navigation element.')

        return email, name, user_id, nav_element

    def build_student_dict(self, email, name, user_id, nav_element):
        # if any navigation fails here, we cannot recover without restarting
        self.perform_navigation(nav_element)  # navigate to student overview

        try:

            parser = AdviseeOverviewParser(self.scraper.html)
            overview = parser.parse()
            overview['email'] = email
            overview['name'] = name
            overview['user_id'] = user_id

            return overview

        except errors.ScraperError:
            traceback.print_exc()
        finally:
            # The __EVENTTARGET postback identifier is hardcoded because MyGCC is a jerk.
            # We cannot reliably obtain the navigation element to get back to the roster
            #   since MyGCC will randomly not include it within the breadcrumb trail.
            self.perform_navigation(None, self.STUDENT_TO_ROSTER_EVENT_TARGET)

    def try_nav_to_next_page(self):
        next_page = self.get_next_page_element()
        if next_page is None:
            return False
        self.perform_navigation(next_page)

    def get_next_page_element(self):
        # find the navigation container
        navigator = self.scraper.html.find('div', class_='letterNavigator')

        # ensure the list exists
        if navigator is not None:

            # find all navigation elements within the container
            nav_links = navigator.find_all(recursive=False)

            # if the last one is "next page" then return it
            if nav_links and nav_links[-1].get_text() == 'Next page -->':
                return nav_links[-1]

    def perform_navigation(self, nav_element, event_target=None):
        scraper = self.scraper
        action, payload = scraper.prepare_payload(nav_element=nav_element)

        if isinstance(event_target, str):
            payload['__EVENTTARGET'] = event_target

        scraper.http_post(scraper.to_url(action), data=payload)
