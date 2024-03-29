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

1. Install MySql and configure properly - if need to write to MySql
2. SQLite - Should support out of the box without special configuration
3. JSON - should support out of box
4. Tested only on Ubuntu Linux -- probably will need considerable modifications to run on windows
5. If any further support - MariaDB or any other tool si needed, then just register observer and support functions in DBObserver .. that should abstract much of the implementation with DB details.

