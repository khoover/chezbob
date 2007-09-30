--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: books; Type: TABLE; Schema: public; Owner: postgres; Tablespace: 
--

CREATE TABLE books (
    barcode character varying NOT NULL,
    isbn character varying,
    author character varying NOT NULL,
    title character varying NOT NULL
);


ALTER TABLE public.books OWNER TO postgres;

--
-- Data for Name: books; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO books (barcode, isbn, author, title) VALUES ('9780805313192', '0805313192', '-', 'LogicWorks 3 interactive circuit design software for Windows and Macintosh');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780534204990', '0534204996', 'Decker, Rick; Hirshfield, Stuart', 'The Object Concept : An Introduction to Computer Programming Using Cb++/Special Beta/Book and Disk');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9783211826492', '3211826491', 'Cristian, F.; Le Lann, G.', 'Dependable Computing for Critical Applications 4 (Dependable Computing and Fault-Tolerant Systems, Vol 9)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201565270', '0201565277', 'Atkinson, Colin', 'Object-Oriented Reuse, Concurrency and Distribution : An Ada-Based Approach');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201416060', '0201416069', 'Bratko, Ivan', 'Prolog Programming for Artificial Intelligence (International Computer Science Series)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780131907522', '0131907522', 'Shaffer, Clifford A.', 'Practical Introduction to Data Structures and Algorithm Analysis, A (C++ Edition)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201419917', '0201419912', 'Abrahams, Paul W.; Larson, Bruce', 'Unix for the Hyper-Impatient');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780471853190', '0471853194', 'Wakerly, John F.', 'Microcomputer Architecture and Programming : The 68000 Family');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201565065', '0201565064', 'Halsall, Fred', 'Data communications, computer networks, and open systems');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780471607649', '0471607649', 'Newell, Gale E.; Newell, Sydney', 'Introduction to Microcomputing');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780763706210', '0763706213', 'Dale, Nell PhD', 'C++ Plus Data Structures');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201568851', '0201568853', 'Wilson, Leslie B.; Clark, Robert G.', 'Comparative Programming Languages (International Computer Science Series)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201508895', '0201508893', 'Budd, Timothy A.', 'Classic Data Structures in C++');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780387948348', '0387948341', 'Beidler, John', 'Data Structures and Algorithms : An Object-Oriented Approach Using Ada 95 (Undergraduate Texts in Computer Science)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201855715', '0201855712', 'Angel, Edward', 'Interactive Computer Graphics : a Top-Down Approach With Opengl');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780471930112', '0471930113', '-', 'C++ for Programmers');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780024209719', '0024209716', 'Ford, William; Topp, William; William, Ford', 'Data Structures With C++');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780471503088', '0471503088', 'Koschmann, Timothy D.', 'The Common Lisp Companion');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780387948997', '0387948996', 'Jalote, Pankaj', 'An Integrated Approach to Software Engineering (Undergraduate Texts in Computer Science)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780131182660', '0131182668', 'Anderson, Arthur E., Jr.; Heinze, William J.', 'C++ Programming and Fundamental Concepts');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780805300888', '0805300880', 'Adrews, Gregory R.; Olsson, Ronald A.; Andrews, Gregory R.; Olsson, Ron', 'The Sr Programming Language : Concurrency in Practice');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9781565920446', '1565920449', 'Flanagan, David', 'Motif Tools : Streamlined Gui Design and Programming With the Xmt Library/Book and Cd-Rom');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201876987', '0201876981', 'Ceri, Stefano; Mandrioli, Dino; Sbattella, L.', 'The Art and Craft of Computing');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780137689958', '0137689950', 'Kruse, Robert L.; Ryba, Alex; Ryba, Alexander J.', 'Data Structures and Program Design in C++');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201549836', '0201549832', 'Grimaldi, Ralph P.', 'Discrete and Combinatorial Mathematics : An Applied Introduction');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9781565920743', '1565920740', 'Gallmeister, Bill O.', 'Posix. 4 : Programming for the Real World');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201461381', '0201461382', 'Woo, Mason; Neider, Jackie; Davis, Tom; Opengl Architecture Review boa', 'Opengl Programming Guide : The Official Guide to Learning Opengl, Version 1.1');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780064671453', '0064671453', 'Vilms, Liia', 'Introduction to Computer Science and Programming Harpercollins College Outline)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780672484087', '0672484080', 'Kochan, Stephen', 'Programming in ANSI C');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780135904725', '0135904722', 'Kane, Gerry; Heinrich, Joe; Heinrich, Joseph', 'Mips Risc Architecture');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780669349498', '0669349496', 'Headington, Mark R.; Riley, David D.', 'Data Abstraction and Structures Using C++/Book and Disk');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780070278936', '0070278938', 'Heileman, Gregory L.', 'Data Structures, Algorithms and Object -Oriented Programming');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201633467', '0201633469', 'Stevens, W. Richard', 'TCP/IP Illustrated, Volume 1 : The Protocols (Addison-Wesley Professional Computing Series)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780071092197', '0071092196', 'Sahni, Sartaj', 'Data Structures, Algorithms, and Applications in C++');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780805304435', '0805304436', 'Almasi, George S.; Gottlieb, Allan', 'Highly Parallel Computing (The Benjamin/Cummings Series in Computer Science and Engineering)');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780201563337', '0201563339', 'Partridge, Craig', 'Gigabit Networking');
INSERT INTO books (barcode, isbn, author, title) VALUES ('9780256129984', '0256129983', 'Schach, Stephen R.', 'Software Engineering (The Asken Associates Series in Electrical and Computer Engineering)');


--
-- Name: books_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres; Tablespace: 
--

ALTER TABLE ONLY books
    ADD CONSTRAINT books_pkey PRIMARY KEY (barcode);


--
-- Name: books; Type: ACL; Schema: public; Owner: postgres
--

REVOKE ALL ON TABLE books FROM PUBLIC;
REVOKE ALL ON TABLE books FROM postgres;
GRANT ALL ON TABLE books TO postgres;
GRANT ALL ON TABLE books TO chezbob;


--
-- PostgreSQL database dump complete
--

