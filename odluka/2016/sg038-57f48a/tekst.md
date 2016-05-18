Službeni glasnik BiH, broj 38/16
Na osnovu člana 8. Zakona o statistici Bosne i Hercegovine ("Službeni glasnik BiH", broj 26/04 i 42/04) i na osnovu člana 20. i člana 28. Zakona o popisu stanovništva, domaćinstava i stanova u Bosni i Hercegovini 2013. godine ("Službeni glasnik BiH", broj 10/12 i 18/13), direktor Agencije za statistiku Bosne i Hercegovine propisuje
ODLUKU
O USVAJANJU JEDINSTVENOG PROGRAMA OBRADE PODATAKA POPISA STANOVNIŠTVA, DOMAĆINSTAVA I STANOVA U BOSNI I HERCEGOVINI 2013. GODINE
Član 1.
(Predmet Odluke o usvajanju Jedinstvenog programa)
Usvaja se Jedinstveni program obrade podataka popisa stanovništva, domaćinstava i stanova u Bosni i Hercegovini 2013. godine (u daljem tekstu: Jedinstveni program), koji će se provoditi na nivou Bosne i Hercegovine.
Član 2.
(Jedinstveni program)
Jedinstveni program je sastavni dio ove odluke.
Član 3.
(Nadležno tijelo za provođenje Jedinstvenog programa)
Agencija za statistiku Bosne i Hercegovine, Federalni zavod za statistiku i Republički zavod za statistiku Republike Srpske su nadležni za provođenje aktivnosti iz Jedinstvenog programa.
Član 4.
(Stupanje na snagu)
Ova odluka stupa na snagu danom donošenja i objavljuje se u "Službenom glasniku BiH".
Broj 11-43-2-12-601-2/16
18. maja 2016. godine
Sarajevo
Direktor
Mr. sc. Velimir Jukić, s. r.
Na osnovu čl. 20. i čl. 28. Zakona o popisu stanovništva, domaćinstava i stanova u Bosni i Hercegovini 2013. godine ("Službeni glasnik BiH", br. 10/12 i 18/13), direktor Agencije za statistiku BiH donosi
"JEDINSTVENI PROGRAM OBRADE PODATAKA POPISA STANOVNIŠTVA, DOMAĆINSTAVA I STANOVA U BOSNI I HERCEGOVINI 2013. GODINE"
1. OPĆI DIO
Jedinstvenim programom se uređuje proces obrade podataka popisa; redoslijed izvršavanja koraka u postupku određivanja stalnog (rezidentnog) stanovništva; način izvođenja konačne baze podataka koja će se koristiti za statističke obrade i objave (diseminaciju) statičkih podataka prikupljenih popisom.
Cilj jedinstvenog programa je definisati okvir obrade podataka popisa u skladu sa Zakonom o popisu stanovništva, domaćinstava i stanova u Bosni i Hercegovini 2013. godine (u daljem tekstu: Zakon o popisu), Metodologijom za pripremu, organizovanje i provođenje popisa stanovništva, domaćinstava i stanova u Bosni i Hercegovini 2013. godine (u daljem tekstu: Metodologija) i slijedećim međunarodnim standardima i preporukama:
- Međunarodne preporuke za popise stanovništva i domaćinstava koje definišu UNECE i Eurostat, a koje je odobrila Konferencija evropskih statističara kao Preporuke za Popise stanovništva i domaćinstava 2010. i uputama Međunarodnog monitoring tima (u daljem tekstu: IMO tim);
- Odredbu (EK) 763/2008 o popisima stanovništva i domaćinstava, te mjere implementacije;
- Odredbu (EK) 1201/2009 tehničke specifikacije obilježja i njihova distribucija;
- Osnovna načela zvanične statistike, usvojena od strane Statističke komisije UN, kao i sa Kodeksom prakse evropske statistike proglašen od strane Evropske komisije;
- Standardi zaštite i povjerljivosti podataka, kako je dato u Konvenciji o zaštiti pojedinca, a u vezi sa automatskom obradom ličnih podataka Vijeća Evrope, kao i sa važećim relevantnim odredbama Evropske unije;
- Preporuke IMO tima datim u 20. i 21. Izvještaju;
- Pismu predsjedavajućeg IMO tima, sa preporukama za rješavanje otvorenih pitanja, upućenog 16.6.2015. Vijeću ministara Bosne i Hercegovine.
2. PROCES OBRADE PODATAKA
Proces obrade podataka podrazumijeva niz predefinisanih koraka i automatizovanih procedura kojima se obrađuju podaci popisa.
Nakon završetka terenskog rada i skladištenja materijala u centralnom obradnom mjestu, pristupilo se provođenju aktivnosti neophodnih za dobijanje elektronske baze sirovih podataka.
Na slici 1. prikazan je funkcionalni dijagram obrade podataka koji uključuje i sve faze pripreme popisnog materijala za obradu.
Slika 1
2.1. Kontrola i validiranje podataka
Nakon dobijanja sirove baze podataka, pristupa se procesu obrade podataka koji je definisan u narednim koracima.
2.1.1. Utvrđivanje važećih popisnica za obradu
Iz ukupnog broja popisnica P1 i P2, uz upotrebu automatizovanih SQL procedura koje se primjenjuju direktno na bazi podataka, će biti izdvojene popisnice koje se ne trebaju obrađivati prema Zakonu o popisu i metodologiji.
Sljedeće popisnice neće ići u dalju obradu:
- Popisnice sa vještačkim bar codeom (popisnice korištene za trening popisivača i dio popisnica korištenih za predpopisivanje koji nisu odbačeni u procesu ručne pripreme);
- P2 popisnice za objekte koji nisu jedinice popisa;
- P1 popisnice bez ijednog odgovora na pitanja Q1-Q7;
- P1 popisnice za strano diplomatsko, konzularno i vojno osoblje;
- Popisnice za djecu rođenu poslije kritičnog momenta popisa;
- Djeca odsutna iz mjesta popisa, rođena poslije 30. septembra 1998. godine, a podatke za njih nisu dali njihovi roditelji;
- Osobe za koje su podatke dale maloljetne osobe;
- Domaćinstva čiji su svi članovi odsutni iz mjesta popisa;
- Domaćinstva čiji su svi članovi odsutni i koji su popisani sa privremeno prisutnim osobama u mjestu popisa;
- Privremeno prisutne osobe koje nisu dale podatke za sebe.
Nakon što ove popisnice budu izdvojene, iz baze podataka će biti eliminisane višestrukе popisnice P1 koje se odnose na istu osobu. Jedna popisnica ide u dalju obradu.
Preostale popisnice P1 i P2 čine ukupan set popisnica koje će se koristiti za statističke obrade podataka popisa.
Na kraju ovog procesa, biti će potvrđena usklađenost između popisnica P1 i P2. Ovo se uglavnom odnosi na slučajeve domaćinstva čiji svi članovi nisu obuhvaćeni.
2.1.2. Preliminarne ispravke geografskih varijabli
U ovom koraku, šifre geografskih varijabli se ispravljaju korištenjem specifičnih procedura razvijenih u SQL-u.
Za ispravljanje grešaka koriste se donori, ispravni odgovori koji se odnose na isto mjesto popisa u kojima su napravljene greške.
2.1.3. Određivanje statusa rezidenta popisanih osoba
Nakon definisanja ukupnog seta validnih popisnica P1 i P2, izvršiti će se utvrđivanje statusa rezidenta za svaku osobu.
Ovaj proces se sastoji od sljedećih koraka:
a) Primjena seta determinističkih pravila na pitanja 1-7 P1 popisnice sa ciljem rješavanja nedoslijednosti u odgovorima, a koje se mogu riješiti uz minimalne promjene varijabli. U prilogu 1 se nalazi 9 determinističkih pravila za ispravljanje očiglednih nedoslijednosti na pitanjima 1-7 P1 popisnice;
b) Izvođenje varijable po imenu Trajanje (dužina prisutnosti/odsutnosti) kao sumu vrijednosti pitanja Q4 i Q5 P1 popisnice;
c) Primjena 29 determinističkih pravila (na osnovu prvih sedam pitanja) za određivanje statusa rezidenta; U prilogu 2 se nalazi 29 determinističkih pravila za određivanje statusa rezidenta na osnovu pitanja 1-7;
d) Eksportovanje rezultirajućeg seta podataka u ASCII tab delimiter fajl, koji uključuje prvih sedam pitanja, varijablu Trajanje, jedinstveni identifikator zapisa i već utvrđeni status rezidenta (koji može nedostajati za neke osobe);
e) Primjena statističke metode prema Fellegi-Holt algoritmu, koja će utvrditi i ispraviti usklađenost između prvih sedam pitanja (samo za slučajeve u kojima nedostaje status rezidenta);
f) Dozvoljena granica promjena za varijable pitanja 1-7 prema probabilističkoj metodi je 2. U slučaju da varijablu čini više od jednog polja (kao Q4), ukupne promjene su 0 (ako nema promjena ni za jednu vrijednost) ili 1 (najmanje jedna promjena);
g) Unos dobijenog ASCII tab delimiter fajla u bazu podataka;
h) Ponovno izvođenje varijable Trajanje za popisnice tretirane statističkom metodom iz tačke e;
i) Ponovna primjena 29 determinističkih pravila da bi se utvrdio status rezidenta za popisnice tretirane statističkom metodom iz tačke e;
j) Automatska dodjela statusa "Nije rezident u BiH" za osobe koje ne zadovoljavaju ni jedno od 29 pravila.
Koraci (e) i (f) će se izvršiti upotrebom ADaMSoft i Concord/SCIA programskih alata.
Svi drugi koraci će se realizovati na bazi podataka izvršavanjem predefinisanih SQL skripti.
ADaMSoft softver će se koristiti i za provjeru i verifikaciju postupaka izvođenja rezidentnog statusa (korak c).
2.1.4. Editovanje i imputacija podataka
Nakon određivanja statusa rezidenta, podaci na popisnicama P1 i P2 će biti verifikovani na način da se provjeri njihova unutrašnja koherentnost.
Te aktivnosti se odnose na:
- Editovanje podataka - korake u kojima se podaci verifikuju, i na kraju, ispravljaju;
- Verifikacija podataka - provjere rezultata dobijenih u prethodnom koraku, uzimajući u obzir izvorni raspored varijabli, vanjskih izvora i verifikujući promjene, dobijene u koraku editovanje podataka, između svih varijabli.
Ove aktivnosti će se izvršavati iterativno, sve dok validacija ne potvrdi da su rezultati doslijedni i da nisu generirane nikakve greške na izvornim podacima.
Na popisnici P2, koraci editovanja podataka podrazumijevaju:
a) Editovanje i imputacija uzimajući u obzir sve kategorijske varijable za svako domaćinstvo;
b) Editovanje i imputacija za svaki stan/zgradu da bi se postigla koherentnost za varijable uključene u provjere, kao što su broj spratova, postojanje lifta, itd.;
c) Editovanje i imputacija numeričkih varijabli koji se odnose na obilježja kuća (broj soba, kvadratura, itd.);
d) Validacija i ispravljanje varijabli koje se odnose na dio popisnice sa podacima o poljoprivredi.
Na popisnici P1, koraci editovanja podataka podrazumijevaju:
a) Provjere i ispravke podskupa varijabli koje se odnose na svako domaćinstvo: godine, spol, bračni status, odnos prema nosiocu domaćinstva i status porodice;
b) Primjena determinističkih ispravki uzimajući u obzir modifikacije proistekle iz prethodnih koraka;
c) Primjena statističke metode, prema Fellegi-Holt algoritmu, za provjeru i ispravku varijabli za popisnice P1 i P2 (izuzimajući pitanja 1-7 popisnice P1);
d) Konačne determinističke ispravke koje će uzeti u obzir rezultate proistekle iz prethodnog koraka (na primjer za varijable koje nisu direktno korištene u pravilima).
2.1.5. Šifriranje tekstualnih obilježja
Tekstualnim zapisima u bazi podataka će biti dodijeljena odgovarajuća šifra u skladu sa usvojenim šifarnicima i tezaurusima.
Tekstualna polja koja su predmet šifriranja su:
- Državljanstvo
- Države
- Općine
- Naseljena mjesta
- Zanimanje: Klasifikacija zanimanja KZ BiH - 08
- Djelatnost: Klasifikacija djelatnosti KD BiH - 2010
- Nacionalnost/etnička pripadnost
- Maternji jezik
- Vjeroispovijest
Objava rezultata popisa će biti urađena u skladu sa šifarnicima.
3. OBJAVA REZULTATA POPISA
U skladu sa Zakonom o popisu konačni rezultati popisa će biti objavljeni najkasnije do 1.7.2016. godine.
Do navedenog datuma će biti objavljen ukupan broj stanovnika na svim nivoima vlasti (država, entiteti, kantoni, općine, Brčko Distrikt).
Objava preostalih podataka će biti realizovana sukcesivno u skladu sa planom diseminacije podataka popisa.
Prilog 1:
9 determinističkih pravila za korekcije očiglednih nekonzistentnosti na pitanjima Q1-Q7
Prilog 2:
29 determinističkih pravila za određivanje rezidentnog statusa na osnovu pitanja Q1-Q7
Ovaj program stupa na snagu danom donošenja i objavljuje se u "Službenom glasniku BiH".
Broj 11-43-2-12-601-3-1/16
18. maja 2016. godine
Sarajevo
Agencija za statistiku BiH
Direktor
Mr. sc. Velimir Jukić, s. r.
Prilog 1:
9 determinističkih pravila za korekcije očiglednih nekonzistentnosti na pitanjima Q1-Q7
Prije puštanja pravila za izvođenje rezidenata primjenjuju se određena deterministička pravila za rješavanje greške (RES = 0; popisnice za koje nije bilo moguće odrediti rezidentni status). Primjenom determinističkih pravila postiže se konzistentnost između odgovora na način da se vrši izmjena samo jednog odgovora na pitanjima 1-7.
Značenje pojmova:
- NULL - prazno polje, nema odgovora na pitanje
- NOT NULL - postoji odgovor na pitanje
- Q - redni broj pitanja na popisnici
Determinističko pravilo 1
Q1_stalni
2
Q2_pris
2
Q3_razlog
NOT NULL
Q4Q5(extracted)_trajanje
<> 0
Q6a_mjestoop
NOT NULL
Q7_ucest
NOT NULL
Akcija
Promijeni Q2_pris na NULL
Pravilom broj 1 vrši se promjena odgovora Q2=2 na NULL. Tačnije, osoba je odsutna i na prvom pitanju je označen odgovor b), a na drugom pitanju je još jednom potvrdila svoju odsutnost iako nije treba dati odgovor na ovo pitanje.
Determinističko pravilo 2
Q1_stalni
2
Q2_pris
NULL
Q3_razlog
NOT NULL
Q4Q5(extracted)_trajanje
1
Q6a_mjestoop
NOT NULL
Q7_ucest
NULL
Akcija
Promijeni Q7_ucest na 1
Pravilom broj 2 odgovor na pitanju 7 se mijenja u odgovor 1 (rjeđe od jednom sedmično). Osoba je odsutna iz mjesta popisa kraće od godinu dana pa samo pitanje učestalosti vraćanja u mjesto popisa ne utiče na njenu rezidentnost (rezident u mjestu popisa).
Determinističko pravilo 3
Q1_stalni
1
Q2_pris
1
Q3_razlog
NULL
Q4Q5(extracted)_trajanje
0
Q6a_mjestoop
NULL
Q7_ucest
Not null
Akcija
Promijeni Q7_ucest na NULL
Pravilom broj 3 odgovor na pitanju 7 se mijenja u odgovor NULL, tj. briše se odgovor na ovom pitanju jer je osoba odgovorila da živi u mjestu popisa i prisutna je u kritičnom momentu popisa, ne treba da ima odgovore na pitanja 3-7.
Determinističko pravilo 4
Q1_stalni
1
Q2_pris
1
Q3_razlog
NULL
Q4Q5(extracted)_trajanje
0
Q6a_mjestoop
NOT NULL
Q7_ucest
NULL
Akcija
Promijeni
Q6_mjestoop na NULL
Pravilom broj 4 odgovor na pitanju 6 se mijenja u odgovor NULL, tj. briše se odgovor na ovom pitanju jer je osoba odgovorila da živi u mjestu popisa i prisutna je u kritičnom momentu popisa, ne treba da ima odgovore na pitanja 3-7.
Determinističko pravilo 5
Q1_stalni
1
Q2_pris
2
Q3_razlog
NOT NULL
Q4Q5(extracted)_trajanje
1
Q6a_mjestoop
NOT NULL
Q7_ucest
NULL
Akcija
Promijeni Q7_ucest na 1
Pravilom broj 5 odgovor na pitanju 7 se mijenja u odgovor 1 (rjeđe od jednom sedmično). Osoba je na pitanju 1 odgovorila da živi u mjestu popisa godinu dana ili duže, a na drugom pitanju je odgovorila da nije prisutna. Na pitanjima 3 do 7 trebaju biti odgovori, a na pitanju 7 ne postoji odgovor. Pitanje učestalosti vraćanja u mjesto popisa ne utiče na rezidentnost osobe jer je dužina odsustva kraća od godinu dana.
Determinističko pravilo 6
Q1_stalni
2
Q2_pris
NULL
Q3_razlog
NOT NULL
Q4Q5(extracted)_trajanje
2
Q6a_mjestoop
1
Q7_ucest
NULL
Akcija
Promijeni Q7_ucest na 1
Pravilom broj 6 odgovor na pitanju 7 se mijenja u odgovor 1 (rjeđe od jednom sedmično). Osoba je odsutna iz mjesta popisa duže od godinu dana u drugom mjestu unutar BiH, pa samo pitanje učestalosti vraćanja u mjesto popisa ne utiče na njenu rezidentnost (rezident u drugom mjestu u BiH).
Determinističko pravilo 7
Q1_stalni
3
Q2_pris
1
Q3_razlog
NOT NULL
Q4Q5(extracted)_trajanje
<>0
Q6a_mjestoop
NOT NULL
Q7_ucest
NOT NULL
Akcija
Promijeni Q2_pris na NULL
Pravilom broj 7 vrši se promjena odgovora Q2=2 na NULL. Tačnije, osoba je privremeno prisutna i na prvom pitanju je označen odgovor c), a na drugom pitanju je još jednom potvrdila svoju prisutnost iako nije treba dati odgovor na ovo pitanje.
Determinističko pravilo 8
Q1_stalni
3
Q2_pris
NULL
Q3_razlog
NOT NULL
Q4Q5(extracted)_trajanje
<>0
Q6a_mjestoop
1
Q7_ucest
NULL
Akcija
Promijeni Q7_ucest na 1
Pravilom broj 8 odgovor na pitanju 7 se mijenja u odgovor 1 (rjeđe od jednom sedmično). Osoba je u mjestu popisa privremeno prisutna iz drugog mjesta u BiH, pa samo pitanje učestalosti vraćanja u mjesto popisa ne utiče na njenu rezidentnost (rezident BiH).
Determinističko pravilo 9
Q1_stalni
3
Q2_pris
NULL
Q3_razlog
NOT NULL
Q4Q5(extracted)_trajanje
1
Q6a_mjestoop
2
Q7_ucest
NULL
Akcija
Promijeni Q7_ucest na 1
Pravilom broj 9 odgovor na pitanju 7 se mijenja u odgovor 1 (rjeđe od jednom sedmično). Osoba je u mjestu popisa privremeno prisutna iz inostranstva kraće od godinu dana pa samo pitanje učestalosti vraćanja u mjesto popisa ne utiče na njenu rezidentnost (nije rezident BiH).
Prilog 2:
29 determinističkih pravila za određivanje rezidentnog statusa na osnovu pitanja Q1-Q7
Set od 29 determinističkih pravila je kreiran u skladu sa Zakonom o popisu u BiH sa ciljem izvođenja kategorije stalnog stanovništva - rezidenata na osnovu člana 2. Zakona o popisu, odnosno na osnovu trajanja i namjere življenja u mjestu popisa.
U sljedećoj tabeli je opisano 29 pravila na osnovu kojih svaka popisnica (osoba/lice) dobija status rezidenta. Postoje tri različita statusa rezidenta od kojih svaka osoba može dobiti jedan od njih:
1. Res=1 - osoba je rezident/stalni stanovnik u mjestu popisa
2. Res=2 - osoba je rezident/stalni stanovnik u drugom mjestu u BiH
3. Res=3 - osoba nije rezident/stalni stanovnik nigdje u BiH
Pored ova tri statusa rezidenta/stalnog stanovnika osoba može dobiti i status Res=0, a to znači da u tom momentu nije bilo moguće izvesti status rezidenta/stalnog stanovnika.
Nakon što se iscrpe sve mogućnosti izvođenja rezidenta/stalnog stanovnika na kraju procesa obrade sve popisnice za koje nije bilo moguće izvesti status rezidenta/stalnog stanovnika se proglašavaju NEREZIDENTIMA tj. nisu stalni stanovnici nigdje u BiH.
Redni broj pravila
Q1_
stalni
Q2_
pris
Q3_
razlog
Q4Q5
_trajanje
Q6a_
mjestoop
Q6b_
nasop
Q6c_
opop
Q6d
_drzop
Q7
_ucest
resident status
Tekstualni opis
pravila
1
1
1
NULL
0
NULL
NULL
NULL
NULL
NULL
Res=1
Osoba popisana kao prisutni član domaćinstva i nema nijedan podatak na
pitanjima od 3 do 7 smatra se rezidentnim stanovnikom mjesta popisa.
2
1
2
1
or 2
or 3
or 4
1
or 2
1
NOT NULL
NOT NULL
NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
drugom mjestu u BiH (1-rad, 2-školovanje, 3-porodični i 4-ostali razlozi) bez
obzira na trajanje odsustva i učestalost vraćanja u mjesto popisa smatra se
rezidentnim stanovnikom mjesta popisa.
3
1
2
5
or 7
2
2
NULL
NULL
NOT NULL
2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (5-rad i 7-član domaćinstva osobe sa odsustvom iz razloga 5), sa
trajanjem godinu i duže i koja se vraća u mjesto popisa najmanje jednom
sedmično smatra se rezidentnim stanovnikom mjesta popisa.
4
1
2
5
or 7
1
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (5-rad i 7-član domaćinstva osobe sa odsustvom iz razloga 5), sa
trajanjem kraće od godinu bez obzira na učestalost vraćanja u mjesto popisa
smatra se rezidentnim stanovnikom mjesta popisa.
5
1
2
5
or 7
2
2
NULL
NULL
NOT NULL
1
Res=3
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (5-rad i 7-član domaćinstva osobe sa odsustvom iz razloga 5), sa
trajanjem godinu i duže i koja se vraća u mjesto popisa rjeđe od jednom
sedmično ne smatra se rezidentnim stanovnikom BiH.
6
1
2
6
or 8
1
or 2
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (6- upućen na rad u DKP, međunarodne organizacije i sl. 8-član
domaćinstva osobe odsutne iz raloga 6) bez obzira na trajanje odsustva i
učestalost vraćanja u mjesto popisa smatra se rezidentnim stanovnikom mjesta
popisa.
7
1
2
9
1
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (9-školovanje), sa trajanjem kraće od godinu bez obzira na
učestalost vraćanja u mjesto popisa smatra se rezidentnim stanovnikom mjesta
popisa.
8
1
2
9
2
2
NULL
NULL
NOT NULL
1
or 2
Res=3
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (9-školovanje), sa trajanjem godinu i duže bez obzira na
učestalost vraćanja u mjesto popisa ne smatra se rezidentnim stanovnikom BiH.
9
1
2
10
1
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (10-ostali razlozi), sa trajanjem kraće od godinu bez obzira na
učestalost vraćanja u mjesto popisa smatra se rezidentnim stanovnikom mjesta
popisa.
10
1
2
10
2
2
NULL
NULL
NOT NULL
1
or 2
Res=3
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (10-ostali razlozi), sa trajanjem godinu i duže bez obzira na
učestalost vraćanja u mjesto popisa ne smatra se rezidentnim stanovnikom BiH.
11
2
NULL
1
or 2
or 3
or 4
1
or 2
1
NOT NULL
NOT NULL
NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
drugom mjestu u BiH (1-rad, 2-školovanje, 3-porodični i 4-ostali razlozi) bez
obzira na trajanje odsustva i učestalost vraćanja u mjesto popisa smatra se
rezidentnim stanovnikom mjesta popisa.
12
2
NULL
5
or 7
2
2
NULL
NULL
NOT NULL
2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (5-rad i 7-član domaćinstva osobe sa odsustvom iz razloga 5), sa
trajanjem godinu i duže i koja se vraća u mjesto popisa najmanje jednom
sedmično smatra se rezidentnim stanovnikom mjesta popisa.
13
2
NULL
5
or 7
1
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (5-rad i 7-član domaćinstva osobe sa odsustvom iz razloga 5), sa
trajanjem kraće od godinu bez obzira na učestalost vraćanja u mjesto popisa
smatra se rezidentnim stanovnikom mjesta popisa.
14
2
NULL
5
or 7
2
2
NULL
NULL
NOT NULL
1
Res=3
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (5-rad i 7-član domaćinstva osobe sa odsustvom iz razloga 5), sa
trajanjem godinu i duže i koja se vraća u mjesto popisa rjeđe od jednom
sedmično ne smatra se rezidentnim stanovnikom BiH.
15
2
NULL
6
or 8
1
or 2
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (6- upućen na rad u DKP, međunarodne organizacije i sl. 8-član
domaćinstva osobe odsutne iz raloga 6) bez obzira na trajanje odsustva i
učestalost vraćanja u mjesto popisa smatra se rezidentnim stanovnikom mjesta
popisa.
16
2
NULL
9
1
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (9-školovanje), sa trajanjem kraće od godinu bez obzira na
učestalost vraćanja u mjesto popisa smatra se rezidentnim stanovnikom mjesta
popisa.
17
2
NULL
9
2
2
NULL
NULL
NOT NULL
1
or 2
Res=3
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (9-školovanje), sa trajanjem godinu i duže bez obzira na
učestalost vraćanja u mjesto popisa ne smatra se rezidentnim stanovnikom BiH.
18
2
NULL
10
1
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (10-ostali razlozi), sa trajanjem kraće od godinu bez obzira na
učestalost vraćanja u mjesto popisa smatra se rezidentnim stanovnikom mjesta
popisa.
19
2
NULL
10
2
2
NULL
NULL
NOT NULL
1
or 2
Res=3
Osoba popisana kao odsutni član domaćinstva sa razlogom odsustva u
inostranstvu (10-ostali razlozi), sa trajanjem godinu i duže bez obzira na
učestalost vraćanja u mjesto popisa ne smatra se rezidentnim stanovnikom BiH.
20
3
NULL
1
1
or 2
1
NOT NULL
NOT NULL
NULL
1
or 2
Res=2
Osoba popisana kao privremeno prisutna u mjestu popisa iz drugog mjesta
BiH sa razlogom rada, bez obzira na trajanje prisustva i učestalost vraćanja
u mjesto stalnog stanovanja smatra se rezidentom drugog naseljenog mjesta
BiH.
21
3
NULL
1
1
2
NULL
NULL
NOT NULL
1
or 2
Res=3
Osoba popisana kao privremeno prisutna u mjestu popisa iz druge države
sa razlogom rada, sa trajanjem prisustva kraće od godinu dana u BiH, bez
obzira na učestalost vraćanja u mjesto stalnog stanovanja ne smatra se
rezidentom BiH.
22
3
NULL
1
2
2
NULL
NULL
NOT NULL
2
Res=3
Osoba popisana kao privremeno prisutna u mjestu popisa iz druge države
sa razlogom rada, sa trajanjem duže od godinu dana u BiH, a vraća se najmanje
jednom sedmično u mjesto stalnog stanovanja ne smatra se rezidentom BiH.
23
3
NULL
1
2
2
NULL
NULL
NOT NULL
1
Res=1
Osoba popisana kao privremeno prisutna u mjestu popisa iz druge države
sa razlogom rada, sa trajanjem duže od godinu dana u BiH, a vraća se rjeđe od
jednom sedmično u mjesto stalnog stanovanja smatra se rezidentom BiH.
24
3
NULL
2
1
or 2
1
NOT NULL
NOT NULL
NULL
1
or 2
Res=2
Osoba popisana kao privremeno prisutna u mjestu popisa iz drugog mjesta
BiH sa razlogom školovanja, bez obzira na trajanje prisustva i učestalost
vraćanja u mjesto stalnog stanovanja smatra se residentom drugog naseljenog
mjesta BiH.
25
3
NULL
2
1
2
NULL
NULL
NOT NULL
1
or 2
Res=3
Osoba popisana kao privremeno prisutna u mjestu popisa iz druge države
sa razlogom školovanja, sa trajanjem prisustva kraće od godinu dana u BiH,
bez obzira na učestalost vraćanja u mjesto stalnog stanovanja ne smatra se
rezidentom BiH.
26
3
NULL
2
2
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao privremeno prisutna u mjestu popisa iz druge države
sa razlogom školovanja, sa trajanjem duže od godinu dana u BiH, bez obzira na
učestalost vraćanja u mjesto stalnog stanovanja smatra se rezidentom BiH.
27
3
NULL
3
or 4
1
or 2
1
NOT NULL
NOT NULL
NULL
1
or 2
Res=2
Osoba popisana kao privremeno prisutna u mjestu popisa iz drugog mjesta
u BiH iz porodičnih i ostalih razloga bez obzira na trajanje i učestalost
vraćanja u mjesto stalnog stanovanja smatra se rezidentom drugog naseljenog
mjesta BiH.
28
3
NULL
3
or 4
1
2
NULL
NULL
NOT NULL
1
or 2
Res=3
Osoba popisana kao privremeno prisutna u mjestu popisa iz druge države
iz porodičnih i ostalih razloga, sa trajanjem prisustva kraće od godinu dana
u BiH, bez obzira na učestalost vraćanja u mjesto stalnog stanovanja ne
smatra se rezidentom BiH.
29
3
NULL
3
or 4
2
2
NULL
NULL
NOT NULL
1
or 2
Res=1
Osoba popisana kao privremeno prisutna u mjestu popisa iz druge države
sa razlogom rada, sa trajanjem duže od godinu dana u BiH, bez obzira na
učestalost vraćanja u mjesto stalnog stanovanja smatra se rezidentom BiH.
