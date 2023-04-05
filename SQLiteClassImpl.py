import DBObserverInterface
import os
import sqlite3
import re
from datetime import datetime

class SQLiteDBImpl:
    
    db_postfix = ".db"
    _name_ = 'default'
    _dbname_ = _name_ + db_postfix
    _connection_ = None
    
    def __init__(self, name='default'):
        self._name_ = name
        dt_string = datetime.now().strftime("_%Y_%m_%d_%H_%M")
        self._dbname_ = self._name_ + dt_string + self.db_postfix
    
    def name(self):
        return self._dbname_
    
    def createDB(self):
        if(os.path.isfile(self._dbname_) == True):
            fileExists = True
            ################################################################################
            ##             REMOVE THIS LINE BELOW                                         ##
            os.remove(self._dbname_) 
            ################################################################################
            
        con = sqlite3.connect(self._dbname_);
        cur = con.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS AUTHORS(author STRING ASC, authorHashVal NUMERIC NOT NULL PRIMARY KEY)")
        cur.execute("CREATE TABLE IF NOT EXISTS COMMITS(commitHash NUMERIC PRIMARY KEY, commitString STRING NOT NULL, \
                    authorHash NUMERIC, authorName STRING, countFilesChanged INTEGER, \
                    linesAdded INTEGER, linesDeleted INTEGER, \
                    linesDeletedNeg INTEGER, linesNewlyAdded INTEGER, linesChurn INTEGER, \
                    commitDate datetime, gitRepo STRING, gitRepoName STRING)")
        cur.execute("CREATE TABLE IF NOT EXISTS FILENAMES(filename STRING ASC, fileHashVal NUMERIC NOT NULL PRIMARY KEY)")
        cur.execute("CREATE TABLE IF NOT EXISTS RENAMEDFILES(commitHash NUMERIC, oldfilePathHash NUMERIC, newfilePathHash NUMERIC)")
        cur.execute("CREATE TABLE IF NOT EXISTS FILECHURN(commitHash NUMERIC, filehashVal NUMERIC, \
                          changeType STRING, \
                          countAddedLines INTEGER, countDeletedLines INTEGER, \
                          countFileLOC INTEGER, \
                          fileComplexity INTEGER, \
                          filenamePath STRING, filename STRING, date datetime, countDeletedLinesNeg INTEGER, countNewlyAdded INTEGER, \
                          countChurn INTEGER, authorName STRING, \
                          PRIMARY KEY(commitHash, filehashVal) \
                      )")

        con.commit()
        self._connection_ = con
        return
    
    def beginTransaction(self):
        cur = self._connection_.cursor()
        cur.execute("BEGIN TRANSACTION")
        return
    
    def commitTransaction(self):
        cur = self._connection_.cursor()
        cur.execute("COMMIT")       # END TRANSACTION should work as well
        return

    def insertAuthors(self, name, hashValue):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT INTO AUTHORS VALUES (?,?)", (name, hashValue))
        except Exception as e:
            print("SQLite: could not insert author " + name + " " + str(hashValue))
            print({e})
            raise
        return
    
    def insertCommits(self, commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, committer_date, dirP):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT OR IGNORE INTO COMMITS VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                            (commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, -1 * deletionsCount, insertionsCount - deletionsCount, insertionsCount + deletionsCount ,committer_date, dirP, re.split(r'[:|\\|\| |/|,]',dirP)[-1]))
        except Exception as e:
            print("SQLite: could not insert commits: " ,
                  commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, -1 * deletionsCount, insertionsCount - deletionsCount, insertionsCount + deletionsCount ,committer_date, dirP, re.split(r'[:|\\|\| |/|,]',dirP)[-1])
            
            print({e})
            raise
        return
    

    def insertRenames(self, commitHash, oldPathHash, newPathHash):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT OR IGNORE INTO RENAMEDFILES VALUES (?, ?, ?)", ( commitHash, oldPathHash, newPathHash) )
        except Exception as e:
            print("SQLite: could not insert renames: ", commitHash, oldPathHash, newPathHash)
            print({e})
            raise
        return
    
    
    def insertFiles(self, filePath, filePathHash):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT OR IGNORE INTO FILENAMES VALUES (?, ?)", (filePath, filePathHash))
        except Exception as e:
            print("SQLite: could not insert files: ", filePath, filePathHash)
            print({e})
            raise
        return
            
    def insertFileChurn(self, commitHash, filePathHash, changeType, added_lines, deleted_lines, nloc, complexity, filename, date, authorName):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT OR IGNORE INTO FILECHURN VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (commitHash, filePathHash, changeType, added_lines, deleted_lines, nloc, complexity, filename, re.split(r'[:|\\|\| |/|,]',filename)[-1], date, -1 * deleted_lines, added_lines - deleted_lines, added_lines + deleted_lines, authorName))
        except Exception as e:
            print("SQLite: could not insert filechurn: ", commitHash, filePathHash, changeType, added_lines, deleted_lines, nloc, complexity, filename, re.split(r'[:|\\|\| |/|,]',filename)[-1], date, -1 * deleted_lines, added_lines - deleted_lines, added_lines + deleted_lines, authorName)
            print({e})
            raise
        return
    
    def finalize(self):
        pass
