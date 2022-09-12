####
# Einstellungen - Konstanten, die nicht in Laufzeit verändert werden
####

####
# MS SQL Server
####

SQL_DRIVER_USED_VERSION_MS_DRIVER: str = "{ODBC Driver 18 for SQL Server}"
SQL_DRIVER_USED_VERSION_FreeTDS: str = "{FreeTDS}"
SQL_DRIVER_USED_VERSION_FreeTDS_VERSION: str = "7.4"

# Merkmal MetaLine aktive value
wawi_advertise_aktive_meta_keyword: str = 'ANZEIGEN=TRUE'

# Pfad zu lokaler Datenbank, die zum Speichern der Statistiken der Nutzung, sowie der Bewertung dient
local_db_path: str = "../db/sqlLiteDB.db"

####
# HTTP Server
####

# Lokaler HTTP SERVER LISTEN IP
local_http_server_ip: str = "0.0.0.0"
# Lokaler HTTP SERVER LISTEN Port
local_http_server_port: int = 8888
# Start Passwort zum Leeren des Logfiles
web_admin_init_pw: str = "pass"
# rename or delete logFile: ( RENAME | DELETE ):
log_file_delete_mode: str = "RENAME"

reset_before_update: bool = False

# Pfad zur Logdatei
log_file_path: str = './../doc/Logs/feinkostBarcodeScannerLog.log'

# Pfad zu Qt-Designer Formulardatei: Die Grafik wurde nämlich mithilfe des Qt Creators erstellt.
ui_file_path: str = "../designer-ui/form.ui"

# Höhe des roten Balkens, der den normalen Preis durchstreicht (für Sonderpreis) in Pixel
SPECIAL_PRICE_RED_LINE_HEIGHT: int = 5
# Abstand zwischen normalen Preis und Sonderpreis in Pixel
SPACE_BETWEEN_PRICE_AND_SPECIAL_PRICE: int = 10
# Schriftgröße des Sonderpreises
SPECIAL_PRICE_FONT_SIZE: int = 50
# PRODUKT Max Font Size in Pixel
PRODUCT_MAX_FONT_SIZE: int = 40

# Maximale Kurzbeschreibungszeichenlänge, wenn größer, dann zeig nur noch "Produkt Informationen:"
# -> Layout sonst nicht mehr schön (Bild wird zu klein, bzw Textfeld zu breit)
MAX_SHORT_DESCRIPTION_LENGTH: int = 50
