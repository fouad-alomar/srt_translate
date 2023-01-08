import logging
import time

import re

import json
from sys import argv

from datetime import datetime

fullCurlyBrackets = "\{(.*?)\}"
openCurlyBracket = "\{.*"
closeCurlyBracket = "\}.*"


def to_extract_ayas(srt_string):
    srt_list = []
    aya_json_list = []
    is_opened = False
    for line in srt_string.split('\n\n'):
        
        if line != '':
            index = int(re.match(r'\d+', line).group())

            pos = re.search(r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+',
                            line).end() + 1
            content = line[pos:]

            section_time = re.findall(
                r'(\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+)', line)[0]

            if re.search(fullCurlyBrackets,content) or (re.search(openCurlyBracket,content) and re.search(closeCurlyBracket,content) ):
                # if full curly brackets means aya just one line
                logging.error("{}")
                aya_json_list.append({
                    'index': index,
                    'content': content,
                    'section_time':section_time,
                })
                is_opened = False
            elif ((is_opened == True) and (re.search(closeCurlyBracket,content) is None )):
                logging.error("open true no closed")
                aya_json_list.append({
                    'index': index,
                    'content': content,
                    'section_time':section_time,
                })
            elif ((is_opened == True) and re.search(closeCurlyBracket,content)):
                logging.error("open true + }")
                aya_json_list.append({
                    'index': index,
                    'content': content,
                    'section_time':section_time,
                })
                is_opened = False
            elif re.search(openCurlyBracket,content):
                logging.error("open {")
                aya_json_list.append({
                    'index': index,
                    'content': content,
                    'section_time':section_time,
                })
                is_opened = True
            else:
                srt_list.append({
                'index': index,
                'content': content,
                'section_time':section_time,
            })
                is_opened = False
                logging.error("should be normal")
            

            logging.error("\n====>" +str(index) +" : "+ str(is_opened))
            continue




            

            
    result = []
    result.append({
                'aya_json_list': aya_json_list,
                'srt_list': srt_list
            })
    return result
    