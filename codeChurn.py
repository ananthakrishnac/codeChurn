import subprocess
import os
import argparse
import dateparser
from pathlib import Path
import pydriller as git
from pydriller.domain.commit import Commit as CommitModsText
import git as gitf
import xxhash 
import sqlite3
from subprocess import call, STDOUT
import configparser
import mysql
import ast
from DBObserverInterface import DBObserverInterface
from SQLiteClassImpl import SQLiteDBImpl
from MySqlClassImpl import MySqlDBImpl
from JSONClassImpl import JSONImpl


# For enabling logs, toggle the below lines
# DEBUG = True
DEBUG = False

# CHeck if this is a rerun or already exists
fileExists = False

# Author dictionary
authorDict = {}
fileDict = {}
commitDict = {}
nameAliasDict = {}


# Bits and ppieces of this code has been picked up from gitcodechurn.py file by Francis LaclA, released under MIT license
# (https://github.com/flacle/truegitcodechurn)
# This was further enhanced using pydriller instead of parsing py logs manually

# Helper code
# -----------------------------------------------------------------------------
def dir_path(path):
    ''' dir_path: Check if the given path is a directory or not
        https://stackoverflow.com/a/54547257
    '''
    if os.path.isdir(path):
        return path
    else:
        raise argparse.ArgumentTypeError(path + " is not a valid path.")

def remove_prefix(text, prefix):
    ''' remove_prefix: Need to remove prefix text
        https://stackoverflow.com/a/16891418
    '''
    if text.startswith(prefix):
        return text[len(prefix):]
    return text  # or whatever

def remove_postfix(text, postfix):
    ''' remove_postfix: Need to remove postfix text
    '''
    raise NotImplementedError;
    return
# -----------------------------------------------------------------------------

# Main
def main():
    
    '''
    python codeChurn.py

    dir is very important. This code uses dir path for marking / mapping files, commits and authors. So, if you run this code from two different
    directory structures, while the output may be same, you cannot compare files between them as the hashes would be different.

    Date format supported: YYYY[-MM[-DD]], DD/MM/YYYY, DD-MM-YYYY, etc.
    
    '''

    parser = argparse.ArgumentParser(
        description = 'Compute true git code churn to understand tech debt.',
        usage       = 'python codechurn.py -config=config.ini [-aliasnames=dbnamesalias.ini]',
        epilog      = ''
    )
    parser.add_argument(
        '-config',
        metavar='',
        default='config.ini',
        type = str,
        help = 'config.ini file describing required parameters'
    )

    parser.add_argument(
        '-aliasnames',
        metavar='',
        default='dbnamesalias.ini',
        type = str,
        help = 'config.ini file describing name aliases'
    )

    args = parser.parse_args()
    configFile=''
    
    configArg  = args.config
    if configArg : 
        configFile  = remove_prefix(configArg, 'config=')
        
    aliasNamesArg = args.aliasnames
    aliasFile = ''
    if aliasNamesArg:
        aliasFile = remove_prefix(aliasNamesArg, 'aliasnames=')

    configini = configparser.ConfigParser()
    configini.optionxform = str                    #https://stackoverflow.com/questions/19359556/configparser-reads-capital-keys-and-make-them-lower-case
    configini.read([configFile, aliasFile])

    for sections in configini.sections():
        print(sections)
    
    projectarg = configini['args']['project']
    pathArg    = ast.literal_eval(configini['args']['dir'])
    afterArg   = configini['args']['after']
    beforeArg  = configini['args']['before']
    authorArg  = ast.literal_eval(configini['args']['author'])
    exdirArg   = ast.literal_eval(configini['args']['exgitrepo'])
    exCommitsArg = ast.literal_eval(configini['args']['exCommits'])

    if not pathArg or pathArg == "" or len(pathArg) == 0:
        return;

    # for the positionals we remove the prefixes
    after = None
    afterDate = None
    before = None
    beforeDate = None
    author = authorArg
    dirPath = None
    exDirPath = None

    if afterArg : 
        after  = remove_prefix(afterArg, 'after=')
        afterDate = dateparser.parse(afterArg)
    if beforeArg:
        before  = remove_prefix(beforeArg, 'before=')
        beforeDate = dateparser.parse(beforeArg) #.date()
    
    exDirPath = exdirArg
    
    #dirPath = remove_prefix(pathArg, 'dir=') 
    dirPath = pathArg

    #if DEBUG == True:
        #print(after,before,author,dir_path(dirPath))
        #print(getAllGITDirectories(dirPath))

    if configini.has_section('namealias'):
        for item in configini.items('namealias'):
            print(repr(item[0]))
            nameAliasDict[xxhash.xxh32(item[0].strip()).intdigest()] = item[1].strip()

    dirs = getAllGITDirectories(dirPath)

    #NOTE: If there are .gitmodules present, then python git crashes for unknown reasons. Hence just remove the .gitmodules for now.. I dont have time to investigate this at the moment.
    removegitmodules(dirPath)

    dbObject = DBObserverInterface()
    
    if configini.getboolean('SQLite','enableSqlite') == True:
        dbname = str(projectarg)+str(configini['SQLite']['DBName'])
        dbObject.attach(SQLiteDBImpl(dbname))
    
    if configini.getboolean('MySql','enableMySql') == True:
        # The below comment enables naming mysql table as ProjectNameTableName. This helps in separating tables. But if doing it on many projects, need indirect reference.
        # On the other hand, for the moment, I'm adding new column which has project name - which may help separating projects.
        #dbname = str(projectarg)+str(configini['MySql']['DBname'])
        dbname = str(configini['MySql']['DBName'])
        dbObject.attach(MySqlDBImpl(name=dbname, project=str(projectarg), user=configini['MySql']['user'], password=configini['MySql']['password'], host=configini['MySql']['host']))

    if configini.getboolean("JSON", 'enableJSON') == True:
        dbname = str(projectarg)
        dbObject.attach(JSONImpl(name=dbname, authorfile=configini['JSON']['authorfile'], \
                        commitfile=configini['JSON']['commitsfile'], renamefiles=configini['JSON']['renamesfile'], \
                            files=configini['JSON']['filesfile'], filechurn=configini['JSON']['churnfile']))
        

    dbObject.createDB()
    
    commits = parseGitStructureForAllDirs(afterDate, beforeDate, author, dirPath, dirs, exDirPath, exCommitsArg, nameAliasDict, dbObject)

    return

