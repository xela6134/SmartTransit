## Querying database scripts

### Getting started
Before getting started you will need to create a .env file in the database directory with the content
specified in the resources discord channel. You should also make a .gitignore file if you don't have one
and add this file into the .gitignore.

### database_add_tuples.py
Using this script you can add tuples into the Users, Rides or Locations tables of the database.
Firstly, put all the tuples you want to add into some file seperated by commas like so. You
should also add this file to your .gitignore.

![alt text](../doccumentation/Screenshot%202025-03-15%20165706.png)

Now simply run the Python script and follow the prompts to specify the table you want to insert to and file name.

![alt text](../doccumentation/Screenshot%202025-03-15%20170238.png)

### querydB.py

Run this script to make queries to the database. Type 'end' to stop
the queries. Any 'select' queries will also display the results. As we can see, the tuples we added before are now in the database.

![alt text](../doccumentation/Screenshot%202025-03-15%20170254.png)

You can also put all the queries you want into a file and run a command like: "python3 querydB.py < queries.txt" to run all the queries seperated by new lines from the file. You should also have the last line of this file have the word 'exit' so the script can end.

### database_delete_tuples.py
coming soon....

### database_update_tuples.py
coming soon....