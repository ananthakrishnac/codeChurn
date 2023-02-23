class DBObserverInterface:
    
    _observers = []
    
    def __init__(self):
        self._observers = []
        

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)
    
    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except:
            pass

    def createDB(self):
        for observer in self._observers:
            observer.createDB()
        
    def DBBeginTransaction(self):
        for observer in self._observers:
            observer.beginTransaction()
    
    def DBCommitTransaction(self):
        for observer in self._observers:
            observer.commitTransaction()
        
            
    def insertAuthors(self, name, hashValue):
        for observer in self._observers:
            observer.insertAuthors(name, hashValue)
    
    def insertCommits(self, commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, committer_date, dirP):
        for observer in self._observers:
            observer.insertCommits(commitHash, commitID, authorHash, authorName, filesCount, insertionsCount, deletionsCount, committer_date, dirP)
    
    def insertFiles(self, filePath, filePathHash):
        for observer in self._observers:
            observer.insertFiles(filePath, filePathHash)
    

    def insertRenames(self, commitHash, oldPathHash, newPathHash):
        for observer in self._observers:
            observer.insertRenames(commitHash, oldPathHash, newPathHash)
    
    def insertFileChurn(self, commitHash, filePathHash, added_lines, deleted_lines, nloc, complexity, filename, date, authorName):
        for observer in self._observers:
            observer.insertFileChurn(commitHash, filePathHash, added_lines, deleted_lines, nloc, complexity, filename, date, authorName)
