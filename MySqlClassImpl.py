import DBObserverInterface
import os
import mysql.connector
import re
import xxhash

class MySqlDBImpl:
    
    db_postfix = "_db"
    _name_ = 'default'
    _dbname_ = _name_ + db_postfix
    _connection_ = None
    user = ''
    password = ''    
    host = ''
    project = 'default'
    
    def __init__(self, user='', password='', host='', name='default', project='default'):
        self._name_ = name
        self._dbname_ = self._name_ + self.db_postfix
        self.user = user
        self.password = password
        self.host = host
        self.project = project
        

    def name(self):
        return self._dbname_
    
    def createDB(self):
        try:           
            self._connection_ = mysql.connector.connect(user=self.user, password=self.password, host=self.host)
            cursor = self._connection_.cursor()
            # cursor.execute("SHOW DATABASES")
            # for dbs in cursor:
            #     print(dbs[0])
            
            ##### REMOVE THIS ####
            #cursor.execute("DROP DATABASE IF EXISTS " + self._dbname_)
            ######################            
            
            cursor.execute("CREATE DATABASE IF NOT EXISTS " + self._dbname_)
            cursor.execute("USE " + self._dbname_)
            
            cursor.execute("CREATE TABLE IF NOT EXISTS AUTHORS (projectName TINYTEXT, projectNameHash INTEGER, author TINYTEXT, authorHashVal NUMERIC NOT NULL, PRIMARY KEY(authorHashVal, projectNameHash))")              
            
            cursor.execute("CREATE TABLE IF NOT EXISTS FILENAMES (projectName TINYTEXT, projectNameHash INTEGER, filename MEDIUMTEXT, fileHashVal NUMERIC NOT NULL, PRIMARY KEY(fileHashVal, projectNameHash))")
            
            cursor.execute("CREATE TABLE IF NOT EXISTS FILECHURN (projectName TINYTEXT, projectNameHash INTEGER,\
                           commitHash NUMERIC, \
                           filehashVal NUMERIC, \
                           changeType TINYTEXT, \
                           countAddedLines INTEGER, \
                           countDeletedLines INTEGER, \
                           countFileLOC INTEGER, \
                           fileComplexity INTEGER, \
                           filenamePath MEDIUMTEXT, \
                           filename TINYTEXT, \
                           date datetime, \
                           countDeletedLinesNeg INTEGER, \
                           countNewlyAdded INTEGER, \
                           countChurn INTEGER, authorName TINYTEXT, \
                           PRIMARY KEY(commitHash,filehashVal, projectNameHash) )")
            
            cursor.execute("CREATE TABLE IF NOT EXISTS RENAMEDFILES (projectName TINYTEXT, commitHash NUMERIC, oldfilePathHashN NUMERIC, newfilePathHash NUMERIC)")
            
            cursor.execute("CREATE TABLE IF NOT EXISTS COMMITS ( projectName TINYTEXT, projectNameHash INTEGER,\
                           commitHash NUMERIC, \
                           commitString TINYTEXT NOT NULL, \
                           authorHash NUMERIC, \
                           authorName TINYTEXT, \
                           countFilesChanged INTEGER, \
                           linesAdded INTEGER, \
                           linesDeleted	INTEGER, \
                           commitDate datetime, \
                           linesDeletedNeg INTEGER, \
                           linesNewlyAdded INTEGER, \
                           linesChurn INTEGER, \
                           gitRepo MEDIUMTEXT, \
                           gitRepoName TINYTEXT, \
                           PRIMARY KEY(commitHash, projectNameHash))"
                           )

            
            # cursor.execute("CREATE TABLE IF NOT EXISTS AUTHORS (projectName TINYTEXT, author TINYTEXT, authorHashVal NUMERIC NOT NULL, PRIMARY KEY(authorHashVal))")              
            
            # cursor.execute("CREATE TABLE IF NOT EXISTS FILENAMES (projectName TINYTEXT, filename MEDIUMTEXT, fileHashVal NUMERIC NOT NULL, PRIMARY KEY(fileHashVal))")
            
            # cursor.execute("CREATE TABLE IF NOT EXISTS FILECHURN (projectName TINYTEXT, \
            #                commitHash NUMERIC, \
            #                filehashVal NUMERIC, \
            #                changeType TINYTEXT, \
            #                countAddedLines INTEGER, \
            #                countDeletedLines INTEGER, \
            #                countFileLOC INTEGER, \
            #                fileComplexity INTEGER, \
            #                filenamePath MEDIUMTEXT, \
            #                filename TINYTEXT, \
            #                date datetime, \
            #                countDeletedLinesNeg INTEGER, \
            #                countNewlyAdded INTEGER, \
            #                countChurn INTEGER, authorName TINYTEXT, \
            #                PRIMARY KEY(commitHash,filehashVal) )")
            
            # cursor.execute("CREATE TABLE IF NOT EXISTS RENAMEDFILES (projectName TINYTEXT, commitHash NUMERIC, oldfilePathHashN NUMERIC, newfilePathHash NUMERIC)")
            
            # cursor.execute("CREATE TABLE IF NOT EXISTS COMMITS ( projectName TINYTEXT, \
            #                commitHash NUMERIC, \
            #                commitString TINYTEXT NOT NULL, \
            #                authorHash NUMERIC, \
            #                authorName TINYTEXT, \
            #                countFilesChanged INTEGER, \
            #                linesAdded INTEGER, \
            #                linesDeleted	INTEGER, \
            #                commitDate datetime, \
            #                linesDeletedNeg INTEGER, \
            #                linesNewlyAdded INTEGER, \
            #                linesChurn INTEGER, \
            #                gitRepo MEDIUMTEXT, \
            #                gitRepoName TINYTEXT, \
            #                PRIMARY KEY(commitHash))"
            #                )
    
        except Exception as e:
            print("Exeption creating DB: ", {e})
            self._connection_ = None
        
        return
    
    def beginTransaction(self):
        cur = self._connection_.cursor()
        cur.execute("BEGIN")
        return
    
    def commitTransaction(self):
        cur = self._connection_.cursor()
        cur.execute("COMMIT")       # END TRANSACTION should work as well
        return
    
    def insertAuthors(self, name, hashValue):
        cur = self._connection_.cursor()
    
        try:
            cur.execute("INSERT IGNORE INTO AUTHORS (projectName, projectNameHash, author, authorHashVal) VALUES (%s, %s, %s, %s)", (self.project, xxhash.xxh32(self.project).intdigest(), name, hashValue))
        except Exception as e:
            print("MySql: could not insert author " + name + " " + str(hashValue))
            print({e})
            raise
        return
       
    def insertCommits(self, commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, committer_date, dirP):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT IGNORE INTO COMMITS (projectName, projectNameHash, commitHash, commitString, authorHash, authorName, countFilesChanged, linesAdded, linesDeleted, linesDeletedNeg, linesNewlyAdded, linesChurn, commitDate, gitRepo, gitRepoName) \
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,  %s, %s, %s, %s, %s)", 
                            (self.project, xxhash.xxh32(self.project).intdigest(), commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, -1 * deletionsCount, insertionsCount - deletionsCount, insertionsCount + deletionsCount ,committer_date, dirP, re.split(r'[:|\\|\| |/|,]',dirP)[-1]))
        except Exception as e:
            print("MySql: could not insert commits:  " ,
                  commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, -1 * deletionsCount, insertionsCount - deletionsCount, insertionsCount + deletionsCount ,committer_date, dirP, re.split(r'[:|\\|\| |/|,]',dirP)[-1])
            print({e})
            raise
        return

    
    def insertRenames(self, commitHash, oldPathHash, newPathHash):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT IGNORE INTO RENAMEDFILES (projectName, commitHash , oldfilePathHashN ,	newfilePathHash	) VALUES (%s, %s, %s, %s)", (self.project, commitHash, oldPathHash, newPathHash) )
        except Exception as e:
            print("MySql: could not insert renames: ", commitHash, oldPathHash, newPathHash)
            print({e})
            raise
        return


    def insertFiles(self, filePath, filePathHash):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT IGNORE INTO FILENAMES (projectName, projectNameHash, filename, fileHashVal) VALUES (%s, %s, %s, %s)", (self.project, xxhash.xxh32(self.project).intdigest(), filePath, filePathHash))
        except Exception as e:
            print("MySql: could not insert files: ", filePath, filePathHash)
            print({e})
            raise
        return
    
    def insertFileChurn(self, commitHash, filePathHash, changeType, added_lines, deleted_lines, nloc, complexity, filename, date, authorName):
        cur = self._connection_.cursor()
        try:
            cur.execute("INSERT IGNORE INTO FILECHURN (projectName, projectNameHash, commitHash, filehashVal, changeType, countAddedLines, countDeletedLines, countFileLOC, fileComplexity, filenamePath, filename, date, countDeletedLinesNeg, countNewlyAdded, countChurn, authorName) \
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                        (self.project, xxhash.xxh32(self.project).intdigest(), commitHash, filePathHash, changeType, added_lines, deleted_lines, nloc, complexity, filename, re.split(r'[:|\\|\| |/|,]',filename)[-1], date, -1 * deleted_lines, added_lines - deleted_lines, added_lines + deleted_lines, authorName))
        except Exception as e:
            print("MySql: could not insert filechurn: " ,commitHash, filePathHash, changeType, added_lines, deleted_lines, nloc, complexity, filename, re.split(r'[:|\\|\| |/|,]',filename)[-1], date, -1 * deleted_lines, added_lines - deleted_lines, added_lines + deleted_lines, authorName)
            print({e})
            raise
        return
    
        
    def finalize(self):
        pass
