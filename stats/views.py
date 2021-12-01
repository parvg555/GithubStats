from django.shortcuts import render
import json
import requests
import numpy as np
import pandas as pd
import requests 


def getdetails(username):
    credentials = json.load(open('credentials.json'))
    token = credentials['token']
    
    data  = requests.get('http://api.github.com/users/'+username,auth = (username,token))
    data = data.json()
    print(data)
    print("Name: {}".format(data['name']))
    print("Email: {}".format(data['email']))
    print("Location: {}".format(data['location']))
    print("Public repos: {}".format(data['public_repos']))
    print("Public gists: {}".format(data['public_gists']))
    print("About: {}".format(data['bio']))
    url = data['repos_url']
    page_no = 1
    repos_data = []
    while (True):
        response = requests.get(url, auth = (username,token))
        response = response.json()
        repos_data = repos_data + response
        repos_fetched = len(response)
        print("Total repositories fetched: {}".format(repos_fetched))
        if (repos_fetched == 30):
            page_no = page_no + 1
            url = data['repos_url'].encode("UTF-8") + '?page=' + str(page_no)
        else:
            break
    print(repos_data[0])
    repos_information = []
    for i, repo in enumerate(repos_data):
        data = []
        data.append(repo['id'])
        data.append(repo['name'])
        data.append(repo['description'])
        data.append(repo['created_at'])
        data.append(repo['updated_at'])
        data.append(repo['owner']['login'])
        data.append(repo['license']['name'] if repo['license'] != None else None)
        data.append(repo['has_wiki'])
        data.append(repo['forks_count'])
        data.append(repo['open_issues_count'])
        data.append(repo['stargazers_count'])
        data.append(repo['watchers_count'])
        data.append(repo['url'])
        data.append(repo['commits_url'].split("{")[0])
        data.append(repo['url'] + '/languages')
        repos_information.append(data)

    repos_df = pd.DataFrame(repos_information, columns = ['Id', 'Name', 'Description', 'Created on', 'Updated on', 'Owner', 'License', 'Includes wiki', 'Forks count', 'Issues count', 'Stars count', 'Watchers count','Repo URL', 'Commits URL', 'Languages URL'])
    for i in range(repos_df.shape[0]):
        response = requests.get(repos_df.loc[i, 'Languages URL'], auth = (username,token))
        response = response.json()
        print(i, response)
        if response != {}:
            languages = []
            for key, value in response.items():
                languages.append(key)
            languages = ', '.join(languages)
            repos_df.loc[i, 'Languages'] = languages
        else:
            repos_df.loc[i, 'Languages'] = ""    

    repos_df.to_csv('repositorydata.csv', index=False)

    commits_information = []
    for i in range(repos_df.shape[0]):
        url = repos_df.loc[i, 'Commits URL']
        page_no = 1
        while (True):
            response = requests.get(url, auth = (username,token))
            response = response.json()
            print("URL: {}, commits: {}".format(url, len(response)))
            for commit in response:
                commit_data = []
                commit_data.append(repos_df.loc[i, 'Id'])
                commit_data.append(commit['sha'])
                commit_data.append(commit['commit']['committer']['date'])
                commit_data.append(commit['commit']['message'])
                commits_information.append(commit_data)
            if (len(response) == 30):
                page_no = page_no + 1
                url = repos_df.loc[i, 'Commits URL'] + '?page=' + str(page_no)
            else:
                break
                
    commits_df = pd.DataFrame(commits_information, columns = ['Repo Id', 'Commit Id', 'Date', 'Message'])
    commits_df.to_csv('commits_info.csv', index = False)

def profile(request,username):
    #getdetails(username)
    
    return render(request,'profile.html',{
        'username':username,
    })

# https://www.analyticsvidhya.com/blog/2021/07/analyzing-popular-repositories-on-github/
# https://towardsdatascience.com/github-user-insights-using-github-api-data-collection-and-analysis-5b7dca1ab214