import gccutils.errors as errors
from bs4 import BeautifulSoup
import requests
import getpass


class ScraperUtils:
    """A utility class for navigating through https://my.gcc.edu/

    MyGCC is a pain in the butt to programmatically navigate through due to
    the way it handles state via hidden fields. This class abstracts many
    of those messy details away to allow for easier navigation via requests.
    """

    BASE_URL = 'https://my.gcc.edu'

    def __init__(self):
        self.session = requests.Session()
        self.response = None
        self.html = None

    def http_get(self, url, check_errors=True, **kwargs):
        """Executes an HTTP GET request to the specified url.

        The response of the request gets saved to the `response` attribute.

        :param url: the url to send the GET request to
        :param check_errors: whether or not to check if problems occurred, default True
        :param kwargs: optional arguments to include with the request
        """

        self.response = self.session.get(url, **kwargs)
        self.refresh_html()  # allows for immediate self.html reference
        if check_errors:     # throws an exception if an error occurred
            self.check_for_error_message()

    def http_post(self, url, check_errors=True, **kwargs):
        """Executes an HTTP POST request to the specified url.

        The response of the request gets saved to the `response` attribute.

        :param url: the url to send the POST request to
        :param check_errors: whether or not to check if problems occurred, default True
        :param kwargs: optional arguments to include with the request
        """

        self.response = self.session.post(url, **kwargs)
        self.refresh_html()  # allows for immediate self.html reference
        if check_errors:     # throws an exception if an error occurred
            self.check_for_error_message()

    def perform_login(self, username=None, password=None):
        """Attempts to login to https://my.gcc.edu/ using the provided credentials.

        If no credentials are provided, they will be requested via a command line prompt.

        :param username: the username to be used for login
        :param password: the password to be used for login
        :raises LoginError: if the supplied credentials are invalid
        """

        self.http_get(self.BASE_URL)  # the base url contains the login fields
        login_btn = self.html.find('input', {'type': 'submit', 'id': 'siteNavBar_btnLogin'})
        if login_btn is not None:
            action, payload = self.prepare_payload(nav_element=login_btn)
            payload['userName'] = username or input('Username: ')
            payload['password'] = password or getpass.getpass()
            self.http_post(self.BASE_URL + action, data=payload)

    def refresh_html(self):
        """ Rebuilds the BeautifulSoup structure of the current page. """

        if self.response is not None:
            raw_html_text = self.response.text
            self.html = BeautifulSoup(raw_html_text, features='html.parser')

        else:  # for when the scraper has not been used yet
            self.html = None

    def to_url(self, path):
        """Ensures the base url is prefixed to the specified path.

        :param path: the route of the url
        :return: the base url prefixed string
        """

        # the url might already be formatted properly
        if path.startswith(self.BASE_URL):
            return path

        # append the path to the base url
        path = '/' + path.lstrip('/')
        return self.BASE_URL + path

    def ensure_screen(self, url):
        """Navigates to the specified url via GET request if we are not already there.

        :param url: the desired url to navigate to
        """

        if self.response is None or self.response.url != url:
            self.http_get(url)

    def prepare_payload(self, html=None, nav_element=None):
        """
        Builds a payload for sending post requests from the current page.

        :param html: a BeautifulSoup representation of the current page
        :param nav_element: an optional navigation element either submit or containing postback
        :return: post url, a dictionary containing the payload keys and values
        """

        if html is None:
            html = self.html

        if html is None:
            return '', {}

        # this is the top level form element
        form = html.find('form', {'name': 'MAINFORM'})

        # return a default value if no form exists
        if form is None:
            return '', {}

        # the action element defines where the post request gets sent to
        action = form.get('action', '')
        payload = {}

        # parse out all the select tags within the form
        select_tags = form.find_all('select')
        for select_tag in select_tags:
            selected_option = select_tag.find('option', {'selected': 'selected'})

            # if nothing is selected then default to the first option
            if selected_option is None:
                selected_options = select_tag.find_all('option')
                if len(selected_options) > 0:
                    selected_option = selected_options[0]

            # add the selection to the payload if it exists
            if selected_option is not None:
                payload[select_tag['name']] = selected_option.get('value', '')

        # parse out all the relevant input tags within the form
        input_tags = form.find_all('input')
        for input_tag in input_tags:
            input_name = input_tag['name']
            input_value = input_tag.get('value', '')
            input_type = input_tag.get('type', 'text')

            # checkboxes and radios only are included when selected
            if input_type in ('checkbox', 'radio'):
                if input_tag.get('checked'):
                    payload[input_name] = input_value

            # ignore image and submit types
            elif input_type in ('image', 'submit'):
                pass  # ignore images
            else:
                payload[input_name] = input_value

        if nav_element is not None:
            # include the optional parameter if it is of type submit
            if nav_element.get('type') == 'submit':
                payload[nav_element['name']] = nav_element.get('value', '')

            else:
                href = nav_element.get('href')
                if href is not None and '__doPostBack' in href:
                    # javascript:__doPostBack('eventTargetValue','eventArgumentValue')
                    href = href.replace('javascript:__doPostBack(', '')
                    href = href.replace(')', '')
                    href = href.replace("'", '')
                    href_elements = href.split(',', 1)
                    if len(href_elements) == 2:
                        payload['__EVENTTARGET'] = href_elements[0]
                        payload['__EVENTARGUMENT'] = href_elements[1]

        return action, payload

    def check_for_error_message(self, html=None):
        """ Checks if you are unauthorized, not logged in, or were redirected. """

        if html is None:
            html = self.html

        if html is None:
            return

        raw_html_text = str(html)
        is_logged_in = html.find('a', {'id': 'logout'}) is not None
        redirect_error = "You have been redirected to this page because you attempted to navigate" in raw_html_text
        unauthorized_error = "require you to be logged in" in raw_html_text

        if redirect_error:
            raise errors.PageRedirectError('Page was redirected due to improper navigation.')
        elif not is_logged_in and unauthorized_error:
            raise errors.NotLoggedInError('You must be logged in to view this page.')
        elif unauthorized_error:
            raise errors.UnauthorizedError('You are not authorized to view this page.')
        else:
            element = html.find('span', {'id': 'CP_V_lblLoginError'})
            if element is not None:
                raise errors.LoginError(element.get_text())
