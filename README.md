# codeChurn

GOAL: This code intends to create a visualization for code churn.

INSTALLATION:
1. Create a virtual environment
python3 -m venv /path/to/virtual_env_folder
source /path/to/virtual_env_folder/bin/activate

2. git clone https://github.com/ananthakrishnac/codeChurn.git
 
3. pip3 install -r requirements.txt

RUN:

python3 codeChurn.py -config=config.ini

Date accepted in most formats, i've tested DD/MM/YYYY, YYYY, YYYY-MM-DD.


REQUIREMENTS:

1. Identify all git folders in a repo (i.e. a starting directory)
2. Loop through all the identified git repos and get commits, file info, author, churn info, ...
3. Save it in a DB (at the moment, sqlite)
4. Enable partial updates
5. Enable/disable DB updates
6. speed up the process by using multiple threads / processes
7. Enable data visualization of various parameters
8. Enable specifying DB names & Path
9. Enable folder(s) exclusion
... To be added later on...

BASED ON:

1. The initial piece (and some bits and pieces) of the code is picked up from gitcodechurn.py file by Francis LaclA, released under MIT license
(https://github.com/flacle/truegitcodechurn)

2. The git parsing uses pydriller library
https://github.com/ishepard/pydriller

3. Lot of Stackoverflow Q&A


NOTES: 

v0.0.5:
1. Revert v0.0.4 -- has issues when working with MySql. But need to implement Multithreading to reducing parsing time from minutes to subminute.
2. Added Json Support

v0.0.4:
1. Implemented multiprocessing to speed up parsing. - Will need to change implementation to make best use of all available cores.

v0.0.3:
1. (v0.0.2: line 5) Added support for JSON
2. (v0.0.1: Line 8) So with this release now supporting MySql, Sqlite and JSON
Remaining TODOs from below (and may be additional ones):
3. Data visualization support in PowerBI / Tableau / etc.
4. Improve logging
5. Speed up DB writes and data saves
6. Support Partial DB updates
7. Error handling - This piece of code just works the way I intended it to. I've not done any explicit error handling. 
As a quote goes, "Every day, man is making bigger and better "fool-proof" things and everyday nature is making bigger and better fools. So far, Nature is winning".
The objective of this code is not to make fool-proof functioning program, but simply to extract data to DB and visulize/analyze it further. I'll be concentrating more on functionality rather than making it fool proof.
If you encounter a issue - please fix it as you deem fit.


v0.0.2

1. (v0.0.1: line 2) Data conflicts are when the same base git repo is pointed by different repo. Otherwise, things seem fine
2. (v0.0.1: line 5) Moved it all to config.ini file, exclude dir (repo) supported, but cannot exclude single folder e.g. doc folder under main repo but consider the rest.
3. (v0.0.1: line 6) Multiple authors supported
4. (v0.0.1: line 7) Project Name added to argument and table
5. (v0.0.1: line 8) MySQL, SQLite supported - JSON still TODO
6. (v0.0.2:) You may be thinking why are so many redundant datafiedls added in database. Reason: It is much easier (and faster) to just use the data and project, rather than calculate during Visualization
7. (v0.0.2:) Can enable / disable individual DBs (MySql, Sqlite, JSON) as needed
8. (v0.0.2: NOTE - IMPORTANT) We cannot use mFile.nloc to compare git lines added/deleted. nloc strips all comments, blanks, etc and counts lines, whereas git added/deleted counts it all. Therefore it is not apples to apples comparison.
9. (v0.0.2: NOTE - IMPORTANT) authorDate and commitDate can be different if commits are amended or merged, else they could be same/similar.

v0.0.1

1. Too slow - need to work on speeding up the process
2. There are still some conflicts, not sure why  -- v0.0.2: Kinda know, but dont know if that is all
3. Need to do data visualization
4. Need to improve logging.. the dumps are mostly developer dumps, need to clean them up.
5. exdir and updateDB flags not functional
6. I've tested only single author name, need to add list support.
7. Add project name to argument
8. Support MYSQL/SQLITE/JSON via interfaces
9. Try to do Data processing as much as possible here, instead of data processing tool to speed up visualization
