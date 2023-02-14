import subprocess
import shlex
import os
import argparse
import dateparser
import datetime
from pathlib import Path
import pydriller as git
from pydriller.domain.commit import Commit as CommitModsText
import git as gitf
from pyhash import fnv1_32 
import sqlite3
from subprocess import call, STDOUT

# For enabling logs, toggle the below lines
# DEBUG = True
DEBUG = False

# CHeck if this is a rerun or already exists
fileExists = False

# Create a single hasher function, to ensure consitency across all hashes.
hasher = fnv1_32()

# Author dictionary
authorDict = {}
fileDict = {}
commitDict = {}

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

def openDB():
    if(os.path.isfile("codeChurn.db") == True):
        fileExists = True
        ################################################################################
        ##             REMOVE THIS LINE BELOW                                         ##
        os.remove("codeChurn.db") 
        ################################################################################
        
    con = sqlite3.connect("codeChurn.db");
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS AUTHORS(author STRING ASC, authorHashVal NUMERIC NOT NULL PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS COMMITS(commitHash NUMERIC PRIMARY KEY, commitString STRING NOT NULL, authorHash NUMERIC, countFilesChanged INTEGER, linesAdded INTEGER, linesDeleted INTEGER, commitDate datetime, gitRepo STRING)")
    cur.execute("CREATE TABLE IF NOT EXISTS FILENAMES(filename STRING ASC, fileHashVal NUMERIC NOT NULL PRIMARY KEY)")
    cur.execute("CREATE TABLE IF NOT EXISTS RENAMEDFILES(commitHash NUMERIC, oldfilePathHash NUMERIC, newfilePathHash NUMERIC)")
    # cur.execute("CREATE TABLE IF NOT EXISTS FILECHURN(commitid NUMERIC, filehash NUMERIC, \
    #                  added INTEGER, deleted INTEGER, \
    #                  PRIMARY KEY(commitid, filehash), \
    #                  FOREIGN KEY (filehash) REFERENCES FILENAMES(hashVal) \
    #                  FOREIGN KEY (commitid) REFERENCES COMMITS(commits) \
    #              )")
    # cur.execute("CREATE TABLE IF NOT EXISTS FILECHURN(commitHash NUMERIC, filehash NUMERIC, \
    #                   added INTEGER, deleted INTEGER, \
    #                   PRIMARY KEY(commitHash, filehash), \
    #                   FOREIGN KEY (filehash) REFERENCES FILENAMES(hashVal) \
    #                   FOREIGN KEY (commitHash) REFERENCES COMMITS(commitHash) \
    #               )")

    cur.execute("CREATE TABLE IF NOT EXISTS FILECHURN(commitHash NUMERIC, filehashVal NUMERIC, \
                      countAddedLines INTEGER, countDeletedLines INTEGER, \
                      PRIMARY KEY(commitHash, filehashVal) \
                  )")

    con.commit()
    return con

# Main
def main():
    '''
    usage : 'python gitcodechurn.py -dir="path" -after="YYYY[-MM[-DD]]" -before="YYYY[-MM[-DD]]" -author="flacle" -exdir="path" -updateDB=True',
    
    dir is very important. This code uses dir path for marking / mapping files, commits and authors. So, if you run this code from two different
    directory structures, while the output may be same, you cannot compare files between them as the hashes would be different.

    Date format supported: YYYY[-MM[-DD]], DD/MM/YYYY, DD-MM-YYYY, etc.
    '''
    parser = argparse.ArgumentParser(
        description = 'Compute true git code churn to understand tech debt.',
        usage       = 'python codechurn.py -dir="path" -after="YYYY[-MM[-DD]]" -before="YYYY[-MM[-DD]]" -author="flacle" -exdir="path" -updateDB=True',
        # Other formats supported DD/MM/YYYY.
        epilog      = 'Feel free to fork at or contribute on: https://github.com/flacle/truegitcodechurn'
    )
    parser.add_argument(
        '-after',
        metavar='',
        type = str,
        help = 'search after a certain date, in YYYY[-MM[-DD]] format'
    )
    parser.add_argument(
        '-before',
        metavar='',
        type = str,
        help = 'search before a certain date, in YYYY[-MM[-DD]] format'
    )
    parser.add_argument(
        '-author',
        metavar='',
        type = str,
        help = 'an author (non-committer), leave blank to scope all authors'
    )
    parser.add_argument(
        '-dir',
        type = str,
        default = '',
        help = 'the Git repository root directory to be included',
        required=True
    )
    parser.add_argument(
        '-exdir',
        metavar='',
        type = str,
        default = '',
        help = 'the Git repository subdirectory to be excluded'
    )
    parser.add_argument(
        '-updateDB',
        metavar='',
        type = bool,
        default = False,
        help = 'create or update status in DB for future use'
    )

    args = parser.parse_args()

    afterArg  = args.after
    beforeArg = args.before
    authorArg = args.author
    pathArg    = args.dir
    exdirArg  = args.exdir
    updateDBArg = args.updateDB

    if not pathArg or pathArg == "":
        return;


    # for the positionals we remove the prefixes
    after = None
    afterDate = None
    before = None
    beforeDate = None
    author = None
    dirPath = None
    exDirPath = None

    if afterArg : 
        after  = remove_prefix(afterArg, 'after=')
        afterDate = dateparser.parse(afterArg) #.date()
        # afterDate.strftime("%Y-%m-%d")
    if beforeArg:
        before  = remove_prefix(beforeArg, 'before=')
        beforeDate = dateparser.parse(beforeArg) #.date()
        # print(beforeDate.strftime("%Y-%m-%d"))
    if authorArg:
        author  = remove_prefix(authorArg, 'author=')
    
    dirPath = remove_prefix(pathArg, 'dir=')
    
    if exdirArg:
        exDirPath = remove_prefix(exdirArg, 'exdir=')

    #updateDB = remove_prefix(updateDB, 'updateDB=')

    if DEBUG == True:
        print(after,before,author,dir_path(dirPath))
        print(getAllGITDirectories(dirPath))

    dirs = getAllGITDirectories(dirPath)

    #NOTE: If there are .gitmodules present, then python git crashes for unknown reasons. Hence just remove the .gitmodules for now.. I dont have time to investigate this at the moment.
    removegitmodules(dirPath)

    con = openDB()

    commits = parseGitStructureForAllDirs(afterDate, beforeDate, author, dirPath, dirs, con)

    return

def find_repo(path):
    "Find repository root from the path's parents"
    for path in Path(path).parents:
        # Check whether "path/.git" exists and is a directory
        git_dir = path / ".git"
        if git_dir.is_dir():
            return path

def is_git_repo(path):
    #return subprocess.call(['git', '-C', path, 'status'], stderr=subprocess.STDOUT, stdout = open(os.devnull, 'w')) == 0

    # try:
    #     _ = gitf.Repo(path).git_dir
    #     return True
    # except:
    #     return False
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


def getAllGITDirectories(startdir):
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
    
    command = 'find ' + startdir + ' -name .git -prune'
    results = get_proc_out(command, os.getcwd()).splitlines()
    if DEBUG == True:
        print ("GIT REPOS: \n")
        print (results)
    
    #for dirpath, dirnames, _ in os.walk(startdir, topdown=False):
    for dirpath in results:
        dirnames = os.listdir(dirpath)
        if Path(dirpath).parts[-1] == ".git" and set(['info', 'objects', 'refs']).issubset(set(dirnames)):
            pPath = Path(dirpath)
            print(pPath.parent.absolute())         # Absolute path
            if DEBUG == True:
                print(pPath.parent.absolute())         # Absolute path
                print(pPath.parent.relative_to('.'))    # Relative path, this should be sufficient
            dirs.append(pPath.parent.relative_to('.'))
    return dirs

def removegitmodules(startdir):
    command = 'find ' + startdir + ' -name .gitmodules -prune'
    results = get_proc_out(command, os.getcwd()).splitlines()
    print("GIT MODULES::: ",results)
    for item in results:
        os.rename(item, item+"--old")
    return

def parseGitStructureForAllDirs(after, before, author, baseDir, dirs, dbCon):

    # Navigate the entire repos.. i.e. list of all git repositories.
    # One way to "probably" get around the relative path problem is to change working dir and use that path from corresponding git repo
    # but, if there exists foldernames / path with same names, then there is a possbility of hash value clash.

    ## TODO: Need to rework on folder logic.
    #os.chdir(baseDir)
    #cwdPath, cwd = os.path.split(os.getcwd())
    #print(cwd)

    cur = dbCon.cursor()

    for dirP in dirs:
        print(dirP)

        for commit in git.Repository(str(dirP), since = after, to = before, only_authors=author).traverse_commits():

            if DEBUG == True:
                #https://pydriller.readthedocs.io/en/latest/commit.html
                print(commit.hash, commit.author.name, commit.committer_date, commit.files, commit.lines, commit.insertions, commit.deletions)

            authorHash = hasher(commit.author.name)

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
                authorDict[authorHash] = commit.author.name
                try:
                    cur.execute("INSERT INTO AUTHORS VALUES (?,?)", (str(commit.author.name), authorHash))
                except:
                    print("ERROR::: COULD NOT INSERT AUTHOR - Dumping author data ------------------ ")
                    print(authorDict)
                    print(str(commit.author.name), authorHash)
                    print("------------------------------------------------------------------------- ")

            commitHash = hasher(commit.hash)
            commitDict[commitHash] = commit.hash
            try:
                cur.execute("INSERT INTO COMMITS VALUES (?, ?, ?, ?, ?, ?, ?, ?)", 
                            (commitHash, str(commit.hash), authorHash, commit.files, commit.insertions, commit.deletions, commit.committer_date, str(dirP)))
            except:
                print("ERROR::: COULD NOT INSERT COMMITS - Dumping commit data ------------------ ")
                print(commitDict)
                print(commit.hash, commitHash, str(dirP), commit.author)
                print("------------------------------------------------------------------------- ")
                # This case has actually happened !! I see that there are two repos with same commitId.
                # two repos Repo1 and Repo2 both show same commitID during project creation. But this is probably due to linking .git folder under .repo/repo
                # and both may have pointed to same empty repo.
                # But in any case, I've checked the case which i've seen. If any of you see this in field, DO NOT IGNORE. Verify it (and if possible, provide a solution)


            
            for mFile in commit.modified_files:
                if DEBUG == True:
                    #https://pydriller.readthedocs.io/en/latest/modifiedfile.html#modifiedfile-toplevel
                    print(mFile.old_path, mFile.new_path, mFile.filename,mFile.change_type.name, mFile.added_lines, mFile.deleted_lines, mFile.nloc, mFile.complexity)
            
                # TODO: INSTEAD of hardcoding MODIFY/ADD/DELETE/RENAME, move it to a different structure and refer them from pydriller
                # Cases:
                # No change in file:
                if mFile.change_type.name == "MODIFY":
                    filePath = mFile.old_path
                    

                # File added:
                if mFile.change_type.name == "ADD":
                    filePath = mFile.new_path
                    

                # File deleted:
                if mFile.change_type.name == "DELETE":
                    filePath = mFile.old_path
                    

                # File renamed / moved:
                if mFile.change_type.name == "RENAME":
                    filePath = mFile.new_path
                    cur.execute("INSERT INTO RENAMEDFILES VALUES (?, ?, ?)", ( commitHash, hasher(mFile.old_path), hasher(mFile.new_path)) )
                    
                if mFile.change_type == "COPY" or mFile.change_type == "UNKNOWN":
                    print("WARNING::: Ignoring unknown type:", mFile.change_type, " FILE: OLD, new", mFile.old_path, mFile.new_path)
                    continue

                filePathHash = hasher(filePath)
                if(filePathHash in fileDict and fileDict[filePathHash] == filePath):
                    #print("File found: ", filePath)
                    pass
                else:
                    fileDict[filePathHash] = filePath
                    try:
                        cur.execute("INSERT INTO FILENAMES VALUES (?, ?)", (filePath, filePathHash))
                    except:
                        print("ERROR::: COULD NOT INSERT FILENAMES - Dumping file data ------------------ ")
                        print(fileDict)
                        print(filePath, filePathHash, mFile.change_type.name)
                        print("------------------------------------------------------------------------- ")
                
                # cur.execute("INSERT INTO FILECHURN VALUES (?,?,?,?)", (commitHash, filePathHash, mFile.added_lines, mFile.deleted_lines))

                try:
                    cur.execute("INSERT INTO FILECHURN VALUES (?,?,?,?)", (commitHash, filePathHash, mFile.added_lines, mFile.deleted_lines))
                except:
                    print("ERROR::: COULD NOT INSERT FILECHURN - Dumping filechurn data ------------------ ")
                    #print(fileDict)
                    print(filePath, filePathHash, commitHash, commit.hash, commitHash, filePathHash, mFile.added_lines, mFile.deleted_lines)
                    print("------------------------------------------------------------------------- ")


            dbCon.commit()
    return


if __name__ == '__main__':
    main()
