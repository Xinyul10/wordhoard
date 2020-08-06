START TRANSACTION;
-- first, clear all stored procedures related to our database
USE mysql;
DELETE FROM mysql.proc WHERE db LIKE "wordhoard"; -- found this on stackoverflow

-- drop all of our data
DROP DATABASE IF EXISTS wordhoard;

-- i don't know how to drop triggers. be careful with them!

-- now we can start building our database
CREATE DATABASE wordhoard;
USE wordhoard;


-- table schema
CREATE TABLE Users(
	username VARCHAR(30) NOT NULL,
	password VARCHAR(50) NOT NULL,
	is_administrator BOOLEAN NOT NULL,
	PRIMARY KEY (username)
);

CREATE TABLE Suggestions(
	kind VARCHAR(30) NOT NULL,
	explanation VARCHAR(100) NOT NULL,
	username VARCHAR(30) NOT NULL,
	PRIMARY KEY (kind, explanation, username),
	FOREIGN KEY (username) REFERENCES Users(username) ON DELETE CASCADE
);

CREATE TABLE Words(
	word VARCHAR(100) NOT NULL,
	pronunciation VARCHAR(200) NOT NULL,
	syllables INTEGER NOT NULL,
	rhymekey VARCHAR(2),
	alliterationkey VARCHAR(1),
	PRIMARY KEY (word)
);

CREATE INDEX AlliterationSpeedup ON Words(alliterationkey(1)); -- i don't know if sql is clever enough to know it's already in alphabetical order
-- might as well do it manually

CREATE INDEX RhymeSpeedup ON Words(rhymekey(2));

CREATE INDEX SyllableSpeedup ON Words(syllables);

DELIMITER //

CREATE FUNCTION CountSyllables (word VARCHAR(100)) -- xinyu's utility function
RETURNS INTEGER
DETERMINISTIC
BEGIN
        RETURN (LENGTH(word)*10) -
                                  (LENGTH(REPLACE(word,'0','')) +
                                   LENGTH(REPLACE(word,'1','')) +
                                   LENGTH(REPLACE(word,'2','')) +
                                   LENGTH(REPLACE(word,'3','')) +
                                   LENGTH(REPLACE(word,'4','')) +
                                   LENGTH(REPLACE(word,'5','')) +
                                   LENGTH(REPLACE(word,'6','')) +
                                   LENGTH(REPLACE(word,'7','')) +
                                   LENGTH(REPLACE(word,'8','')) +
                                   LENGTH(REPLACE(word,'9','')));
END//

CREATE TRIGGER AutofillWordInsert BEFORE INSERT ON Words FOR EACH ROW BEGIN
	CALL AutoFillWord(NEW.rhymekey, NEW.alliterationkey, NEW.syllables, NEW.word, NEW.pronunciation);
END//

CREATE TRIGGER AutofillWordUpdate BEFORE UPDATE ON Words FOR EACH ROW BEGIN
	CALL AutoFillWord(NEW.rhymekey, NEW.alliterationkey, NEW.syllables, NEW.word, NEW.pronunciation);
END//

CREATE PROCEDURE AutoFillWord(OUT rhymekey VARCHAR(2),OUT alliterationkey VARCHAR(1),OUT syllables INTEGER,IN word VARCHAR(100), IN pronunciation VARCHAR(200))
BEGIN
	IF LENGTH(pronunciation)>=2 THEN
		SET rhymekey = SUBSTRING(pronunciation,LENGTH(pronunciation)-1,2);
	END IF;
	IF LENGTH(word)>=1 THEN
		SET alliterationkey = SUBSTRING(word,1,1);
	END IF;
	SET syllables = CountSyllables(pronunciation);
END//

DELIMITER ;


CREATE TABLE Synsets(
	synset VARCHAR(100),
	PRIMARY KEY(synset)
);

CREATE TABLE Synonyms(
	word VARCHAR(100) NOT NULL,
	synset VARCHAR(100) NOT NULL,
	PRIMARY KEY (word,synset),
	FOREIGN KEY (word) REFERENCES Words(word) ON DELETE CASCADE,
	FOREIGN KEY (synset) REFERENCES Synsets(synset) ON DELETE CASCADE
);

CREATE INDEX SynSynset ON Synonyms(synset);
CREATE INDEX SynWord ON Synonyms(word);

CREATE TABLE Puns(
	word1 VARCHAR(100) NOT NULL,
	word2 VARCHAR(100) NOT NULL,
	PRIMARY KEY (word1, word2),
	FOREIGN KEY (word1) REFERENCES Words(word) ON DELETE CASCADE,
	FOREIGN KEY (word2) REFERENCES Words(word) ON DELETE CASCADE,
	CONSTRAINT Alphabetic CHECK(word1<word2)
);

CREATE TABLE Hyponym_Of(
	word1 VARCHAR(100) NOT NULL,
	word2 VARCHAR(100) NOT NULL,
	PRIMARY KEY (word1, word2),
	FOREIGN KEY (word1) REFERENCES Words(word) ON DELETE CASCADE,
	FOREIGN KEY (word2) REFERENCES Words(word) ON DELETE CASCADE,
	CONSTRAINT Alphabetic CHECK(word1<word2)
);


DROP FUNCTION IF EXISTS RHYMES;

DELIMITER //

CREATE FUNCTION RHYMES (a VARCHAR(200),b VARCHAR(200))
RETURNS INTEGER
DETERMINISTIC
BEGIN
	DECLARE maxlength INTEGER;
	DECLARE curlength INTEGER;
	DECLARE alen INTEGER;
	DECLARE blen INTEGER;

	SET curlength = 0;
	SET maxlength = LEAST(LENGTH(a),LENGTH(b));
	SET alen = LENGTH(a);
	SET blen = LENGTH(b);

	WHILE curlength<maxlength AND SUBSTR(a,alen-curlength,1)=SUBSTR(b,blen-curlength,1) DO
		SET curlength = curlength+1;
	END WHILE;

	IF curlength=maxlength THEN
		SET curlength = 0; -- one word CONTAINS the other... not a good rhyme. e.g. "screen" and "onscreen".
	END IF;

	RETURN curlength;
END//

DELIMITER ;
COMMIT;
