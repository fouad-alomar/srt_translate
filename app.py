# import pydeepl
import deepl
import urllib.request, json
import http.client
import logging
import time
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

import re
import os
from dotenv import load_dotenv

import json
from sys import argv

from datetime import datetime
from extract import to_extract_ayas

# this pattern will match speaker : if we need other characters to be detected we should add | blabla
pattern = "[a-zA-Z0-9]+\s*:.*|^\s{0,5}-.*|^\s{0,5}>.*|^\s{0,5}=.*"#"[a-zA-Z0-9]+\s*:.*"
# the search will be in the first N charchters  no need to search all the text
N = 15
# split speakers with the following chatchter

SP = "$$"
CT = '^^'
SSP = f'<x>{SP}</x>'
CCT = f'<x>{CT}</x>'

load_dotenv(".env")
AUTH_KEY = os.environ.get("DEEPL_API_KEY")

app = Flask(__name__,static_folder='public', template_folder='views')

upload_path = 'inputs'
translated_path = 'public/outputs'

def parse_srt(srt_string):
    srt_list = []

    for line in srt_string.split('\n\n'):
        if line != '':
            index = int(re.match(r'\d+', line).group())

            pos = re.search(r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+',
                            line).end() + 1
            content = line[pos:]

            section_time = re.findall(
                r'(\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+)', line)[0]

            if re.search(pattern,content[0:N]):
                # if new speaker found we add speaker split charachters at the begining
                content_api = SSP + content
            else:
                # else it is continued text for the previous speaker
                content_api = CCT + content

            srt_list.append({
                'index': index,
                'content': content,
                'section_time':section_time,
                'content_api':content_api,
                'translate':''
            })

    return srt_list

def json_to_srt(json_list , content='content'):
    srt_string = ''
    list_length = len(json_list)
    for index ,jsonObj in enumerate(json_list):
        if 'index' in jsonObj:
            srt_string += str(jsonObj.get('index')) + '\n'
        if 'section_time' in jsonObj:
            srt_string += jsonObj.get('section_time') + '\n'
            if index ==list_length - 1:
                srt_string += jsonObj.get(content)
            else:
                srt_string += jsonObj.get(content) + '\n\n'
    return srt_string
    
def translate_hundler(srt_filename, lang):
    pathname, extension = os.path.splitext(srt_filename)
    file = pathname.split('/')
    if file:
        output_srt = f'{ file[-1]}-{lang}-translated.srt'
    else:
        output_srt = f'{ os.path.basename(srt_filename)}-{lang}-translated.srt'

    # srt_filename = 'input.srt'
    out_filename = 'output.json'
    
    srt = open(srt_filename, 'r', encoding="utf-8").read()


    # # testing text with ayas
    # logging.error('================1==================')
    # arb_srt = open('extract/ar-002-003-r08-2.srt', 'r', encoding="utf-8").read()
    # www = to_extract_ayas(arb_srt)
    # #rwwww = json_to_srt(www["srt_list"])
    
    # logging.error(www)
    # logging.error('================end==================')
    
    parsed_srt = parse_srt(srt)

    # step 1 to this point the text is ready => should be accumlated then call the translate api
    accumulated_text =''
    for record in parsed_srt:
        accumulated_text += record['content_api']
    
    # step 2 translate text by calling deepl api
    translator = deepl.Translator(AUTH_KEY) 
    result = translator.translate_text(accumulated_text, target_lang= lang, tag_handling="xml", ignore_tags="x") 
    translated_text = result.text

    # step 2 reverse the translated text into the json object
    translate_list = []
    speakers_sections = translated_text.split(SSP)
    for section in speakers_sections:
        if section != '':
            for part in section.split(CCT):
                if part != '':
                    translate_list.append(part)
            
        

    # if the length of original data and the translated list are equel => the api result is ok
    if len(parsed_srt) == len(translate_list):
        for index ,jsonObj in enumerate(parsed_srt):
            jsonObj['translate'] = translate_list[index]


    # logging.error('%s raised an error', str(translate_list))
    

    # # for testing
    open(out_filename, 'w', encoding="utf-8").write(json.dumps(parsed_srt, indent=2, sort_keys=True))
    output_srt_file = os.path.join(translated_path, output_srt)
    result =  { "str_content" : json_to_srt(parsed_srt,'translate') ,"srt_file": output_srt_file }
    open(output_srt_file, 'w', encoding="utf-8").write(result['str_content'])
    return result
    #return 'The lengths checking (should be  equal) :' + str(len(parsed_srt))  + 'len' + str(len(translate_list))  + translated_text



@app.route('/upload')
def upload_file_page():
   return render_template('upload.html')
	
@app.route('/uploader', methods = ['GET', 'POST'])
def upload_file():
   if request.method == 'POST':
      f = request.files['file']
      target_lang = request.form.getlist('language')[0]
      
      file_path = os.path.join(upload_path, secure_filename(f.filename))
      if not os.path.exists(upload_path):
        os.makedirs(upload_path)
      f.save(file_path)
      if not os.path.exists(translated_path):
        os.makedirs(translated_path)
      res = "<h3> Failed </h3>"
      if file_path and target_lang:
        returned = translate_hundler(file_path ,target_lang)
        str_content = returned["str_content"]
        srt_file =returned["srt_file"]
        res = f"""
      <!DOCTYPE html>  
        <html>
        <head>
            <link rel="stylesheet" href="/public/css/style.css">
        </head> 
        <body>
        <div class="row">
         <div class="column side">
         </div>
         <div class="column middle">  
        <form action = "http://localhost:8000/upload" method = "GET">  
        <h3>SRT Content (({target_lang} )):</h3><br>
        <textarea rows="35" cols="100">
        {str_content}
        </textarea>  
        <input type="submit" value="Go back!">
        </form>
        <form method="get" action="/{srt_file}">
            <input type="submit" value="Download">
        </form>
        </div> 
         <div class="column side">
         </div>
        </div>
        </body>  
        </html>
      """ 
      
      
      return res
		
if __name__ == '__main__':
   app.run(debug = True)