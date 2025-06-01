import os
import sys
import random
import socket
import urllib
import argparse
import re
import json
import shutil
from bs4 import BeautifulSoup
from http import cookiejar

from Utils import *

class BrowserBase(object):
    def __init__(self, frame, version, APIList, APINote):
        socket.setdefaulttimeout(20)
        self.frame = frame
        self.version = version
        self.APIList = APIList
        self.APINote = APINote
        self.HTML = ''
        self.ActualName = ''
        self.ExpectedName = ''
        self.ExpectedUrl = []
        self.DismatchExpectedName = []
        self.DismatchNotedName = []
        print('--- Starting to crawl {} API Documents on version: '.format(self.frame) + version + ' ---')
        sys.stdout.flush()
        if self.frame == 'PyTorch':
            self.WebPrefix = 'https://pytorch.org/docs/' + self.version + '/'
            self.OriginalUrl = 'https://pytorch.org/docs/' + self.version + '/torch.html'
        elif self.frame == 'TensorFlow':
            if self.version == 'stable':
                self.WebPrefix = 'https://tensorflow.google.cn/api_docs/python/'
            else:
                self.WebPrefix = 'https://tensorflow.google.cn/versions/r' + self.version + '/api_docs/python/'
            self.OriginalUrl = 'https://tensorflow.google.cn/api_docs/python/tf'

    def clear(self):
        self.HTML = ''
        self.ActualName = ''
        self.ExpectedName = ''
        self.ExpectedUrl = []
    def set_expected(self, expected_name):
        self.clear()
        if expected_name in self.APINote:
            if self.APINote[expected_name]["Removed"]:
                raise Exception(f'Function {expected_name} is removed in {self.frame} {self.version}')
            if self.APINote[expected_name]["AbstractClass"]:
                raise Exception(f'Function {expected_name} is abstract class in {self.frame} {self.version}')
            if "ActualName" in self.APINote[expected_name]:
                print(f"Warning: Change APIName from {expected_name} to {self.APINote[expected_name]['ActualName']} for APINote")
                self.ExpectedName = self.APINote[expected_name]["ActualName"]
            else:
                self.ExpectedName = expected_name
            if self.APINote[expected_name]["WebSuffix"] != None:
                self.ExpectedUrl.append(self.WebPrefix + self.APINote[expected_name]["WebSuffix"])
                return
        else:
            self.ExpectedName = expected_name
        expected_name = self.ExpectedName
        
        if self.frame == 'PyTorch':
            if ('Storage' in expected_name or 'storage' in expected_name) and "is_storage" not in expected_name and "Tensor.storage" not in expected_name:
                self.ExpectedUrl.append('https://pytorch.org/docs/' + self.version + '/storage.html')
            elif 'torch.distributed.elastic.multiprocessing.errors.' in expected_name:
                self.ExpectedUrl.append('https://pytorch.org/docs/' + self.version + '/elastic/errors.html')
            elif 'torch.distributed.elastic.' in expected_name:
                temp_suffix = expected_name[len('torch.distributed.elastic.'):].split('.')[0]
                self.ExpectedUrl.append('https://pytorch.org/docs/' + self.version + '/elastic/' + temp_suffix + '.html')
            elif 'torch.utils.benchmark' in expected_name:
                self.ExpectedUrl.append('https://pytorch.org/docs/' + self.version + '/benchmark_utils.html')
            else:
                if expected_name.startswith('torch.utils.'):
                    expected_name = 'torch.' + expected_name[len('torch.utils.'):]
                while expected_name != '':
                    self.ExpectedUrl.append('https://pytorch.org/docs/' + self.version + '/generated/' + expected_name + '.html')
                    self.ExpectedUrl.append('https://pytorch.org/docs/' + self.version + '/' + expected_name + '.html')
                    self.ExpectedUrl.append('https://pytorch.org/docs/' + self.version + '/' + expected_name[len('torch.'):] + '.html')
                    expected_name_split = expected_name.split('.')
                    expected_name_split.pop(-1)
                    expected_name = '.'.join(expected_name_split)
        elif self.frame == 'TensorFlow':
            if expected_name.startswith('tf.keras.layers.experimental.') or expected_name.startswith('tf.keras.mixed_precision.experimental.'):
                # Same to removed!
                raise Exception(f'Function {expected_name} is removed in {self.frame} {self.version}')
            self.ExpectedUrl.append('https://tensorflow.google.cn/api_docs/python/' + '/'.join(expected_name.split('.')))

    def openurl(self):
        cookie_support= urllib.request.HTTPCookieProcessor(cookiejar.CookieJar())
        self.opener = urllib.request.build_opener(cookie_support, urllib.request.HTTPHandler)
        urllib.request.install_opener(self.opener)
        user_agents = [
            'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
            'Opera/9.25 (Windows NT 5.1; U; en)',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
            'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
            'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
            'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
            "Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7",
            "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0 ",
        ]
        agent = random.choice(user_agents)
        if self.frame == 'PyTorch':
            self.opener.addheaders = [("User-agent",agent),("Accept","*/*"),('Referer','https://pytorch.org')]
        elif self.frame == 'TensorFlow':
            self.opener.addheaders = [("User-agent",agent),("Accept","*/*"),('Referer','https://tensorflow.google.cn')]
        for i, url in enumerate(self.ExpectedUrl):
            try:
                res = self.opener.open(url)
                assert res.code == 200, f"Function page loading wrong in code: {res.code}"
                self.HTML = res.read()
                if(i != 0):
                    print(f'Function page loading successfully in: {url}')
                    sys.stdout.flush()
                if url == self.OriginalUrl:
                    print(f"Warning: Function page loading same as {self.OriginalUrl}")
                break
            except Exception as e:
                print(str(e) + ', ' + self.ExpectedUrl[i])
                sys.stdout.flush()
                if i == len(self.ExpectedUrl) - 1:
                    raise Exception(f'Tried all page but loading wrong: ExpectedUrl: {str(self.ExpectedUrl)}')

    def getMainArticle(self):
        soup = BeautifulSoup(self.HTML, features="html.parser")
        self.ActualName = TextPattern.sub('', NamePattern.match(str(soup.findAll('h1')[0])).group(1)).strip()
        try:
            assert self.ActualName == self.ExpectedName
        except:
            print(f'Warning: Function name not match: ExpectedName: {self.ExpectedName}, ActualName: {self.ActualName}')
            sys.stdout.flush()
        if self.frame == 'PyTorch':
            self.HTML = '<html><meta charset="utf-8"><body>' + str(soup.findAll('article',{'id':'pytorch-article','class':'pytorch-article'})[0]) + '</body><html>'
        elif self.frame == 'TensorFlow':
            style_pattern = re.compile(r'<style.*?>.*?</style>', re.DOTALL)
            self.HTML = style_pattern.sub('', '<html><meta charset="utf-8"><body>' + str(soup.findAll('article',{'class':'devsite-article'})[0]) + '</body><html>')
        self.Text = TextPattern.sub('', str(self.HTML))
    
    def saveHTMLAndText(self):
        try:
            shutil.rmtree(os.path.join(CRAWLER_RESULTS_PATH.format(self.frame), "Crawler", self.ExpectedName))
            print("Warning: Remove old results:", os.path.join(CRAWLER_RESULTS_PATH.format(self.frame), "Crawler", self.ExpectedName))
        except:
            pass
        os.makedirs(os.path.join(CRAWLER_RESULTS_PATH.format(self.frame), "Crawler", self.ExpectedName), exist_ok=True)
        # save HTML
        HTMLPath = os.path.join(CRAWLER_RESULTS_PATH.format(self.frame), "Crawler", self.ExpectedName, self.ActualName+'.html')
        try:
            HTMLPointer = open(HTMLPath,'w+')
        except:
            raise FileNotFoundError(HTMLPath)
        HTMLPointer.write(self.HTML)
        HTMLPointer.close()
        # save text
        TextPath = os.path.join(CRAWLER_RESULTS_PATH.format(self.frame), "Crawler", self.ExpectedName, self.ActualName+'.txt')
        try:
            TextPointer = open(TextPath,'w+')
        except:
            raise FileNotFoundError(TextPath)
        TextPointer.write(self.Text)
        TextPointer.close()

    def OutDismatchAPI(self):
        print('All DismatchExpectedName: ' + str(self.DismatchExpectedName))
        print('All DismatchNotedName: ' + str(self.DismatchNotedName))
        sys.stdout.flush()

    def run(self, expected_name: str):
        print('--- Starting to crawl: ' + expected_name + ' ---')
        sys.stdout.flush()
        try:
            self.set_expected(expected_name)
            self.openurl()
            self.getMainArticle()
            self.saveHTMLAndText()
        except Exception as e:
            print(f"Error on {expected_name}:", str(e))
            sys.stdout.flush()
            if expected_name not in self.APINote:
                self.DismatchExpectedName.append(expected_name)
            else:
                self.DismatchNotedName.append(expected_name)

