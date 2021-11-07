import os

from flask import Flask
import os
import nltk
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
nltk.download('wordnet')


from string import ascii_letters


from pdf2image import convert_from_path, pdfinfo_from_path

import cv2.cv2 as cv2

import pytesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag


def tag_trans(S):
    S = S[:2]
    if S == "NN":
        return "n"
    if S == "VB":
        return "v"
    if S == "JJ":
        return "a"
    if S == "RB":
        return "r"
    return "e"


def app():
    # create and configure the app
    app = Flask(__name__)

    @app.route('/getRelatedPDFs', methods=['POST'])
    def getRelatedPDFs():
        stop_words = set(stopwords.words('english'))
        #we need to take the file from the request files
        if 'file' in request.files:
                file = request.files['file']
                # This isn't working, a text file is saved with the same name ,ending in pdf
                path = 'file.pdf'
                # file = open(path, 'wb')
                file.save(path)
                print('calculating number of pages')
                try:
                    info = pdfinfo_from_path(path, userpw=None, poppler_path=None)
                except:
                    print('failed in pdf parsing')
                    os.remove(path)
                    data = {'status': 'failure'}
                    return data, 500
                maxPages = info["Pages"]
                if maxPages > 20:
                    print(f'too many pages ({maxPages}) :/ skipping paper')
                    os.remove(path)
                    data = {'status': 'failure'}
                    return data, 500
                try:
                    pages = convert_from_path(path, dpi=350, fmt='jpeg')
                except:
                    print('errored in conversion')
                    os.remove(path)
                    data = {'status': 'failure'}
                    return data, 500
                text = ''
                print(f'calculated number of pages {len(pages)}, running OCR')
                for i, page in enumerate(pages):
                    print(f'running on page {i}/{len(pages)}')
                    image_name = 'file'  + ".jpg"
                    page.save(image_name, "JPEG")
                    # c = line_items_coordinates[1]

                    # cropping image img = image[y0:y1, x0:x1]
                    # img = image[c[0][1]:c[1][1], c[0][0]:c[1][0]]
                    img = cv2.imread(image_name)
                    # convert the image to black and white for better OCR
                    ret, thresh1 = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)

                    # pytesseract image to string to get results
                    t_text = str(pytesseract.image_to_string(thresh1, config='--psm 3'))
                    text = text + t_text.replace('.', '').replace(';', '').replace(':', '')
                    os.remove(image_name)
                    del img
                    del thresh1
                words = []
                for candidate in text.split():
                    if all(c in ascii_letters + '-\'' for c in candidate):
                        if len(candidate) == 1:
                            if candidate[0] in ascii_letters:
                                words.append(candidate)
                        else:
                            words.append(candidate)
                # print(words)
                words = pos_tag(words)
                # print(words)
                failcount = 0
                wordcount = 0
                lemmatizer = WordNetLemmatizer()
                word_string = ''
                try:
                    for t in words:
                        word = t[0].lower()
                        if word not in stop_words:
                            wordcount += 1
                            wtag = tag_trans(t[1])
                            # print(wtag)
                            if wtag == "e":
                                failcount += 1
                                word_string+=" " + word
                            else:
                                # print(f'trying to lemmatize {word} got {lemmatizer.lemmatize(word, wtag)}')
                                word_string+=" " + lemmatizer.lemmatize(word, wtag)
                        else:
                            pass
                except:
                    pass
                #TODO USE the word_string to generate the counts/ word vector
                #this will involve pulling the vocab shape from the sql server
                #then we will need to multiple the new document vector by all others in the server and return the top 20 ids from the sql server
                #that is all that needs to happen

        else:
            data = {'status':'failure'}
            return data, 500

    return app