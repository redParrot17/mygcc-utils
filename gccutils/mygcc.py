from gccutils.scraper_utils import ScraperUtils
from gccutils.asyncscrapers.coursescraper import AsyncCourseScraper
from gccutils.asyncscrapers.adviseescraper import AsyncAdviseeScraper
import gccutils.errors as errors


class ProfileInformation:
    PROFILEURL = 'https://my.gcc.edu/ICS/'

    def __init__(self, data_collection: ScraperUtils):
        self.dc = data_collection
        self._screen = None

        # About me
        self.__user_id = None
        self.__photo = None
        self.__name = None
        self.__birthday = None
        self.__gender = None
        self.__ethnicity = None
        self.__marital_status = None

        # Contact information
        # TODO: implement contact information properties

        # Academic information
        self.__major = None
        self.__minor = None
        self.__certification = None
        self.__concentration = None
        self.__degree_honor = None
        self.__course_of_study = None
        self.__classification = None
        self.__division = None
        self.__academic_status = None
        self.__enrolled_date = None
        self.__planned_grad = None
        self.__max_credits = None
        self.__ss_benefits = None
        self.__vet_benefits = None

    ### ABOUT ME ###

    @property
    def user_id(self):
        if self.__user_id is None:
            header = self._span_template('AboutMeView', 'CP_V_ViewHeader_SiteManagerLabel')
            self.__user_id = header.split('#')[-1]
        return self.__user_id

    @property
    def photo(self):
        if self.__photo is None:
            self._ensure_screen('AboutMeView')
            element = self.dc.html.find('span', dict(id='UploadedImage'))
            img_text = element.get('style') if element else ''
            self.__photo = self.dc.to_url(img_text.split("'")[1]) if img_text else ''
        return self.__photo

    @property
    def name(self):
        if self.__name is None:
            self._ensure_screen('AboutMeView')
            html = self.dc.html

            # get prefix
            prefix_elem = html.find('select', dict(id='CP_V_LegalPrefix'))
            if prefix_elem is not None:
                prefix_option = prefix_elem.find('option', dict(selected='selected'))
                prefix = prefix_option.text if prefix_option else ''
            else:
                prefix = ''

            # get first name
            fname_elem = html.find('input', dict(id='CP_V_LegalFirstName'))
            fname = fname_elem.get('value') if fname_elem else ''

            # get middle name
            mname_elem = html.find('input', dict(id='CP_V_LegalMiddleName'))
            mname = mname_elem.get('value') if mname_elem else ''

            # get last name
            lname_elem = html.find('input', dict(id='CP_V_LegalLastName'))
            lname = lname_elem.get('value') if lname_elem else ''

            # get suffix
            suffix_elem = html.find('select', dict(id='CP_V_LegalSuffix'))
            if suffix_elem is not None:
                suffix_option = suffix_elem.find('option', dict(selected='selected'))
                suffix = suffix_option.text if suffix_option else ''
            else:
                suffix = ''

            self.__name = {
                'prefix': prefix,
                'firstname': fname,
                'middlename': mname,
                'lastname': lname,
                'suffix': suffix}

        return self.__name

    @property
    def birthday(self):
        if self.__birthday is None:
            self.__birthday = self._span_template('AboutMeView', 'CP_V_StaticDateOfBirth')
        return self.__birthday

    @property
    def gender(self):
        if self.__gender is None:
            self.__gender = self._span_template('AboutMeView', 'CP_V_StaticGenderValue')
        return self.__gender

    @property
    def ethnicity(self):
        if self.__ethnicity is None:
            self.__ethnicity = self._span_template('AboutMeView', 'CP_V_StaticEthnicityValue')
        return self.__ethnicity

    @property
    def marital_status(self):
        if self.__marital_status is None:
            self.__marital_status = self._span_template('AboutMeView', 'CP_V_StaticMaritalStatus')
        return self.__marital_status

    ### CONTACT INFORMATION ###

    ### ACADEMIC INFORMATION ###

    @property
    def major(self):
        if self.__major is None:
            self.__major = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl00_InformationItemsRepeater_ctl00_Value')
        return self.__major

    @property
    def minor(self):
        if self.__minor is None:
            self.__minor = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl00_InformationItemsRepeater_ctl01_Value')
        return self.__minor

    @property
    def certification(self):
        if self.__certification is None:
            self.__certification = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl00_InformationItemsRepeater_ctl02_Value')
        return self.__certification

    @property
    def concentration(self):
        if self.__concentration is None:
            self.__concentration = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl00_InformationItemsRepeater_ctl03_Value')
        return self.__concentration

    @property
    def degree_honor(self):
        if self.__degree_honor is None:
            self.__degree_honor = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl00_InformationItemsRepeater_ctl04_Value')
        return self.__degree_honor

    @property
    def course_of_study(self):
        if self.__course_of_study is None:
            self.__course_of_study = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl01_InformationItemsRepeater_ctl00_Value')
        return self.__course_of_study

    @property
    def classification(self):
        if self.__classification is None:
            self.__classification = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl01_InformationItemsRepeater_ctl01_Value')
        return self.__classification

    @property
    def division(self):
        if self.__division is None:
            self.__division = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl01_InformationItemsRepeater_ctl02_Value')
        return self.__division

    @property
    def academic_status(self):
        if self.__academic_status is None:
            self.__academic_status = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl01_InformationItemsRepeater_ctl03_Value')
        return self.__academic_status

    @property
    def enrolled_date(self):
        if self.__enrolled_date is None:
            self.__enrolled_date = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl01_InformationItemsRepeater_ctl04_Value')
        return self.__enrolled_date

    @property
    def planned_graduation(self):
        if self.__planned_grad is None:
            self.__planned_grad = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl01_InformationItemsRepeater_ctl05_Value')
        return self.__planned_grad

    @property
    def max_credits(self):
        if self.__max_credits is None:
            value = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl01_InformationItemsRepeater_ctl06_Value')
            self.__max_credits = float(value) if value else 0.0
        return self.__max_credits

    @property
    def social_security_benefits(self):
        if self.__ss_benefits is None:
            self.__ss_benefits = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl02_InformationItemsRepeater_ctl00_Value')
        return self.__ss_benefits

    @property
    def veterans_benefits(self):
        if self.__vet_benefits is None:
            self.__vet_benefits = self._span_template('AcademicInformationView', 'CP_V_AcademicInformationCards_ctl00_AcademicInformationCard_InformationSetsRepeater_ctl02_InformationItemsRepeater_ctl01_Value')
        return self.__vet_benefits

    ## helper methods ##

    def _ensure_screen(self, screen):
        if self._screen != screen:
            self._screen = screen
            params = self._get_params(screen)
            self.dc.http_get(self.PROFILEURL, params=params)

    def _span_template(self, screen, elem_id):
        self._ensure_screen(screen)
        element = self.dc.html.find('span', dict(id=elem_id))
        return element.text if element else ''

    @staticmethod
    def _get_params(screen):
        return {
            'tool': 'myProfileSettings',
            'screen': screen,
            'screenType': 'next'}


