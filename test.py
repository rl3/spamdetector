

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from tools import read_mail_from_file

mail = read_mail_from_file('mails/stephan/Spam/636.')
if mail:
    vect = MyVectorizer(
        ngram_range=(1, 3),
        strip_accents='unicode',
        decode_error='ignore'
    )
    vect = CountVectorizer(
        ngram_range=(1, 3),
        strip_accents='unicode',
        decode_error='ignore',

    )
    subjects: list[str] = ['huhu', 'haha', 'hhjoho']
    froms: list[str] = ["huhu", "hihi", "huhu"]
    bodies: list[str] = ["hoho", "huhu", "haha"]

    # subjects: list[str] = ['huhu']
    # froms: list[str] = ["huhu"]
    # bodies: list[str] = ["hoho"]

    vect.fit(froms)
    print(vect.vocabulary_, vect.fixed_vocabulary_)
    vect = MyVectorizer(
        ngram_range=(1, 3),
        strip_accents='unicode',
        decode_error='ignore',
        vocabulary=vect.vocabulary_,
    )
    vect.fit(subjects)
    print(vect.vocabulary_, vect.fixed_vocabulary_)
    vect.fit(bodies)
    print(vect.vocabulary_, vect.fixed_vocabulary_)
    exit()

    cv1 = vect.transform(subjects)
    # print(vect.vocabulary_)
    cv2 = vect.transform(froms)
    # print(vect.vocabulary_)
    cv3 = vect.transform(bodies)
    # print(vect.vocabulary_)
    # print(cv1, cv2, cv3)
    print(cv1 + cv2 + cv3)
    # print(vect.get_feature_names())
    print(vect.vocabulary_)