def find_repo(path):
    "Find repository root from the path's parents"
    for path in Path(path).parents:
        # Check whether "path/.git" exists and is a directory
        git_dir = path / ".git"
        if git_dir.is_dir():
            return path

def is_git_repo(path):
    if call(["git", "branch"], stderr=STDOUT, stdout=open(os.devnull, 'w')) != 0:
        return True
    return False

def get_proc_out(command, dir):
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=dir,
        shell=True
    )
    return process.communicate()[0].decode("utf-8")


def getAllGITDirectories(startdirs):
    ''' getAllGITDirectories: recurse from the given startdir and fetch path for all internal git directories
                         useful in repo analysis. Repo is usually collection of git repos, instead of
                         giving individual paths, this code fetches all git repos from the start path
                         The paths are relative to "Current working directory"
    '''
    
    
    dirs = []
    
    # In case of android repo, there are some git folders which are maintained under .repo folder.
    # i.e.
    # ROOT/.repo/repo/folder1.git (contains info, objects, refs, ... folder of git)
    # ROOT/actual_source_code/folder1/.git --> ROOT/.repo/repo/folder1.git (soft linked)
    # 
    # Alternatively, if we use the followlinks, there were some loops in the folder, which caused it to loop infinitely
    # If we can ensure no loops, then os.walk(followlinks=True) should work
    # there are other solutions, need to check
    
    #WINDOWS TEST
    #return (["..\project_name"])        ## DELETE THIS
    ##########
    
    for startdir in startdirs:
        command = 'find ' + str(startdir) + ' -name .git -prune'
        results = get_proc_out(command, os.getcwd()).splitlines()
        if DEBUG == True:
            print ("GIT REPOS: \n")
            print (results)
        
        #for dirpath, dirnames, _ in os.walk(startdir, topdown=False):
        for dirpath in results:
            dirnames = os.listdir(dirpath)
            if Path(dirpath).parts[-1] == ".git" and set(['info', 'objects', 'refs']).issubset(set(dirnames)):
                pPath = Path(dirpath)
                #print(pPath.parent.absolute())         # Absolute path
                if DEBUG == True:
                    print(pPath.parent.absolute())         # Absolute path
                    print(pPath.parent.relative_to('.'))    # Relative path, this should be sufficient
                dirs.append(pPath.parent.relative_to('.'))

    # print(dirs)                
    return dirs

