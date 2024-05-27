import zipfile
import os
import argparse
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

def getAllPushes(gitClient, projectName, repoID):
    return gitClient.get_pushes(project=projectName, repository_id=repoID, top=1)

def getGitClient(connection):
    return connection.clients.get_git_client()

def createConnection(personalAccessToken, organizationURL):
    credentials = BasicAuthentication('', personalAccessToken)
    connection = Connection(base_url=organizationURL, creds=credentials)

    return connection

def getModifiedFromPush(pushes, gitClient, projectName, repoID, modifiedFiles, deletedFiles):
    lastPushID = pushes[0].push_id
    push_details = gitClient.get_push(project=projectName, repository_id=repoID, push_id=lastPushID)
    commits = push_details.commits

    for commit in commits:
        commitID = commit.commit_id

        commitDetails = gitClient.get_commit(project=projectName, repository_id=repoID, commit_id=commitID) 

        if commitDetails:
            changes = gitClient.get_changes(project=projectName, repository_id=repoID, commit_id=commitID)
            if changes:
                for change in changes.changes:
                    # Added and modified files
                    if not change['item'].get('isFolder') and change['changeType'] != 'delete':
                        nameFile = change['item']['path'].lstrip('/')
                        print(f'Arquivo modificado: {nameFile}')
                        modifiedFiles.add(nameFile)        
                    
                    # Deleted files
                    if not change['item'].get('isFolder') and change['changeType'] == 'delete':
                        nameFile = change['item']['path'].lstrip('/')
                        print(f'Arquivo deletado: {nameFile}')
                        deletedFiles.add(nameFile)  

def main():
    parser = argparse.ArgumentParser('This script create a zip with the modified files in last push from Azure Repo.')
    parser.add_argument('-pat', '--pat', help='Personal Access Token', required=True)
    parser.add_argument('-ourl', '--orgurl', help='Organization URL', required=True)
    parser.add_argument('-pn', '--projectname', help='Project Name', required=True)
    parser.add_argument('-ri', '--repoid', help='Repository ID', required=True)
    args = parser.parse_args()

    personalAccessToken = args.pat
    organizationURL = args.orgurl
    projectName = args.projectname
    repoID = args.repoid
    modifiedFiles = set()
    deletedFiles = set()

    connection = createConnection(personalAccessToken, organizationURL)

    gitClient = getGitClient(connection)

    pushes = getAllPushes(gitClient, projectName, repoID)

    if pushes:
        getModifiedFromPush(pushes, gitClient, projectName, repoID, modifiedFiles, deletedFiles)

    if modifiedFiles and deletedFiles:
        with zipfile.ZipFile("modified_files.zip", "w") as zipf:
            for filePath in modifiedFiles:
                zipf.write(filePath)

        with open('deleted_files.txt', 'w') as file:
            for filePath in deletedFiles:
                file.write(filePath + '\n')

    elif modifiedFiles:
        with zipfile.ZipFile("modified_files.zip", "w") as zipf:
            for filePath in modifiedFiles:
                zipf.write(filePath)

    elif deletedFiles:
        with open('deleted_files.txt', 'w') as file:
            for filePath in deletedFiles:
                file.write(filePath + '\n')

if __name__ == '__main__':
    main()