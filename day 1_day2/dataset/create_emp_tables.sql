-- Synthetic employee organization schema
-- drop table emp;

CREATE TABLE emp (
    emp_id VARCHAR(10) PRIMARY KEY,
    firstname VARCHAR(50) NOT NULL,
	lastname varchar(50),
	gender varchar(1),
	email varchar(100) not null,
    designation VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    reporting_manager VARCHAR(100),
    join_date varchar(10) NOT NULL
);

select * from emp;

-- drop table emp_personal_details;

CREATE TABLE emp_personal_details (
    emp_id VARCHAR(10) PRIMARY KEY,
    dob varchar(10) NOT NULL,
    spouse_name VARCHAR(100),
    children INT DEFAULT 0,
	education varchar(50),
    CONSTRAINT fk_emp_personal_emp
        FOREIGN KEY (emp_id) REFERENCES emp(emp_id)
);

select * from emp_personal_details;

-- drop table emp_address;
-- truncate table emp_address;
CREATE TABLE emp_address (
    emp_id VARCHAR(10) PRIMARY KEY,
	add1 varchar(75) not null,
	add2 varchar(75),
	state varchar(2),
	zip int,
    CONSTRAINT fk_emp_address_emp
        FOREIGN KEY (emp_id) REFERENCES emp(emp_id)
);

select * from emp_address; 

-- drop table emp_salary;

CREATE TABLE emp_salary (
    emp_id VARCHAR(10) PRIMARY KEY,
    base int,
	bonus_perc int,
	grade varchar(10),
	joining_bonus int,
    CONSTRAINT fk_em_salary_emp
        FOREIGN KEY (emp_id) REFERENCES emp(emp_id)
);

truncate table emp_salary;
select * from emp_salary;

