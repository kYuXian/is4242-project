import steamspypi
import json
import csv
import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import math
from textwrap import dedent
import traceback

#API pull from steam spy for AppID,Name
def get_appid_name_spy():
    result = {'x':[]}
    for i in range(0,100):
        API_1 = requests.get("https://steamspy.com/api.php?request=all&page={}".format(i))
        try:
            data = json.loads(API_1.text)
        except:
            print("No more games to load")
            break
        for item in data:
            result['x'].append(data[item])
        print("written_page {}".format(i))
        time.sleep(30)
    df = pd.DataFrame(result['x'])
    df.to_csv('steam_app.csv',encoding = 'utf-8-sig')
    print(df)

#can parameterise the write_index function for all 3 cases
#track index for steam_spy
def write_index(index):
    f = open("index.txt","w")
    f.write(str(index))
    f.close()

    
#track index for steam_store_api
def write_index_store(index):
    f = open("index_store.txt","w")
    f.write(str(index))
    f.close()

#track index for steam_store_dlc
def write_index_store_dlc(index):
    f = open("index_store_dlc.txt","w")
    f.write(str(index))
    f.close()

#API pull from steam_spy_all_data
def get_data_steam_spy(batch,start):
    result = {'x':[]}
    end = start + batch
    dfi = pd.read_csv('steam_app.csv')
    if end > len(dfi):
        end = len(dfi)
    try:
        df_continue = pd.read_csv('steam_games.csv',index_col=0)
    except:
        df_continue = pd.DataFrame()
        pass
    for i in range(start,end):
        item = dfi.iloc[i]['appid']
        try:
            API_2 = requests.get("https://steamspy.com/api.php?request=appdetails&appid={}".format(item))
            game_detail = API_2.json()
        except KeyboardInterrupt:
            raise KeyboardInterrupt()
        except:
            raise ConnectionError("Connection refused from Web API, Will sleep for 5 mins and resume")
        result['x'].append(game_detail)
    df_combine = pd.DataFrame(result['x'])
    if len(df_continue) != 0:
        df_new = pd.concat([df_continue,df_combine],ignore_index=True)
    else:
        df_new = df_combine
    print("Writing index {} to {} into csv file...".format(start,end - 1))
    df_new.to_csv('steam_games.csv',encoding = 'utf-8-sig')
    write_index(end)
    print("Finished Writing...")

#API for steam_store games
def get_data_steam_store_games(batch,start):

    n_cols = [
    'type', 'name', 'steam_appid', 'required_age', 'is_free', 'controller_support',
    'dlc','developers',
    'publishers','price_overview',
    'platforms', 'metacritic','categories','release_date']
    
    col_remove = ['detailed_description','about_the_game','short_description','header_image','website',
                  'legal_notice','drm_notice','ext_user_account_notice','demos','packages','package_groups',
                  'screenshots','movies','achievements','support_info','background','content_descriptors',
                  'recommendations','pc_requirements', 'mac_requirements','linux_requirements','fullgame',
                  'background_raw','reviews','supported_languages','genres']

    result = {'x':[]}
    end = start + batch
    dfi = pd.read_csv('steam_app.csv')
    if end > len(dfi):
        end = len(dfi)
    try:
        df_continue = pd.read_csv('steam_store.csv',index_col=0)
    except:
        df_continue = pd.DataFrame()
        pass
    for i in range(start,end):
        item_d = dfi.iloc[i]['name']
        item = dfi.iloc[i]['appid']
        while True:
            try:
                API_2 = requests.get("https://store.steampowered.com/api/appdetails?appids={}".format(item))
                if API_2.json()[str(item)]['success'] == True:
                    game_detail = API_2.json()[str(item)]['data']
                    break
                else:
                    game_detail = {}
                    for i in n_cols:
                        if i == 'steam_appid':
                            game_detail[i] = item
                        elif i == 'name':
                            game_detail[i] = item_d
                        else:
                            game_detail[i] = None
                    print(item)
                    break
            except KeyboardInterrupt:
                raise KeyboardInterrupt("Stopped Programme")
            except:
                print("Connection refused...")
                print("sleeping for {}s".format(60))
                time.sleep(60)
                print("retrying for appid: {}".format(item))
                continue
        for item in col_remove:
            if item in game_detail.keys():
                game_detail.pop(item)
        result['x'].append(game_detail)
        count = 0
    df_combine = pd.DataFrame(result['x'])
    if len(df_continue) != 0:
        df_new = pd.concat([df_continue,df_combine],ignore_index=True)
    else:
        df_new = df_combine
    print("Writing index {} to {} into csv file...".format(start,end - 1))
    df_new.to_csv('steam_store_dlc_full.csv',encoding = 'utf-8-sig')
    write_index_store(end)
    print("Finished Writing...")
    

