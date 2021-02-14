import gccutils.errors as errors
from bs4 import BeautifulSoup
import requests
import getpass


class ScraperUtils:
    BASE_URL = 'https://my.gcc.edu'

    def __init__(self):
        self.session = requests.Session()
        self.response = None
        self.html = None

    def http_get(self, url, check_errors=True, **kwargs):
        self.response = self.session.get(url, **kwargs)
        self.refresh_html()
        if check_errors:
            self.check_for_error_message()

    def http_post(self, url, check_errors=True, **kwargs):
        self.response = self.session.post(url, **kwargs)
        self.refresh_html()
        if check_errors:
            self.check_for_error_message()

    def perform_login(self, username=None, password=None):
        self.http_get(self.BASE_URL)
        login_btn = self.html.find('input', {'type': 'submit', 'id': 'siteNavBar_btnLogin'})
        action, payload = self.prepare_payload(nav_element=login_btn)
        payload['userName'] = username or input('Username: ')
        payload['password'] = password or getpass.getpass()
        self.http_post(self.BASE_URL + action, data=payload)

    def refresh_html(self):
        if self.response is not None:
            self.html = BeautifulSoup(self.response.text, features='html.parser')
        else:
            self.html = None

    def to_url(self, path):
        """ Returns the url with the appropriate base url attached. """
        if path.startswith(self.BASE_URL):
            return path
        path = '/' + path.lstrip('/')
        return self.BASE_URL + path

    def ensure_screen(self, url):
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

        is_logged_in = html.find('a', {'id': 'logout'}) is not None
        title_bar = html.find('div', {'id': 'PageBar_pageTitle'})
        if title_bar is not None:
            alert_container = title_bar.find('div', {'class': 'alert-container'})
        else:
            alert_container = None
        is_alert_present = alert_container is not None

        if is_alert_present:
            alert_text = alert_container.get_text()
            missing_permissions = 'require you to be logged in' in alert_text
            redirect_error = 'attempted to navigate using your browser' in alert_text

            if not is_logged_in:
                raise errors.NotLoggedInError('You must be logged in to view this page.')
            elif missing_permissions:
                raise errors.UnauthorizedError('You are not authorized to view this page.')
            elif redirect_error:
                raise errors.PageRedirectError('Page was redirected due to improper navigation.')
            else:
                raise errors.PageError(f'An unknown page error occurred: {alert_text}')