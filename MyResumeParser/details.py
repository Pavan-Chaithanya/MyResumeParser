import os,re,nltk
import pandas as pd
from datetime import datetime
from dateutil import relativedelta
import constants as cs
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from pdfminer.pdfpage import PDFPage

def get_number_of_pages(file_name):
    if file_name.endswith('.pdf'):
        count = 0
        with open(file_name, 'rb') as fh:
            for page in PDFPage.get_pages(fh, 
                                        caching=True,
                                        check_extractable=True):
                count += 1
        return count
    else:
        return None
def extract_entity_sections_grad(text):

    text_split = [i.strip() for i in text.split('\n')]

    entities = {}
    key = False
    for phrase in text_split:
        if len(phrase) == 1:
            p_key = phrase
        else:
            p_key = set(phrase.lower().split()) & set(cs.RESUME_SECTIONS_GRAD)
        try:
            p_key = list(p_key)[0]
        except IndexError:
            pass
        if p_key in cs.RESUME_SECTIONS_GRAD:
            entities[p_key] = []
            key = p_key
        elif key and phrase.strip():
            entities[key].append(phrase)
    return entities
def get_total_experience(experience_list):
    exp_ = []
    for line in experience_list:
        experience = re.search('(?P<fmonth>\w+.\d+)\s*(\D|to)\s*(?P<smonth>\w+.\d+|present|till date)', line, re.I)
        if experience:
            exp_.append(experience.groups())
    total_experience_in_months = sum([get_number_of_months_from_dates(i[0], i[2]) for i in exp_])
    return total_experience_in_months
def extract_email(text):
    email = re.findall("([^@|\s]+@[^@]+\.[^@|\s]+)", text)
    if email:
        try:
            return email[0].split()[0].strip(';')
        except IndexError:
            return None
def extract_name(nlp_text, matcher):
    pattern = [cs.NAME_PATTERN]
    
    matcher.add('NAME', None, *pattern)
    
    matches = matcher(nlp_text)
    
    for _, start, end in matches:
        span = nlp_text[start:end]
        return span.text
def extract_mobile_number(text):
    phone = re.findall(re.compile(r'(?:(?:\+?([1-9]|[0-9][0-9]|[0-9][0-9][0-9])\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([0-9][1-9]|[0-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})(?:\s*(?:#|x\.?|ext\.?|extension)\s*(\d+))?'), text)
    if phone:
        number = ''.join(phone[0])
        if len(number) > 10:
            return '+' + number
        else:
            return number
def extract_skills(nlp_text, noun_chunks):
    tokens = [token.text for token in nlp_text if not token.is_stop]
    data = pd.read_csv(os.path.join(os.path.dirname(__file__), 'skills.csv')) 
    skills = list(data.columns.values)
    skillset = []
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
    return [i.capitalize() for i in set([i.lower() for i in skillset])]
def extract_education(nlp_text):
    edu = {}
    for index, text in enumerate(nlp_text):
        for tex in text.split():
            tex = re.sub(r'[?|$|.|!|,]', r'', tex)
            if tex.upper() in cs.EDUCATION and tex not in cs.STOPWORDS:
                edu[tex] = text + nlp_text[index + 1]
    education = []
    for key in edu.keys():
        year = re.search(re.compile(cs.YEAR), edu[key])
        if year:
            education.append((key, ''.join(year.group(0))))
        else:
            education.append(key)
    return education
def extract_experience(resume_text):
    wordnet_lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english')) 
    word_tokens = nltk.word_tokenize(resume_text) 
    filtered_sentence = [w for w in word_tokens if not w in stop_words and wordnet_lemmatizer.lemmatize(w) not in stop_words] 
    sent = nltk.pos_tag(filtered_sentence)
    cp = nltk.RegexpParser('P: {<NNP>+}')
    cs = cp.parse(sent)
    test = []
    for vp in list(cs.subtrees(filter=lambda x: x.label()=='P')):
        test.append(" ".join([i[0] for i in vp.leaves() if len(vp.leaves()) >= 2]))
    x = [x[x.lower().index('experience') + 10:] for i, x in enumerate(test) if x and 'experience' in x.lower()]
    return x