if __name__ == '__main__':
    # args
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame", type=str, default="TensorFlow", choices=["PyTorch", "TensorFlow"])
    parser.add_argument("--version", type=str, default="stable")
    args = parser.parse_args()
    # prepare
    APIListPath = os.path.join(DATA_PATH, "{}_API_List.txt".format(args.frame))
    APINotePath = os.path.join(DATA_PATH, "{}_API_Note.json".format(args.frame))
    if args.frame == "PyTorch":
        NamePattern = re.compile(r"^<h1>(.*?)(<a class=|$)")
    elif args.frame == "TensorFlow":
        NamePattern = re.compile(r'^<h1 class="devsite-page-title" tabindex="-1">\s*?(.*?)\s*?(<div class=|$)')
    TextPattern = re.compile(r"<[^<>]*?>|</[^<>]*?>")
    os.makedirs(CRAWLER_RESULTS_PATH.format(args.frame), exist_ok=True)
    os.makedirs(os.path.join(CRAWLER_RESULTS_PATH.format(args.frame), "Crawler"), exist_ok=True)
    
    if args.version != "stable":
        try:
            version = float(args.version)
        except:
            raise ValueError("version should be float or 'stable'!")
    # load api list
    print('--- Loading API list ---')
    sys.stdout.flush()
    with open(APIListPath, "r") as f:
        APIList = f.read().splitlines()
    # APIList = ["torch.nn.utils.prune.Identity"]
    APINote = json.load(open(APINotePath, 'r'))
    # apps
    browser = BrowserBase(args.frame, args.version, APIList, APINote)
    print("APIList:", str(APIList))
    print("APINote:", str(APINote))
    sys.stdout.flush()
    # crawl
    for api in APIList:
        browser.run(api)
    browser.OutDismatchAPI()
    print("APIList Num:", len(APIList))
    print("APINote Num:", len(APINote))