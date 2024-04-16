PRAGMA foreign_keys = ON;


CREATE TABLE "stadium" (
"Stadium_ID" int,
"Location" text,
"Name" text,
"Capacity" int,
"Highest" int,
"Lowest" int,
"Average" int,
PRIMARY KEY ("Stadium_ID")
);


INSERT INTO  "stadium" VALUES (1,"Raith Rovers","Stark's Park","10104","4812","1294","2106");
INSERT INTO  "stadium" VALUES (2,"Ayr United","Somerset Park","11998","2363","1057","1477");
INSERT INTO  "stadium" VALUES (3,"East Fife","Bayview Stadium","2000","1980","533","864");
INSERT INTO  "stadium" VALUES (4,"Queen's Park","Hampden Park","52500","1763","466","730");
INSERT INTO  "stadium" VALUES (5,"Stirling Albion","Forthbank Stadium","3808","1125","404","642");
INSERT INTO  "stadium" VALUES (6,"Arbroath","Gayfield Park","4125","921","411","638");
INSERT INTO  "stadium" VALUES (7,"Alloa Athletic","Recreation Park","3100","1057","331","637");
INSERT INTO  "stadium" VALUES (9,"Peterhead","Balmoor","4000","837","400","615");
INSERT INTO  "stadium" VALUES (10,"Brechin City","Glebe Park","3960","780","315","552");

CREATE TABLE "singer" (
"Singer_ID" int,
"Name" text,
"Country" text,
"Song_Name" text,
"Song_release_year" text,
"Age" int,
"Is_male" bool,
PRIMARY KEY ("Singer_ID")
);



INSERT INTO  "singer" VALUES (1,"Joe Sharp","Netherlands","You","1992",52,"F");
INSERT INTO  "singer" VALUES (2,"Timbaland","United States","Dangerous","2008",32,"T");
INSERT INTO  "singer" VALUES (3,"Justin Brown","France","Hey Oh","2013",29,"T");
INSERT INTO  "singer" VALUES (4,"Rose White","France","Sun","2003",41,"F");
INSERT INTO  "singer" VALUES (5,"John Nizinik","France","Gentleman","2014",43,"T");
INSERT INTO  "singer" VALUES (6,"Tribal King","France","Love","2016",25,"T");


CREATE TABLE "concert" (
"concert_ID" int,
"concert_Name" text,
"Theme" text,
"Stadium_ID" text,
"Year" text,
PRIMARY KEY ("concert_ID"),
FOREIGN KEY ("Stadium_ID") REFERENCES "stadium"("Stadium_ID")
);



INSERT INTO  "concert" VALUES (1,"Auditions","Free choice",1,2014);
INSERT INTO  "concert" VALUES (2,"Super bootcamp","Free choice 2",2,2014);
INSERT INTO  "concert" VALUES (3,"Home Visits","Bleeding Love",2,2015);
INSERT INTO  "concert" VALUES (4,"Week 1","Wide Awake",10,2014);
INSERT INTO  "concert" VALUES (5,"Week 1","Happy Tonight",9,2015);
INSERT INTO  "concert" VALUES (6,"Week 2","Party All Night",7,2015);


CREATE TABLE "singer_in_concert" (
"concert_ID" int,
"Singer_ID" text,
PRIMARY KEY ("concert_ID","Singer_ID"),
FOREIGN KEY ("concert_ID") REFERENCES "concert"("concert_ID"),
FOREIGN KEY ("Singer_ID") REFERENCES "singer"("Singer_ID")
);

INSERT INTO  "singer_in_concert" VALUES (1, 2);
INSERT INTO  "singer_in_concert" VALUES (1, 3);
INSERT INTO  "singer_in_concert" VALUES (1, 5);
INSERT INTO  "singer_in_concert" VALUES (2, 3);
INSERT INTO  "singer_in_concert" VALUES (2, 6);
INSERT INTO  "singer_in_concert" VALUES (3, 5);
INSERT INTO  "singer_in_concert" VALUES (4, 4);
INSERT INTO  "singer_in_concert" VALUES (5, 6);
INSERT INTO  "singer_in_concert" VALUES (5, 3);
INSERT INTO  "singer_in_concert" VALUES (6, 2);

