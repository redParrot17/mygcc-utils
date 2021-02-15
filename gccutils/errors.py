
class ScraperError(Exception):
    """ Common base class for all web-scraping exceptions. """


class MissingElementError(ScraperError):
    """ HTML element not found. """


class UnexpectedElementPropertyError(ScraperError):
    """ HTML element differs from expectation. """


class PageError(ScraperError):
    """ Caused when an action resulted in an alert container. """


class LoginError(PageError):
    """ Caused when improper credentials were used to perform login. """


class PageRedirectError(PageError):
    """ Caused when navigating without proper view-state headers. """


class UnauthorizedError(PageError):
    """ Caused when navigating to a page without having access to it. """


class NotLoggedInError(UnauthorizedError):
    """ Caused when navigating to a restricted page without being logged in. """
