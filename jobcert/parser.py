import json
from bs4 import BeautifulSoup
from textstat.textstat import textstat
import genderdecoder

class JobAdvert():
    title = None
    description = None
    publishing_format = None
    creative_commons_licences = []
    salary = None

    def to_text(self):
        return "%s" % (self.description)

class Parser():

    job_advert = None
    results = []

    def _parse_creative_commons_licence(self, data):
        licences = []
        soup = BeautifulSoup(data, "html5lib")

        #look in <head>
        for link in soup.find_all("link", attrs={"rel": "license"}):
            if '//creativecommons.org/licenses/' in link['href']:
                licences.append({'name':'', 'url': link['href']})

        #look for anchors
        for a in soup.find_all("a", attrs={"rel": "license"}):
            if '//creativecommons.org/licenses/' in a['href']:
                licences.append({'name':'', 'url': a['href']})

        for licence in licences:
            if '//creativecommons.org/licenses/by-nd/4.0' in licence['url']:
                licence['name'] = 'Creative Commons Attribution'
            elif '//creativecommons.org/licenses/by-nd' in licence['url']:
                licence['name'] = 'Creative Commons Attribution-NoDerivs'
            elif '//creativecommons.org/licenses/by-nc-sa' in licence['url']:
                licence['name'] = 'Attribution-NonCommercial-ShareAlike'
            elif '//creativecommons.org/licenses/by-sa' in licence['url']:
                licence['name'] = 'Attribution-ShareAlike'
            elif '//creativecommons.org/licenses/by-nc' in licence['url']:
                licence['name'] = 'Attribution-NonCommercial'
            elif '//creativecommons.org/licenses/by-nc-nd' in licence['url']:
                licence['name'] = 'Attribution-NonCommercial-NoDerivs'
            else:
                licence['name'] = 'Creative Commons (unable to determine exact licence)'            

        self.job_advert.creative_commons_licences = licences

    @staticmethod
    def calculate_flesch_reading_ease(data):
        try:
            return textstat.flesch_reading_ease(data)
        except TypeError:
            return None

    @staticmethod
    def has_jobposting(data):
        soup = BeautifulSoup(data, "html5lib")

        # Look for any of the 3 types of JobPosting markups
        job_posting_found = []

        # Case 1: Microdata
        job_posting_found.append(
            soup.findAll('div', {'itemtype' : 'http://schema.org/JobPosting'})
        )

        # Case 2: RDFa
        job_posting_found.append(
            soup.findAll('div', {
                'vocab' : 'http://schema.org/',
                'typeof': 'JobPosting',
            })
        )

        # Case 3: JSON-LD
        ld_jsons = soup.findAll('script', {
            'type' : 'application/ld+json',
        })
        for ld in ld_jsons:
            ld_json = json.loads(ld.string)
            job_posting_found.append(ld_json.get("@type", '') == "JobPosting")

        return any(job_posting_found)

    def get_result(self, name):
        """ Try and find a result based on a result name"""
        found = False
        for result in self.results:
            if result['name'] == name:
                found = result
                break
        return found

    def _parse_microdata(self, data):
        success = False
        soup = BeautifulSoup(data, "html5lib")
        job_advert = soup.find('div', {'itemtype' : 'http://schema.org/JobPosting'})
        if job_advert:
            success = True
            self.job_advert.publishing_format = 'microdata'

            #title
            title_element = job_advert.find(attrs={"itemprop": "title"})
            if title_element:
                self.job_advert.title = title_element.text

            #description
            description_element = job_advert.find(attrs={"itemprop": "description"})
            if description_element:
                self.job_advert.description = description_element.text

            #salary
            salary_currency_element = job_advert.find(attrs={"itemprop": "salaryCurrency"})
            base_salary_element = job_advert.find(attrs={"itemprop": "baseSalary"})

            if salary_currency_element:
                self.job_advert.salary = salary_currency_element.text
            if base_salary_element:
                self.job_advert.salary = self.job_advert.salary + " %s" %base_salary_element.text

        return success

    def _parse_rdfa(self, data):
        return False

    def _parse_jsonld(self, data):
        return False

    def _parse_html(self, data):
        return False

    def _analyse(self):

        #is jobPosting?
        self.results.append(
          {
            'name': 'valid-jobposting',
            'result': self.job_advert.publishing_format in ['microdata', 'rdfa', 'jsonld'],
            'explanation': '',
          }
        )

        #How easy is the description to read?
        self.results.append(
          {
            'name': 'flesch-reading-ease',
            'result': self.calculate_flesch_reading_ease(self.job_advert.to_text()),
            'explanation': '',
          }
        )

        #Is there a creative commons licence?
        self.results.append(
          {
            'name': 'creative-commons-licence',
            'result': len(self.job_advert.creative_commons_licences) > 0,
            'explanation': '',
          }
        )

        #Is the salary clear?
        self.results.append(
          {
            'name': 'has-salary',
            'result': self.job_advert.salary != None,
            'explanation': '',
          }
        )

        #Gender-coded language
        gender_coded_result = genderdecoder.assess(self.job_advert.to_text())
        self.results.append(
          {
            'name': 'gender-coded-language',
            'result': gender_coded_result['result'],
            'explanation': gender_coded_result['explanation'],
          }
        )

    def parse(self, data):
        self.job_advert = JobAdvert()
        self.results = []

        #try various ways of parsing the job advert
        success = self._parse_microdata(data)
        if not success:
            success = self._parse_rdfa(data)
        if not success:
            success = self._parse_jsonld(data)
        if not success:
            success = self._parse_html(data)

        #parse licence
        self._parse_creative_commons_licence(data)        

        #analyse
        self._analyse()






