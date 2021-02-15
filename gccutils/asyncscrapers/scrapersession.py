from gccutils.scraper_utils import ScraperUtils
import multiprocessing
import threading


class AsyncScraperSession(threading.Thread):
    """ The base class for implementing a threaded web-scraper. """

    def __init__(self, username, password, callback, thread_num, num_threads):
        """Constructor

        :param username: the username to be used for logging in
        :param password: the password to be used for logging in
        :param callback: the callback to send the results to
        :param thread_num: the identifier for this thread
        :param num_threads: how many threads there are
        """

        threading.Thread.__init__(self)
        self.callback = callback
        self.thread_num = thread_num
        self.num_threads = num_threads
        self.dc = ScraperUtils()
        self.dc.perform_login(username, password)
        self.aborted = False

    def abort(self):
        """Asks the thread to stop running as soon as it is convenient.

        This does not guarantee that the thread will stop!
        """
        self.aborted = True

    def run(self):
        """The primary method of this thread.

        Do not manually call this method. Use `AsyncScraperSession#start()` instead.

        :raises NotImplementedError: if not overridden
        """
        raise NotImplementedError


class AsyncScraperManager:
    """The base class for managing threaded `AsyncScraperSession`'s.

    When run, spawns a thread team equal to the number of cpu cores available.
    """

    def __init__(self, username, password, session, callback):
        """Constructor

        :param username: the username to be used for logging into mygcc
        :param password: the password to be used for logging into mygcc
        :param session:  the `AsyncScraperSession` class to be used
        :param callback: a callback for the result of the scraper to be sent to
        """

        self.__username = username
        self.__password = password
        self.__callback = callback
        self.__sessions = []
        self.__session = session
        self.__cpu_count = multiprocessing.cpu_count()
        self.reset()  # creates the initial thread team

    def is_running(self):
        """ Returns whether or not the thread team is currently running. """

        for session in self.__sessions:
            if session.is_alive():
                return True
        return False

    def start(self):
        """Starts the thread team.

        :raises RuntimeError: if already running
        """

        # make sure the threads are not already running
        if self.is_running():
            raise RuntimeError('scrapers are already running')

        for session in self.__sessions:
            session.start()

    def stop(self):
        """ Sends an abort request to each of the threads. """

        for session in self.__sessions:
            session.abort()

    def reset(self):
        """ Aborts any running threads and resets the thread team to be rerun. """

        # abort any currently running threads
        # this has no effect if the threads are hanging
        self.stop()

        # localizing the variables for quicker lookup
        cpu_count = self.__cpu_count
        username = self.__username
        password = self.__password
        callback = self.__callback
        session = self.__session

        # creating the thread team
        self.__sessions = [session(username, password, callback, i, cpu_count)
                           for i in range(cpu_count)]
