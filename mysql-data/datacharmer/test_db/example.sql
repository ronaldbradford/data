SET SQL_BIG_SELECTS=1;
SELECT gender, COUNT(*) AS total_employees
FROM employees
GROUP BY gender;
SELECT d.dept_name, COUNT(de.emp_no) AS total_employees
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
GROUP BY d.dept_name;
SELECT d.dept_name, e.first_name, e.last_name, dm.from_date, dm.to_date
FROM departments d
JOIN dept_manager dm ON d.dept_no = dm.dept_no
JOIN employees e ON dm.emp_no = e.emp_no;
SELECT d.dept_name, AVG(s.salary) AS avg_salary
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
JOIN salaries s ON de.emp_no = s.emp_no
GROUP BY d.dept_name;
SELECT t.title, COUNT(*) AS total_employees
FROM titles t
WHERE t.to_date IS NULL
GROUP BY t.title;
SELECT first_name, last_name, hire_date
FROM employees
WHERE hire_date < '2000-01-01';
SELECT d.dept_name, MAX(s.salary) AS highest_salary
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
JOIN salaries s ON de.emp_no = s.emp_no
GROUP BY d.dept_name;
SELECT e.first_name, e.last_name, d.dept_name, t.title
FROM employees e
JOIN dept_emp de ON e.emp_no = de.emp_no
JOIN departments d ON de.dept_no = d.dept_no
JOIN titles t ON e.emp_no = t.emp_no
WHERE t.to_date IS NULL;
SELECT first_name, last_name, hire_date, DATEDIFF(CURDATE(), hire_date) AS days_served
FROM employees
ORDER BY days_served DESC
LIMIT 10;
SELECT d.dept_name, SUM(s.salary) AS total_salary
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
JOIN salaries s ON de.emp_no = s.emp_no
GROUP BY d.dept_name;
SELECT
    d.dept_name,
    e.gender,
    COUNT(e.emp_no) AS gender_count,
    COUNT(e.emp_no) / total_dept.total_count * 100 AS gender_percentage
FROM
    employees e
JOIN
    dept_emp de ON e.emp_no = de.emp_no
JOIN
    departments d ON de.dept_no = d.dept_no
JOIN
    (SELECT dept_no, COUNT(emp_no) AS total_count
     FROM dept_emp
     GROUP BY dept_no) AS total_dept
     ON de.dept_no = total_dept.dept_no
GROUP BY
    d.dept_name, e.gender, total_dept.total_count
ORDER BY
    d.dept_name, e.gender;
SELECT d.dept_name, COUNT(de.emp_no) AS total_employees
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
GROUP BY d.dept_name WITH ROLLUP;
SELECT d.dept_name, e.gender, COUNT(e.emp_no) AS total_employees
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
JOIN employees e ON de.emp_no = e.emp_no
GROUP BY d.dept_name, e.gender WITH ROLLUP;
SELECT d.dept_name, SUM(s.salary) AS total_salary
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
JOIN salaries s ON de.emp_no = s.emp_no
GROUP BY d.dept_name WITH ROLLUP;
SELECT d.dept_name, e.gender, AVG(s.salary) AS avg_salary
FROM departments d
JOIN dept_emp de ON d.dept_no = de.dept_no
JOIN employees e ON de.emp_no = e.emp_no
JOIN salaries s ON e.emp_no = s.emp_no
GROUP BY d.dept_name, e.gender WITH ROLLUP;
SELECT
    CASE
        WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) < 30 THEN 'Under 30'
        WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) BETWEEN 30 AND 50 THEN '30-50'
        ELSE 'Above 50'
    END AS age_range,
    COUNT(*) AS total_employees
FROM employees
GROUP BY age_range;
SELECT
    CASE
        WHEN TIMESTAMPDIFF(YEAR, hire_date, CURDATE()) < 5 THEN 'Less than 5 years'
        WHEN TIMESTAMPDIFF(YEAR, hire_date, CURDATE()) BETWEEN 5 AND 10 THEN '5-10 years'
        ELSE 'More than 10 years'
    END AS tenure_range,
    COUNT(*) AS total_employees
