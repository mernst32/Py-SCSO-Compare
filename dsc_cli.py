import urllib.request
import urllib.parse
import json
import os
import time
import math
from urllib.error import HTTPError
import argparse


def handle_err(url, cause, src, id_num):
    try:
        os.makedirs("err/{0}".format(src))
    except FileExistsError as e:
        pass
    with open("err/{0}/{1}.error".format(src, id_num), 'w', encoding='utf-8') as ofile:
        ofile.write(url + '\n' + repr(cause))


def get_raw(url):
    # print("get data from "+url)
    contents = urllib.request.urlopen(url).read()
    return json.loads(contents.decode('utf-8'))


def get_page(search, page, per_page, src):
    params = {'q': search, 'lan': '23', 'p': page, 'per_page': per_page, 'src': src["id"]}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        results = raw_data["results"]
        id_list = []
        for result in results:
            id_list.append(result["id"])
        for id_num in id_list:
            url = "https://searchcode.com/api/result/" + str(id_num) + "/"
            try:
                code = get_raw(url)["code"]
                lines = code.split('\n')
                with open("out/{0}/{1}.java".format(src["source"], id_num), 'w', encoding='utf-8') as ofile:
                    ofile.write("// https://searchcode.com/codesearch/raw/" + str(id_num) + "/" + '\n')
                    for line in lines:
                        ofile.write(line + '\n')
            except HTTPError as e:
                handle_err(url, e, src["source"], id_num)
            except json.decoder.JSONDecodeError as e:
                handle_err(url, e, src["source"], id_num)
        return len(id_list)
    except HTTPError as e:
        print("ERROR:Could not get data from {0}: {1}".format(url, repr(e)))
        return 0


def get_java_code_from_repo(search, src, per_page):
    params = {'q': search, 'lan': '23', 'src': src["id"]}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        total = raw_data["total"]
        if total > (50 * per_page):
            total = (50 * per_page)
        pages = int(math.ceil(total / per_page))
        bar_len = 50
        dl_size = 0
        print("Downloading from {0}: ".format(src["source"]))
        for page in range(0, pages):
            dl_size = dl_size + get_page(search, page, per_page, src)

            if dl_size == 0:
                print("\tNothing to download!")
            else:
                prog = int(((page + 1) * bar_len) // pages)
                bar = '#' * prog + '.' * (bar_len - prog)
                print("\t{0}% [{1}] {2}/{3} Downloaded".format(int((prog / bar_len) * 100), bar, dl_size, total),
                      end='\r')
            time.sleep(1)
        print()
    except HTTPError as e:
        print("ERROR:Could not get data from {0}: {1}".format(url, repr(e)))


def handle_input(search, info, repo, per_page):
    params = {'q': search, 'lan': '23'}
    url = "https://searchcode.com/api/codesearch_I/?" + urllib.parse.urlencode(params)
    try:
        raw_data = get_raw(url)
        src_filters = raw_data["source_filters"]
        print("Found {0} repo-source(s) with java files, that contain the string \"{1}\".\n"
              .format(len(src_filters), search))
        if not info:
            try:
                os.makedirs("out")
                os.makedirs("err")
            except FileExistsError as e:
                pass
            print("Starting download of the Java files...")
            if repo == -1:
                for src in src_filters:
                    try:
                        os.makedirs("out/{0}".format(src["source"]))
                    except FileExistsError as e:
                        pass
                    get_java_code_from_repo(search, src, per_page)
                    time.sleep(2)
            else:
                for src in src_filters:
                    if src["id"] == repo:
                        try:
                            os.makedirs("out/{0}".format(src["source"]))
                        except FileExistsError as e:
                            pass
                        get_java_code_from_repo(search, src, per_page)
            print("DONE WITH DOWNLOADS!")
        else:
            for src in src_filters:
                print("{0}[repo_id: {1}] with a total of {2} restult(s)."
                      .format(src["source"], src["id"], src["count"]))
                if src["count"] > (50 * per_page):
                    print("WARNING:The searchcode API only allows the download from up to 50 pages!")
                    print("\tSo this script will only be able to get {0} of the {1} files!"
                          .format(50 * per_page, src["count"]))
    except HTTPError as e:
        print("ERROR:Could not get data from {0}: {1}".format(url, repr(e)))


parser = argparse.ArgumentParser(
    description='Download Java Code from searchcode, that contain the given searchquery.')
parser.add_argument('query', metavar='Q', nargs=1, help="the searchquery.")
parser.add_argument('-i', '--info', action='store_true', help="only get the number of results.")
parser.add_argument('-r', '--repo', nargs=1, type=int, default=[-1],
                    help="specify the repo to search by giving the repo_id.")
args = parser.parse_args()

handle_input(args.query[0], args.info, args.repo[0], 20)
