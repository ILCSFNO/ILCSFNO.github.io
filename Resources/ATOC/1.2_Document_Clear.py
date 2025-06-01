import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import sys
import glob
import re
import json
import torch
import tensorflow
import shutil
import argparse

from Utils import *

if __name__ == "__main__":
    # args
    parser = argparse.ArgumentParser()
    parser.add_argument("--frame", type=str, default="TensorFlow", choices=["PyTorch", "TensorFlow"])
    args = parser.parse_args()
    # prepare
    os.makedirs(CRAWLER_RESULTS_PATH.format(args.frame), exist_ok=True)
    all_document_path = os.path.join(CRAWLER_RESULTS_PATH.format(args.frame), "Crawler")
    output_path = os.path.join(CRAWLER_RESULTS_PATH.format(args.frame), "Document_Clear")
    os.makedirs(os.path.join(CRAWLER_RESULTS_PATH.format(args.frame), "Document_Clear"), exist_ok=True)
    mypython = TESTORACLE_PYTHON_PATH
    api_list = [ _[len(all_document_path)+1:] for _ in glob.glob(os.path.join(all_document_path, "*")) if os.path.isdir(_)]
    # api_list = ['torch.arange', 'torch.optim.Adam', 'torch.addcdiv', 'torch.nn.init.orthogonal_', 'torch.utils.data.BatchSampler'] # ！！！！！！！！！！！！！！！！！！！
    dismatch_api = []
    match_api = []
    record = []
    print('api list:', api_list)
    # clear
    for api in api_list:
        print(f'--- Dealing with {api} ---')
        sys.stdout.flush()
        try:
            try:
                shutil.rmtree(os.path.join(output_path, api))
                print("Warning: Remove old results:", os.path.join(output_path, api))
            except:
                pass
            if args.frame == "PyTorch":
                # document
                document_path = glob.glob(os.path.join(all_document_path, api, "*.txt"))[0]
                document_name = document_path[len(os.path.join(all_document_path, api))+1:-len(".txt")]
                old_document = open(document_path).read()
                document = old_document
                document = re.sub(r'\\text\{(.*?)\}', r'`\1`', document)
                document = re.sub(r'\\texttt\{(.*?)\}', r'`\1`', document)
                flag = False
                while document != "" and document.find(api) != -1: # note for api A in api B: name
                    document = document[document.find(api):]
                    if document.split('\n')[0].find('¶') != -1 and not document[len(api)].isalpha():
                        flag = True
                        break
                    else:
                        document = '\n'.join(document.split('\n')[1:])
                if flag:
                    document_end = '\n'.join(document.split('\n')[1:])
                    while True:
                        tag = document_end.rfind('¶')
                        if tag != -1 and api not in document_end[:tag].split('\n')[-1]:
                            document_end = '\n'.join(document_end[:tag].split('\n')[:-1])
                        else:
                            break
                    document = document.split('\n')[0] + '\n' + document_end
                else:
                    try:
                        document = eval(api).__doc__
                        print(document)
                    except:
                        raise Exception('API not Existed!')
                    raise Exception('API no normal introduction online!')
                # place
                first_note = document.find('Note\n')
                first_warning = document.find('Warning\n')
                first_parameters = document.find('Parameters\n')
                first_keyword_arguments = document.find('Keyword Arguments\n')
                first_place = len(document)
                if first_note != -1:
                    first_place = min(first_place, first_note)
                if first_warning != -1:
                    first_place = min(first_place, first_warning)
                if first_parameters != -1:
                    first_place = min(first_place, first_parameters)
                if first_keyword_arguments != -1:
                    first_place = min(first_place, first_keyword_arguments)
                
                if first_parameters == -1:
                    raise Exception('API no parameters!')
                # introduction
                introduction = document[:first_place]
                introduction = introduction.strip()
                while(introduction.find('\n\n') != -1):
                    introduction = introduction.replace('\n\n', '\n')
                # parameters
                mark_parameters = 1
                if first_parameters != -1:
                    parameters = document[first_parameters:first_parameters+len('Parameters\n')+document[first_parameters+len('Parameters\n'):].find('\n\n')]
                    parameters = parameters.split('\n')
                    temp_parameters = ['Parameters']
                    for i in range(1, len(parameters)):
                        if(parameters[i].find(" – ") != -1):
                            temp_parameters.append("(" + str(mark_parameters) + ") " + parameters[i])
                            mark_parameters += 1
                        else:
                            if len(temp_parameters) != 1:
                                temp_parameters[-1] += parameters[i]
                    parameters = '\n'.join(temp_parameters)
                else:
                    parameters = ""
                parameters = parameters.strip()
                while(parameters.find('\n\n') != -1):
                    parameters = parameters.replace('\n\n', '\n')
                # keyword_arguments
                mark = mark_parameters
                mark_parameters -= 1
                if first_keyword_arguments != -1:
                    keyword_arguments = document[first_keyword_arguments:first_keyword_arguments+len('Keyword Arguments\n')+document[first_keyword_arguments+len('Keyword Arguments\n'):].find('\n\n')]
                    keyword_arguments = keyword_arguments.split('\n')
                    temp_keyword_arguments = ['Keyword Arguments']
                    for i in range(1, len(keyword_arguments)):
                        if(keyword_arguments[i].find(" – ") != -1):
                            temp_keyword_arguments.append("(" + str(mark) + ") " + keyword_arguments[i])
                            mark += 1
                        else:
                            if len(temp_keyword_arguments) != 1:
                                temp_keyword_arguments[-1] += keyword_arguments[i]
                    keyword_arguments = '\n'.join(temp_keyword_arguments)
                else:
                    keyword_arguments = ""
                keyword_arguments = keyword_arguments.strip()
                while(keyword_arguments.find('\n\n') != -1):
                    keyword_arguments = keyword_arguments.replace('\n\n', '\n')
                mark -= 1
                # save
                new_document = introduction + '\n\n' + parameters + '\n\n' + keyword_arguments
                os.makedirs(os.path.join(output_path, api), exist_ok=True)
                open(os.path.join(output_path, api, document_name+'.ini'), 'w').write(old_document)
                open(os.path.join(output_path, api, document_name+'.txt'), 'w').write(new_document)
                match_api.append(api)
                record.append({
                    'api': api,
                    'mark': mark,
                    'mark-parameters': mark_parameters,
                    'mark-keyword_arguments': mark-mark_parameters,
                    'introduction': introduction,
                    'parameters': parameters,
                    'keyword_arguments': keyword_arguments,
                    'old-document': old_document,
                    'new-document': new_document
                })
                record.sort(key=lambda x: x['mark'], reverse=True)
                json.dump(record, open(os.path.join(output_path, 'record.json'), 'w'), indent=4)
            elif args.frame == "TensorFlow":
                # document
                document_path = glob.glob(os.path.join(all_document_path, api, "*.txt"))[0]
                document_name = document_path[len(os.path.join(all_document_path, api))+1:-len(".txt")]
                old_document = open(document_path).read()
                document = old_document
                document = re.sub(r'\\text\{(.*?)\}', r'`\1`', document)
                document = re.sub(r'\\texttt\{(.*?)\}', r'`\1`', document)
                # introduction
                document_st = ""
                while(document != ""):
                    document_st = document.split('\n')[0]
                    if document_st != "" and not document_st.startswith(" "):
                        break
                    document = '\n'.join(document.split('\n')[1:])
                assert not document_st.startswith(" ")
                introduction = document[:document.find("\n\n")].strip().replace('\n', ' ')
                while introduction.find('  ') != -1:
                    introduction = introduction.replace('  ', ' ')
                
                document = document[:document.find('Methods\n')] # escape methods section below
                
                if document.find(api + '(\n'):
                    usage = document[document.find(api + '(\n'):]
                    usage = usage[:usage.find('\n\n')]
                    usage = usage.strip().replace('\n', ' ')
                    while usage.find('  ') != -1:
                        usage = usage.replace('  ', ' ')
                else:
                    usage = api
                
                first_parameters = document.find('Args\n')
                if first_parameters == -1:
                    raise Exception('API no parameters!')
                document = document[document.find('Args\n\n\n')+len('Args\n\n\n'):]
                document = document[:document.find('\n\n\n\n\n')]
                document_list = document.strip().split('\n\n\n\n')
                
                # parameters
                mark_parameters = 1
                parameters = 'Args\n'
                for single_document in document_list:
                    single_document_list = single_document.strip().split('\n\n\n')
                    if len(single_document_list) != 2:
                        print(f'single_document_list not just include arg and its description!, {single_document_list}')
                        break
                    if len(single_document_list[0].strip().split('\n')) != 1:
                        print(f'single_document_list[0] not arg!, {single_document_list}')
                        break
                    temp_name = single_document_list[0].strip()
                    temp_desc = single_document_list[1].strip().replace('\n', ' ')
                    while temp_desc.find('  ') != -1:
                        temp_desc = temp_desc.replace('  ', ' ')
                    parameters += f"({mark_parameters}) {temp_name}: {temp_desc}\n"
                    mark_parameters += 1
                mark_parameters -= 1
                
                # save
                new_document = usage + '\n\n' + introduction + '\n\n' + parameters
                os.makedirs(os.path.join(output_path, api), exist_ok=True)
                open(os.path.join(output_path, api, document_name+'.ini'), 'w').write(old_document)
                open(os.path.join(output_path, api, document_name+'.txt'), 'w').write(new_document)
                match_api.append(api)
                record.append({
                    'api': api,
                    'mark': mark_parameters,
                    'mark-parameters': mark_parameters,
                    'mark-keyword_arguments': 0,
                    'introduction': introduction,
                    'parameters': parameters,
                    'keyword_arguments': '',
                    'old-document': old_document,
                    'new-document': new_document
                })
                record.sort(key=lambda x: x['mark'], reverse=True)
                json.dump(record, open(os.path.join(output_path, 'record.json'), 'w'), indent=4)
        except Exception as e:
            print(f'Document Error for api {api}, Error: {e}')
            dismatch_api.append(api)
            continue
    print('match_api:', str(match_api))
    print('dismatch_api:', str(dismatch_api))
    print('match_api num:', len(match_api))
    print('dismatch_api num:', len(dismatch_api))