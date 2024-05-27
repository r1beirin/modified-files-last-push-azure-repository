import zipfile
import argparse
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication

def getAllPushes(gitClient, projectName, repoID):
    return gitClient.get_pushes(project=projectName, repository_id=repoID, top=1)

def getGitClient(connection):
    return connection.clients.get_git_client()

def createConnection(personalAccessToken, organizationURL):
    credentials = BasicAuthentication('', personalAccessToken)
    return Connection(base_url=organizationURL, creds=credentials)

def getModifiedFromPush(pushes, gitClient, projectName, repoID):
    modifiedFiles = set()
    deletedFiles = set()
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
                    if not change['item'].get('isFolder'):
                        nameFile = change['item']['path'].lstrip('/')
                        # Added and modified files
                        if change['changeType'] != 'delete':
                            print(f'Arquivo modificado: {nameFile}')
                            modifiedFiles.add(nameFile)        
                        
                        # Deleted files
                        if change['changeType'] == 'delete':
                            print(f'Arquivo deletado: {nameFile}')
                            deletedFiles.add(nameFile)  
    
    return modifiedFiles, deletedFiles

def createFromModifiedFiles(fileName, modifiedFiles):
    with zipfile.ZipFile(fileName, 'w') as zipf:
        for filePath in modifiedFiles:
            zipf.write(filePath)

def createFromDeletedFiles(fileName, deletedFiles):
    with open(fileName, 'w') as file:
        for filePath in deletedFiles:
            file.write(filePath + '\n')

def argumentParser():
    parser = argparse.ArgumentParser('This script create a zip with the modified or deleted files in last push from Azure Repo.')
    parser.add_argument('-pat', '--pat', help='Personal Access Token', required=True)
    parser.add_argument('-ourl', '--orgurl', help='Organization URL', required=True)
    parser.add_argument('-pn', '--projectname', help='Project Name', required=True)
    parser.add_argument('-ri', '--repoid', help='Repository ID', required=True)
    return parser

def main():
    args = argumentParser().parse_args()
    personalAccessToken = args.pat
    organizationURL = args.orgurl
    projectName = args.projectname
    repoID = args.repoid

    connection = createConnection(personalAccessToken, organizationURL)

    gitClient = getGitClient(connection)

    pushes = getAllPushes(gitClient, projectName, repoID)

    if not pushes:
        return
    
    modifiedFiles, deletedFiles = getModifiedFromPush(pushes, gitClient, projectName, repoID)

    if modifiedFiles and deletedFiles:
        createFromModifiedFiles('modified_files.zip', modifiedFiles)
        createFromDeletedFiles('deleted_files.txt', deletedFiles)

    elif modifiedFiles:
        createFromModifiedFiles('modified_files.zip', modifiedFiles)

    elif deletedFiles:
        createFromDeletedFiles('deleted_files.txt', deletedFiles)

if __name__ == '__main__':
    main()