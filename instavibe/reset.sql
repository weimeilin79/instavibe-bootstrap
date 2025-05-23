DROP INDEX IF EXISTS PersonByName;
DROP INDEX IF EXISTS EventByDate;
DROP INDEX IF EXISTS PostByTimestamp;
DROP INDEX IF EXISTS PostByAuthor;
DROP INDEX IF EXISTS FriendshipByPersonB;
DROP INDEX IF EXISTS AttendanceByEvent;
DROP INDEX IF EXISTS MentionByPerson;
DROP INDEX IF EXISTS EventLocationByLocationId;

DROP PROPERTY GRAPH IF EXISTS SocialGraph;


DROP TABLE IF EXISTS EventLocation;
DROP TABLE IF EXISTS Mention;
DROP TABLE IF EXISTS Attendance;
DROP TABLE IF EXISTS Friendship;
DROP TABLE IF EXISTS Post;
DROP TABLE IF EXISTS Event;
DROP TABLE IF EXISTS Location;
DROP TABLE IF EXISTS Person;