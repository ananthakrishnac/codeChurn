import json
import os
import re
import datetime

class JSONImpl:
    
    db_postfix = ".json"
    _name_ = 'default'
    _dbname_ = _name_ + db_postfix
    _connection_ = None
    jsonDictCommits = []
    jsonDictAuthors = []
    jsonDictFilenames = []
    jsonDictrenamedFiles = []
    jsonDictfilechurn = []
    
    def __init__(self, name='default', authorfile='authors', commitfile='commits', renamefiles='renames', files='files', filechurn='churn'):
        self._name_ = name
        self._dbname_ = self._name_ + self.db_postfix
        self._authorfile_ = self._name_+"_"+authorfile+self.db_postfix
        self._commitfile_ = self._name_+"_"+commitfile+self.db_postfix
        self._renamefile_ = self._name_+"_"+renamefiles+self.db_postfix
        self._filesfile_ = self._name_+"_"+files+self.db_postfix
        self._filechurnfile_ = self._name_+"_"+filechurn+self.db_postfix
    
    def name(self):
        return self._dbname_
    
    def createDB(self):
        if(os.path.isfile(self._dbname_) == True):
            fileExists = True
            ################################################################################
            ##             REMOVE THIS LINE BELOW                                         ##
            os.remove(self._dbname_) 
            ################################################################################
                
        
        return
    
    def beginTransaction(self):
        
        return
    
    def commitTransaction(self):
        
        return

    def insertAuthors(self, name, hashValue):
        
        Authors = {"author" : name, "authorHashVal" : hashValue}
        self.jsonDictAuthors.append(Authors)
        
        return
    
    def insertCommits(self, commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, committer_date, dirP):
        commits = {"commitHash": commitHash, "commitString" : commitID, "authorHash" : authorHash, "authorName" : authorName, "countFilesChanged" : filesCount, \
                   "linesAdded" : insertionsCount, "linesDeleted" : deletionsCount, "linesDeletedNeg" : -1*deletionsCount, "linesNewlyAdded" : insertionsCount - deletionsCount, \
                   "linesChurn" : insertionsCount + deletionsCount , "commitDate" : committer_date.isoformat(), "gitRepo" : dirP, "gitRepoName" : re.split(r'[:|\\|\| |/|,]',dirP)[-1]}
        self.jsonDictCommits.append(commits)
        
        return
    

    def insertRenames(self, commitHash, oldPathHash, newPathHash):
        renames = {"commitHash" : commitHash , "oldfilePathHashN" : oldPathHash, "newfilePathHash": newPathHash}
        self.jsonDictrenamedFiles.append(renames)
        return
    
    
    def insertFiles(self, filePath, filePathHash):
        files = {"filename" : filePath, "fileHashVal" : filePathHash}
        self.jsonDictFilenames.append(files)
        return
            
    def insertFileChurn(self, commitHash, filePathHash, added_lines, deleted_lines, nloc, complexity, filename, date, authorName):
        churn = {"commitHash" : commitHash, "filehashVal" : filePathHash, "countAddedLines" : added_lines, "countDeletedLines" : deleted_lines, 
                 "countFileLOC" : nloc, "fileComplexity" : complexity, "filenamePath" : filename, "filename" : re.split(r'[:|\\|\| |/|,]',filename)[-1], 
                 "date" : date.isoformat(), "countDeletedLinesNeg" : -1 * deleted_lines, "countNewlyAdded" : added_lines - deleted_lines, "countChurn" : added_lines + deleted_lines, "authorName" : authorName}
        self.jsonDictfilechurn.append(churn)
        return
    
    def finalize(self):
        
        with open(self._authorfile_, "w") as outfile:    # TODO: "a+" mode is preferred here
            proj = {"project":self._name_, "AuthorData":self.jsonDictAuthors}
            json.dump(proj, outfile)
            outfile.close()
            
        with open(self._commitfile_, "w") as outfile:    # TODO: "a+" mode is preferred here
            proj = {"project":self._name_, "CommitData":self.jsonDictCommits}
            json.dump(proj, outfile)
            outfile.close()
            
        with open(self._renamefile_, "w") as outfile:    # TODO: "a+" mode is preferred here
            proj = {"project":self._name_, "RenamefileData":self.jsonDictrenamedFiles}
            json.dump(proj, outfile)
            outfile.close()
            
        with open(self._filesfile_, "w") as outfile:    # TODO: "a+" mode is preferred here
            proj = {"project":self._name_, "filesData":self.jsonDictFilenames}
            json.dump(proj, outfile)
            outfile.close()

        with open(self._filechurnfile_, "w") as outfile:    # TODO: "a+" mode is preferred here
            proj = {"project":self._name_, "fileChurnData":self.jsonDictfilechurn}
            json.dump(proj, outfile)
            outfile.close()
