





class DataBaseManager:
    
    def __init__():

        import pyodbc

        # cnxn = pyodbc.connect("DRIVER={ODBC Driver 18 for SQL Server};"
        #                      "Server=PC-MARKUS;"
        #                      "Database=PC-MARKUS;"
        #                      "Trusted_Connection=yes;"
        #                      "uid=test;pwd=altinsystems;")

        cnxn = pyodbc.connect(driver='{ODBC Driver 18 for SQL Server}', host="PC-MARKUS", database="Mandant_1",
                              trusted_connection="yes", user="test", password="altinsystems", encrypt="no")

        cursor = cnxn.cursor()
        cursor.execute('SELECT * FROM ArtikelVerwaltung.vArtikelliste')

        for row in cursor:
            print('row = %r' % (row,))

        columns = [column[0] for column in cursor.description]

        for column in columns:
            print(column)

        # kArtikel kStueckliste kVaterArtikel kArtikelForKategorieArtikel Artikelnummer Sortiernummer Artikelname Einheit EAN Herkunftsland UNNUmmer cHAN Gefahrennummer ISBN ASIN TaricCode UPC Hersteller Lieferstatus Breite Hoehe Laenge Erstelldatum

        Ich
        habe
        gestern
        noch
        JTL
        bei
        mir
        installiert.Mit
        dem
        Microsoft
        SQL
        Server
        Management
        Studio
        bin
        ich
        dann
        auch
        die
        Datenbanken
        durchgegangen.

        Jedoch
        weiß
        ich
        nicht, welche
        Informationen
        Sie
        zu
        ihren
        Produkten
        alles
        gespeichert
        haben, und
        auch
        nicht,

        welche
        später
        auf
        dem
        Bildschirm
        angezeigt
        werden
        sollen.

        Wäre
        es
        vielleicht
        möglich, das
        alles in der
        nächsten
        Zeit, zum
        Beispiel
        über
        eine
        Videokonferenz
        zu
        klären?






