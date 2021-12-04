from django.shortcuts import redirect, render
import json
import requests
import numpy as np
import pandas as pd
import requests 
from datetime import date,datetime


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
        data.append(repo['html_url'])
        data.append(repo['commits_url'].split("{")[0])
        data.append(repo['url'] + '/languages')
        repos_information.append(data)
    repos_df = pd.DataFrame(repos_information, columns = ['Id', 'Name', 'Description', 'Created on', 'Updated on', 'Owner', 'License', 'Includes wiki', 'Forks_count', 'Issues_count', 'Stars_count', 'Watchers_count','Repo URL','html_url', 'Commits URL', 'Languages URL'])
    langdetails = {}
    for i in range(repos_df.shape[0]):
        response = requests.get(repos_df.loc[i, 'Languages URL'], auth = (username,token))
        response = response.json()
        print(i, response)
        if response != {}:
            languages = []
            for key, value in response.items():
                languages.append(str(str(key)+":"+str(value)))
                langdetails[key] = langdetails.get(key, 0) + value
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
                commit_data.append(commit['html_url'])
                commits_information.append(commit_data)
            if (len(response) == 30):
                page_no = page_no + 1
                url = repos_df.loc[i, 'Commits URL'] + '?page=' + str(page_no)
            else:
                break

    commits_df = pd.DataFrame(commits_information, columns = ['Repo Id', 'Commit Id', 'Date', 'Message','html_url'])
    commits_df.to_csv('commits_info.csv', index = False)

def profile(request,username):
    getdetails(username)
    #reads the csv file for the data extracted
    CommitsData= pd.read_csv("commits_info.csv")
    RepositoryData = pd.read_csv("repositorydata.csv")

    #data is converted into dataframes
    CommitsData = pd.DataFrame(CommitsData)
    RepositoryData = pd.DataFrame(RepositoryData)

    #creating url for streak api
    streak_url = "https://github-readme-streak-stats.herokuapp.com/?user="+username+"&theme=light&hide_border=true"
    
    #summing the various columns of tables to get the required data
    StarsEarned = RepositoryData['Stars_count'].sum()
    ForkCount = RepositoryData['Forks_count'].sum()
    IssuesCount = RepositoryData['Issues_count'].sum()
    WatchersCount = RepositoryData['Watchers_count'].sum()
    TotalCommits = CommitsData.shape[0]

    #extracting the details for repository and values for various languages
    language = []
    language_value = []
    language_details = {}
    for index,row in RepositoryData.iterrows():
      temp = str(row['Languages'])
      if temp == "nan":
        continue
      seprated_temp = temp.split(", ")
      for i in seprated_temp:
        temp2 = i.split(":")
        language_details[temp2[0]] = language_details.get(temp2[0],0) + int(temp2[1])
    sum = 0
    for key,value in language_details.items():
      sum+=value
    for key,value in language_details.items():
      language_details[key] = float((value/sum)*100)
    language_details = dict(sorted(language_details.items(), key=lambda item: item[1],reverse = True))
    i = 0
    for key,value in language_details.items():
      i+=1
      if i>5:
        break
      language.append(key)
      language_value.append(int(value))
    
    #extracting recent commits
    CommitsData = CommitsData.sort_values(by = ['Date'], ascending= False)
    RecentCommits = CommitsData[:3].to_dict('records')

    #extracting most famous repositories
    RepositoryData['Total'] = RepositoryData.iloc[:,8:12].sum(axis = 1, skipna = True)
    RepositoryData = RepositoryData.sort_values(by=['Total'],ascending = False)
    TopRepositories = RepositoryData[:3].to_dict('records')

    StarsPerLanguage = {}
    for index,row in RepositoryData.iterrows():
      temp = str(row['Languages']).split(", ")
      for item in temp:
        if item != 'nan':
          item = item.split(":")
          StarsPerLanguage[item[0]] = StarsPerLanguage.get(item[0], 0) + int(row['Stars_count'])
        break
    StarsPerLanguage = dict(sorted(StarsPerLanguage.items(), key = lambda x:x[1], reverse = True)[:5])
    StarsPerLanguage_Language = []
    StarsPerLanguage_Score = []
    for key,value in StarsPerLanguage.items():
      StarsPerLanguage_Language.append(key)
      StarsPerLanguage_Score.append(value)


    #extracting the data of commits this year
    CommitsThisYear = {'January':0,'February':0,'March':0,'April':0,'May':0,'June':0,'July':0,'August':0,'September':0,'October':0,'November':0,'December':0}
    todays_date = date.today()
    year = todays_date.year
    print(year)
    for index,row in CommitsData.iterrows():
      temp = datetime.strptime(row['Date'], "%Y-%m-%dT%H:%M:%SZ")
      if temp.year == todays_date.year:
        if temp.month == 12:
          CommitsThisYear['December'] = CommitsThisYear.get('December',0) + 1
        if temp.month == 11:
          CommitsThisYear['November'] = CommitsThisYear.get('November',0) + 1
        if temp.month == 10:
          CommitsThisYear['October'] = CommitsThisYear.get('October',0) + 1
        if temp.month == 9:
          CommitsThisYear['September'] = CommitsThisYear.get('September',0) + 1
        if temp.month == 8:
          CommitsThisYear['August'] = CommitsThisYear.get('August',0) + 1
        if temp.month == 7:
          CommitsThisYear['July'] = CommitsThisYear.get('July',0) + 1
        if temp.month == 6:
          CommitsThisYear['June'] = CommitsThisYear.get('June',0) + 1
        if temp.month == 5:
          CommitsThisYear['May'] = CommitsThisYear.get('May',0) + 1
        if temp.month == 4:
          CommitsThisYear['April'] = CommitsThisYear.get('April',0) + 1
        if temp.month == 3:
          CommitsThisYear['March'] = CommitsThisYear.get('March',0) + 1
        if temp.month == 2:
          CommitsThisYear['February'] = CommitsThisYear.get('February',0) + 1
        if temp.month == 1:
          CommitsThisYear['January'] = CommitsThisYear.get('January',0) + 1
      else:
        break
    CommitsThisYear_Months = []
    CommitsThisYear_Value = []
    for month,value in CommitsThisYear.items():
        CommitsThisYear_Months.append(month)
        CommitsThisYear_Value.append(value)
    context = {
        'username':username,
        'streak_url':streak_url,
        'StarsEarned':StarsEarned,
        'ForkCount':ForkCount,
        'IssuesCount':IssuesCount,
        'WatchersCount':WatchersCount,
        'TotalCommits':TotalCommits,
        'language':language,
        'language_value':language_value,
        'RecentCommits':RecentCommits,
        'TopRepositories': TopRepositories,
        'StarsPerLanguage_Language' : StarsPerLanguage_Language,
        'StarsPerLanguage_Score':StarsPerLanguage_Score,
        'CommitsThisYear_Months':CommitsThisYear_Months,
        'CommitsThisYear_Value':CommitsThisYear_Value,
    }
    return render(request,'profile.html',context)


def index(request):
    if request.method == "POST":
        username = request.POST.get('username')
        return redirect('profile',username)
    return render(request,'index.html',{})