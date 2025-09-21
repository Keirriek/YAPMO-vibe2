# Version 1.0.0 Werkend

"""
Database Manager

Responsible for adding new images and associated data to the db as well as checking to see whether or not the db is correctly intialized.


"""

import sqlite3
import logging
import globals
import os
glob_cnt=0
class DBManager :

    def __init__(self,dbname, primaryTableName, _reinit = False):
        self.dbname = globals.config_data['db']
        self.primaryTableName = globals.config_data['dbtable_media']
        self.directoryTableName = globals.config_data['dbtable_dirs']
        self.connection = sqlite3.connect(self.dbname)
        self.cursor = self.connection.cursor()

        ### STANDARD INITIALIZATION ###
        # Check if primary table exists
        # If it does not, create it
        if not self.checkIfTableExists(self.primaryTableName):
            if globals.config_data['logging']:
                globals.log_content.append(f"[INFO] Table {self.primaryTableName} does not exists!")
            self.createPrimaryTable()
        if not self.checkIfTableExists(self.directoryTableName):
            if globals.config_data['logging']:
                globals.log_content.append(f"[INFO] Table {self.directoryTableName} does not exists! Creating it now")
            self.createDirectoryTable()

        if _reinit:
            self.dropTable(self.primaryTableName)
            self.createPrimaryTable()
            self.dropTable(self.directoryTableName)
            self.createDirectoryTable()
    def createDirectoryTable(self, tname=None):
        try:
            sql = """

                CREATE TABLE {tname} (
                    id INTEGER PRIMARY KEY,
                    dirname text,
                    dirpath text UNIQUE,
                    filecount int,
                    fully_searched int DEFAULT 0
                )
            
            """.format(tname=tname if not tname == None else self.directoryTableName)

            if globals.config_data['logging']:
                globals.log_content.append(f"[INFO] Directory {self.directoryTableName} table created")
            res = self.cursor.execute(sql)
        except Exception as e:
            print(e)
            # raise Exception(f"ERROR CREATING PRIMARY TABLE - {e}")

    def addDirectoryInfoToTable(self, dirInfo, tname=None):
        try:
            sql = """
                INSERT INTO {tname}(dirname, dirpath, filecount)
                VALUES(?,?,?)
            """.format(tname=tname if not tname == None else self.directoryTableName)
            self.cursor.execute(sql, dirInfo)
            self.connection.commit()
        except Exception as e:
            globals.log_content.append(f"[ERROR] Error adding directory info to table - {e}")
            raise Exception(f"Error adding directory info to table - {e}")
    def checkIfTableExists(self, tname):
        if globals.config_data['logging']:
            globals.log_content.append(f"[INFO] Checking if Table {tname} exists...")

        try:
            self.cursor.execute(f'SELECT count(name) FROM sqlite_master WHERE type=\'table\' AND name=\'{tname}\'')
            return self.cursor.fetchone()[0] == 1

        except Exception as e:
            raise Exception(f"ERROR CHECKING FOR TABLE EXISTENCE - {str(e)}")

        return False

    def addMediaDataToDB(self, mediaInfo, tname=None):
        if mediaInfo is None:
            glob_cnt+=1
            globals.log_content.append(f'[INFO] MediaInfo in None {glob_cnt}')#RM test print
            print(f'MediaInfo in None {glob_cnt}') #RM test print
            return
        try:
            field_map=globals.config_data['dbtable_fields_file']
            field_map.update(globals.config_data['dbtable_fields_video'])
            field_map.update(globals.config_data['dbtable_fields_image'])
            # Bouw data dictionary voor database
            data = {}
            # Find the key values for the file name and path
            rev_dictionary = {value: key for key, value in globals.config_data['dbtable_fields_file'].items()}
            file_name_key_value=rev_dictionary.get('FILE_Name','ERROR_FIELD')
            file_path_key_value=rev_dictionary.get('FILE_Path','ERROR_FIELD')
            file_name = mediaInfo.get(file_name_key_value) #TP dit deel eruit >>or mediaInfo.get('name', '')
            file_path = mediaInfo.get(file_path_key_value) #TP dit deel eruit >> or mediaInfo.get('filepath_original', '')#TODO Keep File+path_original
            #
            #TODO ExifTools return SourcePath
            fqpn = mediaInfo.get('SourceFile') or mediaInfo.get('File:Directory') # Probeer eerst de bestaande fqpn
            
            if not fqpn and file_path and file_name:
                fqpn = os.path.join(file_path, file_name)
            
            data['YAPMO_FQPN'] = fqpn if fqpn else 'nil'
            
            # Dan de rest van de velden
            for exif_key, db_field in field_map.items():
                value = mediaInfo.get(exif_key)
                if value is None:
                    old_key = exif_key.split(':')[-1].lower()
                    value = mediaInfo.get(old_key, 'nil')
                
                if isinstance(value, list):
                    value = ', '.join(str(x) for x in value)
                
                data[db_field] = value if value is not None else 'nil'
            
            # Bouw SQL query
            fields = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            values = list(data.values())
            sql = f"""
                INSERT INTO {tname if tname else self.primaryTableName}
                ({fields}) VALUES ({placeholders})
            """
            # print(f"sql: {sql}") # DEBUG
            self.cursor.execute(sql, values)
            self.connection.commit()
            
        except sqlite3.IntegrityError as e:
            logging.info(f"Record already in DB, skipped: {data.get('FQPN', 'unknown')}")
        except Exception as e:
            globals.log_content.append(f"[ERROR] There was an error adding that info to the db - {str(e)}")
            raise
    
    
    def createPrimaryTable(self, tname=None):
        if globals.config_data['logging']:
            globals.log_content.append(f"[INFO] Creating table {tname if not tname == None else self.primaryTableName}")

        try:
            fields = {}
            fields.update(globals.config_data.get('dbtable_fields_file', {}))
            fields.update(globals.config_data.get('dbtable_fields_image', {}))
            fields.update(globals.config_data.get('dbtable_fields_video', {}))
            
            # Bouw SQL velden string voor Media tabel
            field_definitions = [
                "id INTEGER PRIMARY KEY",
                "YAPMO_FQPN TEXT UNIQUE",
                *[f"{field_name} TEXT DEFAULT 'nil'" for field_name in fields.values()]
            ]
            
            # Maak Media tabel
            sql = f"""
                CREATE TABLE {tname if not tname == None else self.primaryTableName} (
                    {', '.join(field_definitions)}
                )
            """
            self.cursor.execute(sql)
            
            # Maak Media_New tabel met extra velden
            media_new_fields = field_definitions.copy()

            
            sql_new = f"""
                CREATE TABLE {globals.config_data['dbtable_media_new']} (
                    {', '.join(media_new_fields)}
                )
            """
            self.cursor.execute(sql_new)
            
            if globals.config_data['logging']:
                globals.log_content.append(f"[INFO] Media table created")
                globals.log_content.append(f"[INFO] Media_New table created with additional fields")

        except Exception as e:
            globals.log_content.append(f"[ERROR] Error creating tables - {e}")
            raise Exception(f"ERROR CREATING TABLES - {e}")

    def dropTable(self, tname=None):

        if tname == None:
            globals.log_content.append(f"[ERROR] Please provide a table name")
            raise Exception("Please provide a table name")

        try:
            if self.checkIfTableExists(tname):

                logging.info("Table exists. Dropping...")
                if globals.config_data['logging']:
                    globals.log_content.append(f"[INFO] Table exists. Dropping...")
                self.cursor.execute(f'DROP TABLE {tname}')

                res = self.connection.commit()

            else:

                if globals.config_data['logging']:
                    globals.log_content.append(f"[INFO] Table does not exists.")
        
        except Exception as e:
            globals.log_content.append(f"[ERROR] Error in creating primary table - {e}")
            raise Exception(f"ERROR CREATING PRIMARY TABLE - {e}")

    def closeConnection(self):

        if globals.config_data['logging']:
            globals.log_content.append(f"[INFO] Closing connection to db...")

        try:
            self.connection.close()
            logging.info("DB Connection closed!")
            if globals.config_data['logging']:
                globals.log_content.append(f"[INFO] DB Connection closed!")
        except Exception as e:
            globals.log_content.append(f"[ERROR] Error closing db connection - {str(e)}")
            raise Exception(f"ERROR CLOSING DB CONNECTION - {str(e)}")
    
    def getAllRowsFromTable(self, tname=None):

        res = self.cursor.execute(f"SELECT * FROM {tname if not tname is None else self.primaryTableName}")
        print('Get All rows', res) #JM
        return res.fetchall()

    def findDuplicates(self):

        res = self.cursor.execute(f'SELECT * FROM {self.primaryTableName} WHERE hash IN (SELECT hash FROM {self.primaryTableName} GROUP BY hash HAVING COUNT(*) > 1)')
        print('Find Duplicates', res) #JM
        return res.fetchall()