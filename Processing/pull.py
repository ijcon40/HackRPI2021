import requests
import json
import shutil
import os
import nltk
# from memory_profiler import profile
from memory_profiler import profile

nltk.download('stopwords')
from nltk.corpus import stopwords
import gc
import random



from pdf2image import convert_from_path

import cv2.cv2 as cv2

import pytesseract
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

from google.cloud import storage

# Setting credentials using the downloaded JSON file



def mark_region(image_path):
    im = cv2.imread(image_path)

    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (9, 9), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 30)

    # Dilate to combine adjacent text contours
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    dilate = cv2.dilate(thresh, kernel, iterations=4)

    # Find contours, highlight text areas, and extract ROIs
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    image=im
    line_items_coordinates = []
    for c in cnts:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)

        if y >= 600 and x <= 1000:
            if area > 10000:
                image = cv2.rectangle(im, (x, y), (2200, y + h), color=(255, 0, 255), thickness=3)
                line_items_coordinates.append([(x, y), (2200, y + h)])

        if y >= 2400 and x <= 2000:
            image = cv2.rectangle(im, (x, y), (2200, y + h), color=(255, 0, 255), thickness=3)
            line_items_coordinates.append([(x, y), (2200, y + h)])

    return image, line_items_coordinates


# word_tokenize accepts
# a string as an input, not a file.
if __name__ == '__main__':
    api_key = 'QJhYeCVqW47z29PEvxrtoN3A0K1sZbLU'

    client = storage.Client.from_service_account_json(json_credentials_path='/home/ijcon40/hackrpi2021-6276c17facd0.json')

    # Creating bucket object
    # bucket = client.create_bucket('hackrpi2021-data')

    bucket = client.bucket('hackrpi2021-data')

    # Name of the object to be stored in the bucket

    # entropy -1099-4300
    # j_url = f'https://api.core.ac.uk/v3/journals/issn:{"1099-4300"}?api_key={api_key}'
    #https://api.core.ac.uk/v3/journals/issn:1099-4300?api_key={api_key}
    #https://api.core.ac.uk/v3/search/works?q=hi&api_key={api_key}
    j_url = f'https://api.core.ac.uk/v3/search/{"journals"}?api_key={api_key}&limit=9000'
    # payload = open("request.json")
    payload = {}
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    r = requests.get(j_url, data=payload, headers=headers)
    json_data={'results':[]}
    try:
        json_data = json.loads(r.text)
    except:
         print(r.content)

    #generate all the space journal identifiers
    journals = []
    keywords = ['astronomy', 'mars', 'entropy', 'thermodynamic', 'astrophysics']
    for result in json_data['results']:
        if result['language']=='English':
            for subject in result['subjects']:
                included = False
                for key in keywords:
                    if key in subject.lower():
                        included=True
                        for identifier in result['identifiers']:
                            if 'issn:' in identifier:
                                journals.append({'title':result['title'], 'issn':identifier, 'matched_keyword':key})
                                break
                        break
                if included:
                    break
    del json_data
    del r
    #for each of the journals disregarding the first one, we get all documents that correspond to their papers

    if(os.path.exists('./data')):
        shutil.rmtree('./data')
    if(os.path.exists('./testing')):
        shutil.rmtree('./testing')
    os.mkdir('./data')
    os.mkdir('./testing')

    stop_words = set(stopwords.words('english'))
    print(stop_words)
    print(f'got {len(journals)} journals')

    def getJournalDocuments(save_path, journal_obj):
        #get the papers from the journal and save them to an identifier
        api = f"https://api.core.ac.uk/v3/search/works?q=publisher:{journal_obj['title']}+_exists_:fullText+language:English&api_key={api_key}&limit=10000"
        r = requests.get(api, data=payload, headers=headers)
        identifiers=[]
        if(r.text is not None):
        # try:
            json_data = None
            try:
                json_data = json.loads(r.text)
            except:
                print('failed in parsing to json')
                del r
                del json_data
                return
            for result in json_data['results']:
                # if(len(result['identifiers'])>0):
                #     for identifier in result['identifiers']:
                #         if(identifier['type']=='CORE_ID'):
                identifiers.append((result['id'], result['title'].replace(' ', '_').replace('/', '+'), result['downloadUrl']))
            #take the identifiers from the work
            del json_data
        del r
        random.shuffle(identifiers)
        i = 0
        for id, title, link in identifiers:
            i+=1
            print(f'executing identifiers {i}/{len(identifiers)}')
            gc.collect()
            resp = requests.get(f'https://core.ac.uk/download/{id}.pdf')
            if(resp.status_code!=200):
                print('got bad status code, trying backup')
                try:
                    resp = requests.get(link)
                    if (resp.status_code != 200):
                        print('tried backup, still got bad status')
                        continue
                    else:
                        print('backup was successful')
                except:
                    print(f'backup failed with link {link}')

            file = open(save_path + str(id) + '.pdf', 'wb')
            file.write(resp.content)
            pages = -1
            try:
                pages = convert_from_path(save_path + str(id) + '.pdf', dpi=350, fmt='jpeg')
            except:
                print('errored in conversion')
                os.remove(save_path + str(id) + '.pdf')
                continue
            text = ''
            print(f'calculated number of pages {len(pages)}, running OCR')
            for i, page in enumerate(pages):
                print(f'running on page {i}/{len(pages)}')
                image_name = save_path + str(id) + ".jpg"
                page.save(image_name, "JPEG")
                # image, line_items_coordinates = mark_region(image_name)
                # c = line_items_coordinates[1]

                # cropping image img = image[y0:y1, x0:x1]
                # img = image[c[0][1]:c[1][1], c[0][0]:c[1][0]]
                img = cv2.imread(image_name)
                # convert the image to black and white for better OCR
                ret, thresh1 = cv2.threshold(img, 120, 255, cv2.THRESH_BINARY)

                # pytesseract image to string to get results
                t_text = str(pytesseract.image_to_string(thresh1, config='--psm 3'))
                text=text+t_text
                os.remove(save_path + str(id) + ".jpg")
                del img
                del thresh1
            print('finished OCR')
            words = text.split()
            try:
                appendFile = open(save_path + str(id) + '.txt', 'a')
                for word in words:
                    try:
                        float(word)
                    except:
                        if not word in stop_words:
                            appendFile.write(" " + word.lower())
                appendFile.close()
                print('saved file, trying to upload to gcloud')
                blob = bucket.blob('data_'+str(id)+'.txt')
                blob.upload_from_filename(save_path + str(id) + '.txt')
            except:
                print('errored in append to file')
                pass
            del blob
            del pages
            del words
            del text
            del resp
        del identifiers


    random.shuffle(journals)
    print('getting journal information')
    for i in range(0, len(journals)-1):
        journal=journals[i]
        getJournalDocuments('./data/', journal)
    getJournalDocuments('./testing/', journals[len(journals)-1])

    #subjects = space, LCC:Astronomy, Mars science, astronomy
