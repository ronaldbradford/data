\! echo "Adding name indexes"
ALTER TABLE name ADD INDEX (name);
\! echo "Adding title indexes"
ALTER TABLE title ADD INDEX (title);