#API pull from steam_store for DLCS
#can parameterise the http request
#can be parameterised
def get_data_steam_store(batch,start):

    n_cols = [
    'type', 'name', 'steam_appid', 'required_age', 'is_free', 'controller_support',
    'dlc','developers',
    'publishers','price_overview',
    'platforms', 'metacritic','categories','release_date']
    
    col_remove = ['detailed_description','about_the_game','short_description','header_image','website',
                  'legal_notice','drm_notice','ext_user_account_notice','demos','packages','package_groups',
                  'screenshots','movies','achievements','support_info','background','content_descriptors',
                  'recommendations','pc_requirements', 'mac_requirements','linux_requirements','fullgame',
                  'background_raw','reviews','supported_languages','genres']

    result = {'x':[]}
    end = start + batch
    dfi = pd.read_csv('steam_store_dlc.csv')
    if end > len(dfi):
        end = len(dfi)
    try:
        df_continue = pd.read_csv('steam_store_dlc_full.csv',index_col=0)
    except:
        df_continue = pd.DataFrame()
        pass
    for i in range(start,end):
        item = dfi.iloc[i]['appid']
        while True:
            try:
                API_2 = requests.get("https://store.steampowered.com/api/appdetails?appids={}".format(item))
                if len(API_2.text) == 0 or API_2.json()[str(item)]['success'] == False:
                    game_detail = {}
                    for i in n_cols:
                        if i == 'steam_appid':
                            game_detail[i] = item
                        else:
                            game_detail[i] = None
                    print(item)
                    break    
                else: #API_2.json()[str(item)]['success'] == True:
                    game_detail = API_2.json()[str(item)]['data']
                    break
                '''
                else:
                    game_detail = {}
                    for i in n_cols:
                        if i == 'steam_appid':
                            game_detail[i] = item
                        else:
                            game_detail[i] = None
                    print(item)
                    break
                '''
            except KeyboardInterrupt:
                raise KeyboardInterrupt("Stopped Programme")
            except:
                print("Connection refused...")
                print("sleeping for {}s".format(60))
                time.sleep(60)
                print("retrying for appid: {}".format(item))
                continue
        for item in col_remove:
            if item in game_detail.keys():
                game_detail.pop(item)
        result['x'].append(game_detail)
        count = 0
    df_combine = pd.DataFrame(result['x'])
    if len(df_continue) != 0:
        df_new = pd.concat([df_continue,df_combine],ignore_index=True)
    else:
        df_new = df_combine
    print("Writing index {} to {} into csv file...".format(start,end - 1))
    df_new.to_csv('steam_store_dlc_full.csv',encoding = 'utf-8-sig')
    write_index_store_dlc(end)
    #write_index_store(end)
    print("Finished Writing...")

#batch process steam_spy
#can parameterise the main_process
def main_process(batch):
    df_L = len(pd.read_csv('steam_app.csv'))
    while True:
        f = open("index.txt","r")
        index = int(f.read())
        print(index)
        if df_L == index:
            print("Finished pulling every data")
            break
        else:
            try:
                get_data_steam_spy(batch,index)
            except KeyboardInterrupt:
                print("Stopped Programme")
                break
            except ConnectionError:
                print("Going to Sleep for {}s".format(301))
                time.sleep(301)
                print("Woken up, retrying data pulling")
                continue

#batch process steam_store_dlc
def main_process_store(batch):
    df_L = len(pd.read_csv('steam_store_dlc.csv'))
    #df_L = len(pd.read_csv('steam_app.csv'))
    while True:
        #index_store.txt
        f = open("index_store_dlc.txt","r")
        index = int(f.read())
        print(index)
        if df_L == index:
            print("Finished pulling every data")
            break
        else:
            try:
                get_data_steam_store(batch,index)
            except KeyboardInterrupt:
                print("Killing Programme...")
                break
            
def main_process_store_games(batch):
    df_L = len(pd.read_csv('steam_app.csv'))
    while True:
        f = open("index_store.txt","r")
        index = int(f.read())
        print(index)
        if df_L == index:
            print("Finished pulling every data")
            break
        else:
            try:
                get_data_steam_store_games(batch,index)
            except KeyboardInterrupt:
                print("Killing Programme...")
                break

def pull_dlc():
    df = pd.read_csv('steam_store.csv')
    x = {'x':[]}
    for i in range(0,len(df)):
        ls = df.iloc[i]['dlc']
        if isinstance(ls,str):
            res = ls.strip('][').split(', ')
            x['x'].extend(res)
    df_combine = pd.DataFrame(x['x'],columns=['appid'])
    df_combine.to_csv('steam_store_dlc.csv',encoding = 'utf-8-sig')
    
#pull_dlc()

#main
def main():
    while True:
        process = input("1: Pull AppId/Name from steam spy \n" +
                      "2: Pull full data from steam spy \n" +
                      "3: Pull full data DLCS from steam store \n" +
                      "4: Pull full data Games from steam store \n" +
                      "Any other input: Exit Program \n")
        if process == "2":
            while True:
                batch = input("Enter Batch to pull: ")
                if not batch.isdigit():
                    continue
                else:
                    print("Starting data pulling...")
                    main_process(int(batch))
                    break
            print("Finished pulling All Data...")
        elif process == "3":
            while True:
                batch = input("Enter Batch to pull: ")
                if not batch.isdigit():
                    continue
                else:
                    print("Starting data pulling...")
                    main_process_store(int(batch))
                    break
            print("Finished pulling Data...")
        elif process == "4":
            while True:
                batch = input("Enter Batch to pull: ")
                if not batch.isdigit():
                    continue
                else:
                    print("Starting data pulling...")
                    main_process_store_games(int(batch))
                    break
            print("Finished pulling Data...")
        elif process == "1":
            print("Starting data pulling...")
            get_appid_name_spy()
            print("Finished pulling Data...")
            break
        else:
            print("Exiting program...")
            break
        
main()
