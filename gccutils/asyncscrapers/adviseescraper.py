from gccutils.asyncscrapers.scrapersession import AsyncScraperManager, AsyncScraperSession
import gccutils.errors as errors
import time


class Advisee:
    """A simple dataclass for keeping track of information about an adviser's advisee."""

    def __init__(self, **values):
        """Constructor

        :param values: a dictionary of values

            * user_id:         the student's identification number
            * email:           their grove city college email address
            * name:            first and last name
            * classification:  what year they are (Junior, Senior, etc)
            * enrolled_date:   the MM/DD/YYYY they enrolled at the college
            * planned_grad:    the MM/DD/YYYY they are predicted to graduate
            * max_credits:     the most credits they can take per semester
            * academic_status: if they are a Full-Time or Part-Time student
            * degree:          "Bachelor of Science" for example
            * major:           the title of the student's major
        """

        self.user_id = values.pop('user_id')
        self.email = values.pop('email')
        self.name = values.pop('name')

        self.classification = values.pop('classification')
        self.enrolled_date = values.pop('enrolled_date')
        self.planned_grad = values.pop('planned_grad')
        self.max_credits = values.pop('max_credits')

        self.academic_status = values.pop('academic_status')
        self.degree = values.pop('degree')
        self.major = values.pop('major')


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

            * classification
            * enrolled_date
            * planned_grad
            * max_credits
            * academic_status
            * degree
            * major
        """

        table = self.get_table('pg0_V_tblSummaryLeft')
        rows = self.get_table_rows(table, 'left', 5)
        classification = self.fetch_value(rows[0])
        enrolled_date = self.fetch_value(rows[1])
        planned_grad = self.fetch_value(rows[2])
        max_credits = self.fetch_value(rows[3])

        table = self.get_table('pg0_V_tblSummaryRight')
        rows = self.get_table_rows(table, 'right', 3)
        academic_status = self.fetch_value(rows[0])
        degree = self.fetch_value(rows[1])
        major = self.fetch_value(rows[2])

        return {
            'classification': classification,
            'enrolled_date': enrolled_date,
            'planned_grad': planned_grad,
            'max_credits': max_credits,
            'academic_status': academic_status,
            'degree': degree,
            'major': major
        }

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
    def get_table_rows(table, table_name, expected_row_count):
        """Fetches the rows from a table element and ensures proper row count.

        :param table: the table element to get the rows of
        :param table_name: the name of the table for error handling
        :param expected_row_count: the expected number of rows
        :return: the rows belonging to the table
        :raises UnexpectedElementPropertyError: if the number of rows differs from expectation
        """

        table_rows = table.find_all('tr')
        row_count = len(table_rows)

        # ensure the number of rows matches expectations
        if row_count != expected_row_count:
            raise errors.UnexpectedElementPropertyError(
                f'Expected {table_name} table to have {expected_row_count} '
                f'rows but found {row_count} instead.')

        return table_rows

    @staticmethod
    def fetch_value(entry):
        """Returns the text value of an element's inner <td> child.

        :param entry: a table element with an inner <td> child
        :return: the value associated with the element's inner <td> child
        :raises MissingElementError: if the element does not contain a <td> tag
        """

        child = entry.find('td')

        if child is None:  # raise an exception if the value could not be found
            raise errors.MissingElementError('entry contains no element <td></td>')

        return child.text


class AsyncAdviseeScraperSession(AsyncScraperSession):
    """Web-scraping thread for obtaining adviser's advisee information."""

    ADVISEEURL = 'https://my.gcc.edu/ICS/Advising/'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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

        print(f'advisee scraper thread [{thread_num}|{num_threads}] starting')

        # perform initial setup
        self.nav_to_search()
        self.nav_to_advisee_list()

        # for each page of advisees
        while not self.aborted:

            table_rows = self.find_rows_to_parse()

            for table_row in table_rows:
                if self.aborted: continue

                try:
                    # build advisee object from the row data
                    advisee = self.table_row_to_advisee(table_row)

                    if advisee is not None:
                        callback(advisee)
                except Exception as e:
                    # handle errors that occur during advisee creation or the callback
                    print(f'advisee scraper thread [{thread_num}|{num_threads}] exception: {e}')

            # navigate to the next page
            if not self.try_nav_next_page():
                break  # stop if this was the last page

        runtime = int(time.time() - start_time)
        print(f'advisee scraper thread [{thread_num}|{num_threads}] stopping after {runtime} seconds')

    def nav_to_search(self):
        """
        Navigates to the advisee search page.

        This is a necessary first step prior to accessing any advisee.
        """
        self.dc.http_get(self.ADVISEEURL)

    def nav_to_advisee_list(self):
        """ Navigates to the list of advisees. """

        # TODO: verify that this is in fact correct
        search_btn = self.dc.html.find('input', {'id': 'pg0_V_btnSearch'})

        action, payload = self.dc.prepare_payload(nav_element=search_btn)
        post_url = self.dc.BASE_URL + action

        # payload = {
        #     'pg0$V$ddlStatus': 'ALL',
        #     'pg0$V$txtID': '',
        #     'pg0$V$txtLName': '',
        #     'pg0$V$ddlDivision': 'ALLDIVS',
        #     'pg0$V$ddlTerm': '2020;30',
        #     'pg0$V$btnSearch': 'Search',
        #     'pg2$V$CardLayoutControl$cardSetsRepeater$ctl00$SetSortOrderHiddenField': '',
        #     'pg2$V$CardLayoutControl$cardSetsRepeater$ctl00$hiddenFieldForSet': '',
        #     'pg4$V$CardLayoutControl$cardSetsRepeater$ctl00$SetSortOrderHiddenField': '',
        #     'pg4$V$CardLayoutControl$cardSetsRepeater$ctl00$hiddenFieldForSet': '',
        #     'pg4$V$CardLayoutControl$cardSetsRepeater$ctl01$SetSortOrderHiddenField': '',
        #     'pg4$V$CardLayoutControl$cardSetsRepeater$ctl01$hiddenFieldForSet': ''}
        # payload = self.dc.prepare_payload(payload)

        self.dc.http_post(post_url, data=payload)

    def try_nav_next_page(self):
        """ Navigates to the next page of advisees. """

        navigator = self.dc.html.find('div', {'class': 'letterNavigator'})
        if navigator is not None:
            for nav_element in navigator.find_all('a')[::-1]:
                if nav_element.text == 'Next page -->':
                    action, payload = self.dc.prepare_payload(nav_element=nav_element)
                    post_url = self.dc.BASE_URL + action

                    # payload = {
                    #     '__PORTLET': 'pg0$V$ltrNav',
                    #     'pg0$V$ddlStatus': 'ALL',
                    #     'pg0$V$txtID': '',
                    #     'pg0$V$txtLName': '',
                    #     'pg0$V$ddlDivision': 'ALLDIVS',
                    #     'pg0$V$ddlTerm': '2020;30'}
                    # payload = self.dc.prepare_payload(payload, postback)

                    self.dc.http_post(post_url, data=payload)
                    return True
        return False

    def find_rows_to_parse(self):
        """ Returns a list of HTML elements of rows this thread is responsible for. """

        row_index = 0
        thread_num = self.thread_num
        num_threads = self.num_threads
        return_value = []

        # find the table that contains the rows
        table = self.dc.html.find('tbody', {'class': 'gbody'})
        if table is None:
            raise errors.MissingElementError('table element not found')

        # find rows of the table
        table_rows = table.find_all('tr')

        # determine which rows we are responsible for
        for table_row in table_rows:
            should_handle = row_index % num_threads == thread_num
            if should_handle:
                return_value.append(table_row)
            row_index += 1

        return return_value

    def table_row_to_advisee(self, table_row):
        """ Converts a table row into an advisee object. """

        # fetch values from the table row
        email, name, postback, user_id = self.parse_table_row(table_row)

        self.nav_to_overview(postback)

        try:
            # try parsing the values on the overview page
            values = AdviseeOverviewParser(self.dc.html).parse()
            values['email'] = email
            values['name'] = name
            values['user_id'] = user_id

            # construct the object
            return Advisee(**values)
        finally:
            # navigate back from the overview page
            self.nav_back_from_overview()

    def nav_to_overview(self, nav_element):
        """ Navigates to a specific advisee overview page. """
        # build the payload to navigate to the overview page
        # payload = {
        #     '__PORTLET': 'pg0$V$ltrNav',
        #     'pg0$V$ddlStatus': 'ALL',
        #     'pg0$V$txtID': '',
        #     'pg0$V$txtLName': '',
        #     'pg0$V$ddlDivision': 'ALLDIVS',
        #     'pg0$V$ddlTerm': '2020;30'}  # TODO: fetch this
        action, payload = self.dc.prepare_payload(nav_element=nav_element)
        post_url = self.dc.BASE_URL + action

        # navigate to the overview page
        self.dc.http_post(post_url, data=payload)

    @staticmethod
    def parse_table_row(table_row):
        """ Extracts advisee data from the table row. """

        # find all columns of this table row
        row_columns = table_row.find_all('td')

        # ensure all columns are accounted for
        num_row_columns = len(row_columns)
        if num_row_columns != 6:
            raise errors.UnexpectedElementPropertyError(
                f'expected 6 columns in table row - found {num_row_columns}')

        # break the column elements into their separate parts
        _, email_col, link_col, id_col, _, _ = row_columns

        # parse out the student's email address
        email_element = email_col.find('input', {'type': 'image'})
        if email_element is None:
            raise errors.MissingElementError('email column element not found')

        email_address = email_element.get('title')
        if email_address is None:
            raise errors.UnexpectedElementPropertyError(
                "expected email column element to have attribute 'title'")

        # parse out postback attribute for student's overview
        postback_element = link_col.find('a')
        if postback_element is None:
            raise errors.MissingElementError('postback column element not found')

        # parse out student's name from postback_element
        name = postback_element.text
        if not name:
            raise errors.UnexpectedElementPropertyError(
                'expected postback column element to have inner text')

        # parse out user id
        user_id = id_col.text
        if not user_id:
            raise errors.UnexpectedElementPropertyError(
                'expected user id column element to have inner text')

        return email_address, name, postback_element, user_id

    def nav_back_from_overview(self):
        """ Navigates back to the advisee list from an overview page. """

        # find the postback text for the payload
        breadcrumbs = self.dc.html.find('span', {'id': 'portlet-breadcrumbs'})
        if breadcrumbs is None:
            raise errors.MissingElementError('Span portlet-breadcrumbs not found.')

        postback_element = breadcrumbs.find('a')
        if postback_element is None:
            raise errors.MissingElementError('Span has no child <a></a>')

        # construct payload
        # payload = {'__PORTLET': 'pg0$V$ltrNav'}
        action, payload = self.dc.prepare_payload(nav_element=postback_element)
        post_url = self.dc.BASE_URL + action

        # navigate back from the overview page
        self.dc.http_post(post_url, data=payload)


class AsyncAdviseeScraper(AsyncScraperManager):

    def __init__(self, username, password, callback):
        super().__init__(username, password, AsyncAdviseeScraperSession, callback)
