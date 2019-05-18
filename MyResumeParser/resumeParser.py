import os,details,spacy,extract,multiprocessing
from spacy.matcher import Matcher
from pprint import pprint
class ResumeParser(object):
    def __init__(self, resume):
        nlp = spacy.load('en_core_web_sm')
        self._matcher = Matcher(nlp.vocab)
        self._details = {
            'name' : None, 'email' : None, 'mobile_number' : None,
            'skills' : None, 'education' : None, 'experience' : None, 'total_experience' : None,
        }
        self._resume      = resume
        self._alpha_text    = extract.extract_text(self._resume)
        self._text        = ' '.join(self._alpha_text.split())
        self._nlp         = nlp(self._text)
        self._noun_chunks = list(self._nlp.noun_chunks)
        self._get_total_details()

    def get_extracted_data(self):
        return self._details

    def _get_total_details(self):
        name       = details.extract_name(self._nlp, matcher=self._matcher)
        email      = details.extract_email(self._text)
        mobile     = details.extract_mobile_number(self._text)
        skills     = details.extract_skills(self._nlp, self._noun_chunks)
        edu        = details.extract_education([sent.string.strip() for sent in self._nlp.sents])
        entities   = details.extract_entity_sections_grad(self._alpha_text)
        self._details['name'] = name
        self._details['email'] = email
        self._details['mobile_number'] = mobile
        self._details['skills'] = skills
        self._details['education'] = edu
        try:
            self._details['experience'] = entities['experience']
            try:
                self._details['total_experience'] = round(details.get_total_experience(entities['experience']) / 12, 2)
            except KeyError:
                self._details['total_experience'] = 0
        except KeyError:
            pass
        self._details['no_of_pages'] = details.get_number_of_pages(self._resume)
        return
def resume_result_wrapper(resume):
        parser = ResumeParser(resume)
        return parser.get_total_details()
if __name__ == '__main__':
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    beginResumes = []
    data = []
    for root, directories, filenames in os.walk('resumes'):
        for filename in filenames:
            file = os.path.join(root, filename)
            finalResumes.append(file)

    finalResumes = [pool.apply_async(resume_result_wrapper, args=(x,)) for x in finalResumes]

    finalResumes = [p.get() for p in finalResumes]

    pprint(finalResumes)
