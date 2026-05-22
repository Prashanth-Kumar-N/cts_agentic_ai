use employee;
-- select * from emp;
-- select * from emp_personal_details;
-- select * from emp_address; 
-- select * from emp_salary;

-- update emp set gender = 'F' where length(gender) <= 0;
-- Q1
select * from emp where department = 'Finance' and gender = 'F';

-- Q2
select * from emp_personal_details where children > 3;

-- Q3
select * from emp_address where state = "CA" and zip > 90000;

-- Q4
select * from emp_salary where joining_bonus > 7000 and grade = "G6" and bonus_perc > 10 and base > 100000;