def removegitmodules(startdirs):
    for startdir in startdirs:
        command = 'find ' + startdir + ' -name .gitmodules -prune'
        results = get_proc_out(command, os.getcwd()).splitlines()
        print("GIT MODULES::: ",results)
        for item in results:
            os.rename(item, item+"--old")
    return

def parseGitStructureForAllDirs(after, before, author, baseDir, dirs, excludeDirs, exCommitsArg, nameAliasDict, dbObject):

    # Navigate the entire repos.. i.e. list of all git repositories.
    # One way to "probably" get around the relative path problem is to change working dir and use that path from corresponding git repo
    # but, if there exists foldernames / path with same names, then there is a possbility of hash value clash.

    ## TODO: Need to rework on folder logic.
    #os.chdir(baseDir)
    #cwdPath, cwd = os.path.split(os.getcwd())
    #print(cwd)

    #cur = dbCon.cursor()

    for dirP in dirs:
        print(dirP)

        exclude = False        
        for exdir in excludeDirs:
            if str(dirP).find(exdir) != -1: 
                exclude = True
        if exclude == True:
            continue
        
        dbObject.DBBeginTransaction()
        
        #print(str(dirP))
        for commit in git.Repository(str(dirP), since = after, to = before, only_authors=author, num_workers=1).traverse_commits():

            #print(commit.hash)
            #continue
            
            excludeCommit = False        
            for exCommit in exCommitsArg:
                if str(commit.hash).startswith(exCommit) == True or str(commit.hash) == exCommit: 
                    excludeCommit = True
            if excludeCommit == True:
                continue
            
            if DEBUG == True:
                #https://pydriller.readthedocs.io/en/latest/commit.html
                print(commit.hash, commit.author.name, commit.committer_date, commit.files, commit.lines, commit.insertions, commit.deletions)

            authorHash = xxhash.xxh32(str(commit.author.name).strip()).intdigest()
            #print(str(commit.author.name), authorHash)

            # TODO: If this is a rerun, we need to know the authorHash and other Hashes saved.
            # This means, while the DB is present, there is no hash dict saved, meaning, it will fail in INSERTs below
            
            # if an entry exists in authorDict and is the names match, we do not need to anything.
            if ( authorHash in authorDict and authorDict[authorHash] == commit.author.name):
                pass
            # But if an entry exists, but names do not match, we need to change the hashing algo due to hash clash
            # and if an entry does not exist, then just add it to DB
            else:
                # We could have used INSERT OR IGNORE .. but I want it to fail if hash and name does not match.
                # There is no sense in reading the values from DB and checking it. Maintaining a dictionary is faster
                l_authorName = str(commit.author.name).strip()
                if(xxhash.xxh32(l_authorName).intdigest() in nameAliasDict):
                    l_authorName = nameAliasDict[xxhash.xxh32(l_authorName).intdigest()]
                    print("Name matched: " + l_authorName)
                authorDict[authorHash] = l_authorName
                try:
                    # cur.execute("INSERT INTO AUTHORS VALUES (?,?)", (str(commit.author.name), authorHash))
                    dbObject.insertAuthors(l_authorName, authorHash)
                except Exception as e:
                    print({e})
                    print("ERROR::: COULD NOT INSERT AUTHOR - Dumping author data ------------------ ")
                    print(authorDict)
                    print(str(commit.author.name), authorHash)
                    print("------------------------------------------------------------------------- ")

            commitHash = xxhash.xxh32(commit.hash).intdigest()
            commitDict[commitHash] = commit.hash
            try:
                l_authorName = str(commit.author.name).strip()
                if(xxhash.xxh32(str(commit.author.name).strip()).intdigest() in nameAliasDict):
                    l_authorName = nameAliasDict[xxhash.xxh32(str(commit.author.name).strip()).intdigest()]
                dbObject.insertCommits(commitHash, str(commit.hash), authorHash, l_authorName, commit.files, commit.insertions, commit.deletions, commit.committer_date, str(dirP))

            except:
                print("ERROR::: COULD NOT INSERT COMMITS - Dumping commit data ------------------ ")
                print(commitDict)
                print(commit.hash, commitHash, str(dirP), commit.author)
                print("------------------------------------------------------------------------- ")
                # This case has actually happened !! I see that there are two repos with same commitId.
                # two repos Repo1 and Repo2 both show same commitID during project creation. But this is probably due to linking .git folder under .repo/repo
                # and both may have pointed to same empty repo.
                # But in any case, I've checked the case which i've seen. If any of you see this in field, DO NOT IGNORE. Verify it (and if possible, provide a solution)


            try:
                for mFile in commit.modified_files:
                    #if DEBUG == True:
                        #https://pydriller.readthedocs.io/en/latest/modifiedfile.html#modifiedfile-toplevel
                    #    print(mFile.old_path, mFile.new_path, mFile.filename,mFile.change_type.name, mFile.added_lines, mFile.deleted_lines, mFile.nloc, mFile.complexity)
                
                    # TODO: INSTEAD of hardcoding MODIFY/ADD/DELETE/RENAME, move it to a different structure and refer them from pydriller
                    # Cases:
                    # No change in file:
                    if mFile.change_type.name == "MODIFY":
                        filePath = mFile.old_path
                        
    
                    # File added / copied to new location:
                    if mFile.change_type.name == "ADD" or mFile.change_type.name == "COPY":
                        filePath = mFile.new_path
                        
    
                    # File deleted:
                    if mFile.change_type.name == "DELETE":
                        filePath = mFile.old_path
                        
    
                    # File renamed / moved:
                    if mFile.change_type.name == "RENAME":
                        filePath = mFile.new_path
                        dbObject.insertRenames(commitHash, xxhash.xxh32(mFile.old_path).intdigest(), xxhash.xxh32(mFile.new_path).intdigest())
                        
                    if mFile.change_type.name == "UNKNOWN":
                        #print("WARNING::: Ignoring unknown type:", mFile.change_type, " FILE: OLD, new", mFile.old_path, mFile.new_path)
                        if mFile.new_path is not None:
                            filePath = mFile.new_path
                        elif mFile.old_path is not None:
                            filePath = mFile.old_path
                        else:
                            print("WARNING::: Ignoring unknown type:", mFile.change_type, " FILE: OLD, new", mFile.old_path, mFile.new_path)
                            continue
                    
                    if not (mFile.change_type.name == "MODIFY" or mFile.change_type.name == "ADD" or \
                            mFile.change_type.name == "DELETE" or mFile.change_type.name == "RENAME" or \
                            mFile.change_type.name == "COPY" or mFile.change_type.name == "UNKNOWN"):
                        print("WARNING::: Ignoring not recognized type:", mFile.change_type, " FILE: OLD, new", mFile.old_path, mFile.new_path)
                        continue
                    
    
                    filePathHash = xxhash.xxh32(filePath).intdigest()
                    if(filePathHash in fileDict and fileDict[filePathHash] == filePath):
                        pass
                    else:
                        fileDict[filePathHash] = filePath
                        try:
                            dbObject.insertFiles(filePath, filePathHash)
                        except:
                            print("ERROR::: COULD NOT INSERT FILENAMES - Dumping file data ------------------ ")
                            print(fileDict)
                            print(filePath, filePathHash, mFile.change_type.name)
                            print("------------------------------------------------------------------------- ")
                    
    
                    # nloc = int(subprocess.check_output("wc -l " + filePath).split()[0]) # mFile.nloc
                    nloc = mFile.nloc
                    complexity = mFile.complexity
    
                    try:
                        if (nloc == None):
                            nloc = 0
                        if (complexity == None):
                            complexity = -1
                        dbObject.insertFileChurn(commitHash, filePathHash, mFile.change_type.name, mFile.added_lines, mFile.deleted_lines, nloc, complexity, filePath, commit.committer_date ,str(commit.author.name))
                        #https://stackoverflow.com/questions/11856983/why-is-git-authordate-different-from-commitdate
                        #print(commitHash, filePathHash, mFile.added_lines, mFile.deleted_lines, nloc, mFile.complexity, filePath, commit.committer_date, commit.author_date ,str(commit.author.name))
                    except:
                        print("ERROR::: COULD NOT INSERT FILECHURN - Dumping filechurn data ------------------ ")
                        print(commitHash, filePathHash, mFile.added_lines, mFile.deleted_lines, nloc, mFile.complexity, filePath, commit.committer_date ,str(commit.author.name))
                        print("------------------------------------------------------------------------- ")
            except Exception as e:
                print("ERROR::: while looping through modified files ------------------ ")
                print({e})


        dbObject.DBCommitTransaction()
    dbObject.DBFinalize()
    return


if __name__ == '__main__':
    main()
