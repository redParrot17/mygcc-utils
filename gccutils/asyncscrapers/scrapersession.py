from gccutils.scraper_utils import ScraperUtils
import multiprocessing
import threading


class AsyncScraperSession(threading.Thread):

    def __init__(self, username, password, callback, thread_num, num_threads):
        threading.Thread.__init__(self)
        self.callback = callback
        self.thread_num = thread_num
        self.num_threads = num_threads
        self.dc = ScraperUtils()
        self.dc.perform_login(username, password)
        self.aborted = False

    def abort(self):
        """
        Asks the thread to stop running as soon as it is convenient.

        This does not guarantee that the thread will stop!
        """
        self.aborted = True

    def run(self):
        raise NotImplementedError


class AsyncScraperManager:

    def __init__(self, username, password, session, callback):
        self.__username = username
        self.__password = password
        self.__callback = callback
        self.__sessions = []
        self.__session = session
        self.__cpu_count = multiprocessing.cpu_count()
        self.reset()

    def is_running(self):
        for session in self.__sessions:
            if session.is_alive():
                return True
        return False

    def start(self):
        if self.is_running():
            raise RuntimeError('scrapers are already running')
        for session in self.__sessions:
            session.start()

    def stop(self):
        for session in self.__sessions:
            session.abort()

    def reset(self):
        self.stop()
        cpu_count = self.__cpu_count
        username = self.__username
        password = self.__password
        callback = self.__callback
        session = self.__session
        self.__sessions = [session(username, password, callback, i, cpu_count)
                           for i in range(cpu_count)]