class StudentInformation:
    STUDENTURL = 'https://my.gcc.edu/ICS/Student/'

    def __init__(self, data_collection: ScraperUtils):
        self.dc = data_collection
        self.__chapel = None

    @property
    def chapel(self):
        if self.__chapel is None:
            self.dc.ensure_screen(self.STUDENTURL)
            iframe = self.dc.html.find('iframe', dict(id='pg1_V_iframe'))
            chapel = {}
            if iframe is not None:
                self.dc.http_get(iframe['src'])
                table = self.dc.html.find('table', dict(id='grd'))
                if table is not None:
                    rows = table.find_all('tr')
                    if len(rows) == 2:
                        header_cells = rows[0].find_all('th')
                        data_cells = rows[1].find_all('td')
                        chapel = {
                            key.text.lower(): value.text
                            for key, value in
                            zip(header_cells, data_cells)}
                        for key in chapel.keys():
                            try:
                                chapel[key] = int(chapel[key])
                            except ValueError:
                                pass
            self.__chapel = chapel
        return self.__chapel


class AcademicsInformation:
    ACADEMICSURL = 'https://my.gcc.edu/ICS/Academics/'

    def __init__(self, data_collection: ScraperUtils, username, password):
        self.dc = data_collection
        self.__username = username
        self.__password = password

    def get_course_scraper(self, callback):
        return AsyncCourseScraper(self.__username, self.__password, callback)


class AdvisingInformation:
    ADVISINGURL = 'https://my.gcc.edu/ICS/Advising/'

    def __init__(self, data_collection: ScraperUtils, username, password):
        self.dc = data_collection
        self.__username = username
        self.__password = password
        self.__is_advisor = None

    @property
    def is_advisor(self):
        if self.__is_advisor is None:
            try:
                self.dc.http_get(self.ADVISINGURL)
                self.__is_advisor = True
            except errors.UnauthorizedError:
                self.__is_advisor = False
        return self.__is_advisor

    def get_advisee_scraper(self, callback):
        return AsyncAdviseeScraper(self.__username, self.__password, callback)


class MyGcc:

    def __init__(self, username, password):
        self._dc = ScraperUtils()
        self.__username = username
        self.__password = password
        self._logged_in = False
        self.__profile = None
        self.__student = None
        self.__academics = None
        self.__advising = None

    def login(self):
        dc = self._dc
        dc.perform_login(self.__username, self.__password)
        dc.check_for_error_message()
        self._logged_in = True
        return True

    def logout(self):
        dc = self._dc
        if self._logged_in:
            logout_btn = dc.html.find('a', {'id': 'logout'})
            if logout_btn is not None:
                action, payload = dc.prepare_payload(nav_element=logout_btn)
                post_url = dc.BASE_URL + action
                dc.http_post(post_url, data=payload)
            self._logged_in = False

    @property
    def profile(self):
        if self.__profile is None:
            self._ensure_login()
            self.__profile = ProfileInformation(self._dc)
        return self.__profile

    @property
    def student(self):
        if self.__student is None:
            self._ensure_login()
            self.__student = StudentInformation(self._dc)
        return self.__student

    @property
    def academics(self):
        if self.__academics is None:
            self._ensure_login()
            self.__academics = AcademicsInformation(self._dc, self.__username, self.__password)
        return self.__academics

    @property
    def advising(self):
        if self.__advising is None:
            self._ensure_login()
            self.__advising = AdvisingInformation(self._dc, self.__username, self.__password)
        return self.__advising

    def _ensure_login(self):
        if self._logged_in is False:
            self.login()
