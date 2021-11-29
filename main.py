# 导入相关包或模块
import json
import threading, queue
import time, os, subprocess
import requests, urllib, parsel
import random, re, base64
from bs4 import BeautifulSoup

if __name__ == '__main__':
    url = 'https://v.sjtu.edu.cn/course/mobile726.html'  #
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3741.400 QQBrowser/10.5.3863.400',
        'X-AjaxPro-Method': 'GetVideoHLSUrl',
        'Referer': 'https://v.sjtu.edu.cn/course/mobile726.html',
        'Cookie': 'v.sjtu=ffffffff097f1c2245525d5f4f58455e445a4a423660; ASP.NET_SessionId=qrxahuffix4iiouuwxfhtixe'

    }
    json_headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    r = requests.get(url=url, headers=headers)
    video_id_list = re.findall("play_some_video\(\d{3},\d{4}\)", r.text)
    split_test = re.split("</span>|style=' display:none' /></span><span style=' display:none '", r.text)
    video_title_list = []
    for temp in split_test:
        result = re.findall('video_title\d{4}.*', temp)
        if len(result) == 0:
            continue
        else:
            result = result[0].split('>')[1]
            video_title_list.append(result)

    m3u8_post_list = 'https://v.sjtu.edu.cn/ajaxpro/showmobile2,App_Web_0cyw3tth.ashx'

    for video_id_temp, video_title_temp in zip(video_id_list, video_title_list):
        course_id = video_id_temp.split('(')
        course_id = course_id[1].split(')')
        course_id = course_id[0].split(',')
        video_id = course_id[1]
        course_id = course_id[0]

        post_data = {}
        post_data['course_id'] = course_id
        post_data['video_id'] = video_id
        post_data_json = json.dumps(post_data)

        m3u8_playlist = requests.post(url=m3u8_post_list, data=post_data_json, headers=headers)
        m3u8_playlist_url = m3u8_playlist.json().get('value')
        # https://sv.sjtu.edu.cn/media/vod2013/_definst_/mp4:726-信息安全数学基础-陈恭亮/2020-12-22-9-45-29-8329.mp4/playlist.m3u8
        chunklist_base_url = m3u8_playlist_url[:-13]

        chunklist_m3u8 = requests.get(m3u8_playlist_url, headers=headers)
        chunklist_m3u8_url = re.findall('!#|.*.m3u8', chunklist_m3u8.text)

        media_ts = requests.get(chunklist_base_url + chunklist_m3u8_url[0], headers=headers)
        media_ts_url_list = re.findall('!#|.*.ts', media_ts.text)

        # control = video_title_temp.split(' ')[0]
        # if control < "5.1":
        #     continue

        # ['media_w856099523_0.ts', 'media_w856099523_1.ts', 'media_w856099523_2.ts', 'media_w856099523_3.ts', 'media_w856099523_4.ts', 'media_w856099523_5.ts', 'media_w856099523_6.ts']
        for temp in media_ts_url_list:
            response = requests.get(chunklist_base_url + temp, stream=True, headers=headers)
            ts_path = "./temp/" + video_title_temp + "_" + temp.split('_')[2]
            with open(ts_path, "wb+") as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
            print(ts_path + " OK")

            os.chdir('temp')
            os.system('cat *_*.ts >> all.ts')
            os.system('rm *_*.ts')
            os.chdir('..')
            # time.sleep(0.01)

        os.chdir('temp')
        # os.system('cat *_*.ts > all.ts')
        # os.system('rm *_*.ts')

        # file_name_temp = video_title_temp.split(' ')
        # file_name = ''
        # for temp in file_name_temp:
        #     file_name += temp

        cmd = 'ffmpeg -i all.ts -acodec copy -vcodec copy \'' + video_title_temp + '.mp4\''
        os.system(cmd)
        os.system('rm all.ts')
        os.chdir('..')