FROM employees
GROUP BY tenure_range;
SELECT t.title, COUNT(*) AS total_employees
FROM titles t
GROUP BY t.title
ORDER BY total_employees DESC;
SELECT t.title, COUNT(*) AS current_employees
FROM titles t
WHERE t.to_date IS NULL
GROUP BY t.title
ORDER BY current_employees DESC;oSELECT e.emp_no, e.first_name, e.last_name, COUNT(t.title) AS num_titles
FROM employees e
JOIN titles t ON e.emp_no = t.emp_no
GROUP BY e.emp_no, e.first_name, e.last_name
HAVING num_titles > 1
ORDER BY num_titles DESC;
SELECT first_name, last_name, hire_date, DATEDIFF(CURDATE(), hire_date) AS days_served
FROM employees
ORDER BY days_served DESC
LIMIT 10;
SELECT
    CASE
        WHEN TIMESTAMPDIFF(YEAR, hire_date, CURDATE()) < 3 THEN 'Less than 3 years'
        WHEN TIMESTAMPDIFF(YEAR, hire_date, CURDATE()) BETWEEN 3 AND 7 THEN '3-7 years'
        ELSE 'More than 7 years'
    END AS retention_period,
    COUNT(*) AS total_employees
FROM employees
GROUP BY retention_period;
select min(birth_date), max(birth_date),count(*) from employees;
UPDATE employees
SET birth_date = DATE_ADD(
                    '1965-02-01',
                    INTERVAL FLOOR(RAND() * DATEDIFF('2006-01-01', '1965-02-01')) DAY
                )
WHERE birth_date BETWEEN '1952-02-01' AND '1965-02-01';
select min(birth_date), max(birth_date),count(*) from employees;
SELECT
    CASE
        WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) < 30 THEN 'Under 30'
        WHEN TIMESTAMPDIFF(YEAR, birth_date, CURDATE()) BETWEEN 30 AND 50 THEN '30-50'
        ELSE 'Above 50'
    END AS age_range,
    COUNT(*) AS total_employees
FROM employees
GROUP BY age_range;
SELECT
    CASE
        WHEN birth_date BETWEEN '1946-01-01' AND '1964-12-31' THEN 'Baby Boomers'
        WHEN birth_date BETWEEN '1965-01-01' AND '1980-12-31' THEN 'Generation X'
        WHEN birth_date BETWEEN '1981-01-01' AND '1996-12-31' THEN 'Millennials'
        WHEN birth_date BETWEEN '1997-01-01' AND '2012-12-31' THEN 'Generation Z'
        ELSE 'Unknown Generation'
    END AS generation,
    COUNT(*) AS total_employees
FROM employees
GROUP BY generation;
SELECT /* Palindromic Birth Dates */ emp_no, birth_date
FROM employees
WHERE REPLACE(birth_date, '-', '') = REVERSE(REPLACE(birth_date, '-', ''));
SELECT /* longest first names */ first_name, last_name, LENGTH(first_name) AS name_length
FROM employees
ORDER BY name_length DESC
LIMIT 10;
SELECT /* Most common first name letters */ LEFT(first_name, 1) AS first_letter, COUNT(*) AS total
FROM employees
GROUP BY first_letter
ORDER BY total DESC
LIMIT 5;
SELECT /* most departments worked */ de.emp_no, e.first_name, e.last_name, COUNT(DISTINCT de.dept_no) AS dept_count
FROM dept_emp de
JOIN employees e ON de.emp_no = e.emp_no
GROUP BY de.emp_no
ORDER BY dept_count DESC
LIMIT 10;
SELECT /* Shortest Tenure */ emp_no, first_name, last_name, hire_date, DATEDIFF(CURDATE(), hire_date) AS days_worked
FROM employees
ORDER BY days_worked ASC
LIMIT 10;
SELECT /* Most popular birthday month */ MONTHNAME(birth_date) AS birth_month, COUNT(*) AS total
FROM employees
GROUP BY birth_month
ORDER BY total DESC
LIMIT 1;
SELECT /* employees with same first/last name */ emp_no, first_name, last_name
FROM employees
WHERE first_name = last_name;
SELECT /* Most frequently occuring salary */ salary, COUNT(*) AS frequency
FROM salaries
GROUP BY salary
ORDER BY frequency DESC
LIMIT 1;
SELECT /* employees with longest time between title changes */ emp_no, DATEDIFF(MAX(to_date), MIN(from_date)) AS days_between
FROM titles
GROUP BY emp_no
ORDER BY days_between DESC
LIMIT 10;
SELECT /* most common hire date */ hire_date, COUNT(*) AS hires
FROM employees
GROUP BY hire_date
ORDER BY hires DESC
LIMIT 1;
SELECT /* Symmetrical salaries */ emp_no, salary
FROM salaries
WHERE salary = REVERSE(salary);
SELECT /* Same hire/birth month */ emp_no, first_name, last_name, birth_date, hire_date
FROM employees
WHERE MONTH(birth_date) = MONTH(hire_date);
SELECT /* Most frequent year of birth */ YEAR(birth_date) AS birth_year, COUNT(*) AS total
FROM employees
GROUP BY birth_year
ORDER BY total DESC
LIMIT 1;
