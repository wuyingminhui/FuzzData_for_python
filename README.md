FuzzData_for_python
===================

FuzzParser Class:
Initialize the instance data generated a Fuzz analytic DataSet.
	 version () function:
	 Return FuzzData version.
	 
	 append (BoneType) function:
	 BoneType FuzzData for a variety of data types, append the data type to generate the data inserted into the Fuzz's last column.
	 
	 setvalconnect (string) function:
	 Set the link of the parameters between the data types, the default is "&."
	 
	 delete (item) function:
	 Parameters item is FuzzData data type name. Function will remove Fuzz generated data.
	 
	 auto () function:
	 According to append the data list automatically generated FuzzData test cases. Return to list, the list of test cases for the FuzzData.
	 
	 exportToCSV () function:
	 Generate output into a csv file for the test case list . 

BoneString Class:
Initialize a Fuzz data type of String.
	setIllegalChars (chars) function:
	Set the Fuzz illegal characters of String data type.
	
	setvalname (valname) function:
	Set the variable name of the data type .
	
	setMinSize (minsize) function:
	Set the minimum length of the data type.
	
	setMaxSize (maxsize) function:
	Set the maximum length of the data type. The default is 10 .
	
	setConnector (connector) function:
	Set the variable name and value of the connectors between the.
	
	setTerminator (terminator) function:
	Set the variable character whick is the end of the data type .

BoneChar Class:
Initialize a Fuzz data type of Char.
	setvalname (valname) function:
	Set the variable name of the data type .
	
	setMinSize (minsize) function:
	Set the minimum length of the data type.
	
	setMaxSize (maxsize) function:
	Set the maximum length of the data type. The default is 10 .
	
	setConnector (connector) function:
	Set the variable name and value of the connectors between the.
	
	setTerminator (terminator) function:
	Set the variable character whick is the end of the data type .

BoneFloat Class:
Initialize a Fuzz data type of Float.
	The default maximum value: the value of 2 ^ 32
	The default minimum value is: negative value of 2 ^ 32
	
	setvalname (valname) function:
	Set the variable name of the data type .
	
	setMinSize (minsize) function:
	Set the minimum length of the data type.
	
	setMaxSize (maxsize) function:
	Set the maximum length of the data type. The default is 10 .
	
	setConnector (connector) function:
	Set the variable name and value of the connectors between the.
	
	setTerminator (terminator) function:
	Set the variable character whick is the end of the data type .

BoneLongInt Class:
Initialize a Fuzz data type of Long.
	The default maximum value is: 2 ^ 32 -1
	The default minimum value is: 0
	
	setSigned () function
	The default maximum value is: 31 th power minus 2
	The default minimum value is: 2 -1 31 th
	
	setvalname (valname) function:
	Set the variable name of the data type .
	
	setMinSize (minsize) function:
	Set the minimum length of the data type.
	
	setMaxSize (maxsize) function:
	Set the maximum length of the data type. The default is 10 .
	
	setConnector (connector) function:
	Set the variable name and value of the connectors between the.
	
	setTerminator (terminator) function:
	Set the variable character whick is the end of the data type .
	
BoneInteger Class:
Initialize a Fuzz data type of Integer.
	The default maximum value is: 2 ^ 16 -1
	The default minimum value is: 0
	setSigned () function:
	The default maximum value is: 15 th power minus 2
	The default minimum value is: 2 -1 15 th
	
	setvalname (valname) function:
	Set the variable name of the data type .
	
	setMinSize (minsize) function:
	Set the minimum length of the data type.
	
	setMaxSize (maxsize) function:
	Set the maximum length of the data type. The default is 10 .
	
	setConnector (connector) function:
	Set the variable name and value of the connectors between the.
	
	setTerminator (terminator) function:
	Set the variable character whick is the end of the data type .
