-- schema creation

-- username: root
-- password: Pass@123

/*
1) log in to MySQL with userid / pwd
2) Select the icon "Create a New Schema"
3) Give a suitable name. eg: "press" -> Click "Apply"
	3.1) Alternatively, use the following script:
	CREATE SCHEMA press;
	
	3.2) Refresh the Schema to view the new entry
	
4) Create a new table to store the routing info
	create table routing_info

	create table routing_info
	( hid int primary key, headline varchar(100), category varchar(30), email varchar(50), score int );
	
5) Check if the table is created
	SELECT * FROM routing_info;
	
*/ 