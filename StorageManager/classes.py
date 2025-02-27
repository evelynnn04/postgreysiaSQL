import pickle
import os
import copyhttps://github.com/evelynnn04/postgreysiaSQL/pull/54/conflict?name=StorageManager%252Fclasses.py&ancestor_oid=c7a81f15c66fd8fff068119c334a1688e303dade&base_oid=9c355de1224293603b7e387fcf67ae0c31ac92f5&head_oid=9710a9cba9b4b4cf0138f208d36010315e9bc609
from .Bplus import BPlusTree
from .Hash import HashTable
from QueryProcessor.Rows import Rows

class Condition:
    valid_operations = ["=", "<>", ">", ">=", "<", "<=", "!"] # untuk sementara "!" berarti no operation
    def __init__(self, column:str, operation:str, operand:int|str) -> None:
        self.column = column
        if operation not in Condition.valid_operations:
            operation = "!"
        self.operation = operation
        self.operand = operand
    
    def evaluate(self, item:int|str):
        if self.operation == "=":
            return item == self.operand
        elif self.operation == "<>":
            return item != self.operand
        elif self.operation == ">":
            return item > self.operand
        elif self.operation == ">=":
            return item >= self.operand
        elif self.operation == "<":
            return item < self.operand
        else:
            return item <= self.operand

class DataRetrieval:
    def __init__(self, tables:list[str], columns:list[str], conditions:list[Condition]) -> None:
        self.table = tables
        self.column = columns
        self.conditions = conditions

class DataWrite:
    def __init__(self, table:list[str], column:list[str], conditions:list[Condition], new_value:object) -> None:
        self.table = table
        self.column = column
        self.conditions = conditions
        self.new_value = new_value

class DataDeletion:
    def __init__(self, table:str, conditions:list[Condition]) -> None:
        self.table = table
        self.conditions = conditions

class Statistic:
    def __init__(self, n_r:int, b_r:int, l_r:int, f_r:int, V_a_r:dict[str, int], col_data_type:dict[str, str] = None, col_index:dict[str,(int, int)] = None, col_bplus_tree_level:dict[str, int] = None) -> None:
        """
        Mengembalikan statistik dari sebuah tabel
        Param : database_name (string), table_name (string)

        Contoh : storageEngine.get_stats("database1", "users")

        Statistik yang dihasilkan :
        1. n_r : int ==> jumlah tuple dalam tabel
        2. b_r : int ==> jumlah blok yang berisi tuple dalam tabel
        3. l_r : int ==> ukuran satu tuple dalam tabel
        4. f_r : int ==> blocking factor (jumlah tuple dalam satu blok)
        5. V_a_r : dict[str, int] ==> jumlah nilai unik dari setiap atribut dalam tabel
                            contoh keluaran : {"id_user" : 100, "nama_user" : 50}
        6. col_data_type: dict[str, str]  ==> tipe data dari setiap kolom dalam tabel
                            contoh keluaran : {"id_user" : "INTEGER", "nama_user" : "TEXT"}
        7. col_index : dict[str, (int, int)] ==> index yang ada pada setiap kolom dalam tabel
                            format keluaran : 
                            - nama kolom (str)
                            - ada index bplus atau tidak (0 = tidak ada, 1 = ada)
                            - ada index hash atau tidak (0 = tidak ada, 1 = ada)
                            contoh keluaran : {"id_user" : (1,1), "nama_user" : (0,1)}
        8. col_bplus_tree_level : dict[str, int] ==> level dari B+ tree yang ada pada setiap kolom dalam tabel
                            contoh keluaran : {"id_user" : 2, "nama_user" : 3}
        """
        self.n_r = n_r
        self.b_r = b_r
        self.l_r = l_r
        self.f_r = f_r
        self.V_a_r = V_a_r
        self.col_data_type = col_data_type 
        self.col_index = col_index
        self.col_bplus_tree_level = col_bplus_tree_level

    @staticmethod
    def print_statistics(self):
        print(f"Number of tuples in relation r: {self.n_r}")
        print(f"Number of blocks containing tuples of r: {self.b_r}")
        print(f"Size of tuple of r : {self.l_r}")
        print(f"Blocking Factor : {self.b_r}")
        print(f"Number of distinct values that appear in r for attribute A: {self.V_a_r}")


class StorageEngine:
    def __init__(self) -> None:
        self.load()
        self.load_indexes()
        self.buffer = {}
        self.buffer_index = {}

    def get_database_names(self) -> list[str]:
        """
        Mengembalikan seluruh database yang ada
        """
        databases = []
        if self.blocks != {}:
            for database in self.blocks:
                databases.append(database)
        return databases
    
    def get_tables_of_database(self, database_name:str) -> list[str]:
        """
        Mengembalikan seluruh table dalam database
        Param : database_name (string)

        Contoh : storageEngine.get_tables_of_database("database1")
        """
        if database_name not in self.blocks:
            raise ValueError(f"Database '{database_name}' does not exist.")
        tables = []
        for table in self.blocks[database_name] :
            tables.append(table)
        return tables
    
    def get_columns_of_table(self, database_name:str, table_name:str) -> list[str]:
        """
        Mengembalikan seluruh kolom dalam sebuah table
        Param : database_name (string), table_name (string)

        Contoh : storageEngine.get_columns_of_table("database1", "users")
        """
        if database_name not in self.blocks:
            raise ValueError(f"Database '{database_name}' does not exist.")
        if table_name not in self.blocks[database_name]:
            raise ValueError(f"Table '{table_name}' does not exist.")
        columns = []
        for column in self.blocks[database_name][table_name]["columns"]:
            columns.append(column["name"])
        return columns
    
    def get_tables_and_columns_info(self, database_name:str) -> dict:
        """
        Mengembalikan seluruh table dan kolom dalam database
        Param : database_name (string)

        Contoh : storageEngine.get_tables_and_columns_info("database1")
        """
        if database_name not in self.blocks:
            raise ValueError(f"Database '{database_name}' does not exist.")
        tables = {}
        for table in self.blocks[database_name]:
            tables[table] = []
            for column in self.blocks[database_name][table]["columns"]:
                tables[table].append(column["name"])
        return tables
    
    def get_table_metadata(self, database_name:str, table_name:str) -> dict:
        """
        Mengembalikan metadata sebuah table
        Param : database_name (string), table_name (string)

        Contoh : storageEngine.get_table_metadata("database1", "users")
        """
        if database_name not in self.blocks:
            raise ValueError(f"Database '{database_name}' does not exist.")
        if table_name not in self.blocks[database_name]:
            raise ValueError(f"Table '{table_name}' does not exist.")
        return self.blocks[database_name][table_name]['columns']
    
    def load(self) -> None:
        """
        fungsi buat ngebaca disk dan diimport ke variabel\n
        Jangan dipakai (kecuali sangat butuh), fungsi ini cukup dipanggil sekali saat __init__
        """
        try:
            if not (os.path.isfile("data.dat")):
                pickle.dump({}, open("data.dat", "wb"))
            self.blocks = pickle.load(open("data.dat", "rb"))
        except Exception as e:
            print(f"error, {str(e)}")

    def commit_buffer(self, transaction_id:int) -> None:
        """
        fungsi untuk commit transaction_id buat disave ke file utama
        """
        try:
            tempBlocks = self.buffer.get(transaction_id, [])
            if tempBlocks != []:
                self.blocks = tempBlocks
                self.buffer.pop(transaction_id)
            tempIndexes = self.buffer_index.get(transaction_id, [])
            if tempIndexes != []:
                self.indexes = tempIndexes
                self.buffer_index.pop(transaction_id)
        except Exception as e:
            print(f"error, {str(e)}")

    def load_indexes(self) -> None:
        """
        fungsi untuk hold semua data index hasil load dari storage (indexes.dat)
        """
        try:
            if not os.path.isfile("indexes.dat"):
                pickle.dump({}, open("indexes.dat", "wb"))
            self.indexes = pickle.load(open("indexes.dat", "rb"))
        except Exception as e:
            print(f"Error initializing indexes: {str(e)}")
            self.indexes = {}

    def save(self) -> None:
        """
        bakal ngedump file utama di variabel ke file binary (data.dat)
        """
        try:
            pickle.dump(self.blocks, open("data.dat", "wb"))
        except Exception as e:
            print(f"error, {str(e)}")

    def save_indexes(self):
        """
        dump file untuk simpan info index di variabel ke file binary (indexes.dat)
        """
        try:
            pickle.dump(self.indexes, open("indexes.dat","wb"))
        except Exception as e:
             print(f"error, {str(e)}")

    def create_database(self, database_name:str) -> bool:
        """
        bikin database baru, tinggal masuking string aja, misal "database1"
        """
        if database_name in self.blocks:
            return Exception(f"Sudah ada database dengan nama {database_name}")
        self.blocks[database_name] = {}
        return True
    
    def create_table(self, database_name:str, table_name:str, column_type:dict[str, str], informasi_tambahan:dict[str, list[str]]) -> bool|Exception:
        """
        bikin tabel baru\n
        database_name tinggal string, misal "database1"\n
        table_name tinggal string, misal "id_user"\n
        column_type isinya dict[nama_column, tipe_column], misal {"id_user" : "INTEGER", "nama_user" : "VARCHAR(255)"} (tolong caps untuk tipenya, biar bisa diitung bytenya)\n
        buat type nya, khusus VARCHAR harus pake argumen angka, misal "VARCHAR(100)"\n
        informasi_tambahan misal {"id_user" : ["PRIMARY KEY", "UNIQUE"], "nama_user" : ["UNIQUE", "FOREIGN KEY"]} 
        """
        if database_name in self.blocks:
            if table_name not in self.blocks[database_name]:
                self.blocks[database_name][table_name] = {
                    "columns" : [{"name" : nama_col, "type" : tipe_col} for nama_col, tipe_col in column_type.items()],
                    "values" : [[]],
                } 
                for info in informasi_tambahan:
                    for i in range(len(self.blocks[database_name][table_name]["columns"])):
                        if self.blocks[database_name][table_name]["columns"][i]["name"] == info:
                            self.blocks[database_name][table_name]["columns"][i]["constraints"] = informasi_tambahan[info]
                # 1 block berkapasitas 4096 byte, asumsi setiap record perlu 4 byte untuk overhead
                byte_per_record = 4
                for column in self.blocks[database_name][table_name]["columns"]:
                    if column["type"] == "INTEGER" or column["type"] == "FLOAT":
                        byte_per_record+=4
                    elif column["type"] == "CHAR":
                        byte_per_record+=1
                    elif "VARCHAR" in column["type"] or "CHAR" in column["type"]: # VARCHAR atau CHAR
                        byte_per_record += int(column["type"][8:(len(column["type"])-1)])
                    else:
                        return Exception("Ada tipe bentukan yang tidak cocok,", column["type"])
                self.blocks[database_name][table_name]["max_record"] = 4096//byte_per_record
                return True
            return Exception(f"Sudah ada table dengan nama {table_name} di database {database_name}")
        return Exception(f"Tidak ada database dengan nama {database_name}")
    
    def insert_data(self, database_name:str, table_name:str, data_insert:dict, transaction_id:int) -> bool|Exception:
        """
        ngeinsert data baru. (Tidak menghandle duplicate data.)\n
        database_name tinggal string, misal "database1"\n
        table_name tinggal string, misal "id_user"\n
        data_insert tuh isinya kaya {"id_user" : 1, "nama_user" : "mas fuad"}
        """
        if database_name in self.blocks:
            if table_name in self.blocks[database_name]:
                self.buffer[transaction_id] = self.buffer.get(transaction_id, copy.deepcopy(self.blocks))
                temp = self.buffer[transaction_id][database_name][table_name]["values"]
                dimasukin = False
                for block in temp:
                    if len(block) < self.buffer[transaction_id][database_name][table_name]["max_record"]:
                        block.append(data_insert)
                        dimasukin = True
                        break
                if not dimasukin:
                    temp.append([data_insert]) 
                self.buffer[transaction_id][database_name][table_name]["values"] = temp
                return True
            return Exception(f"Tidak ada table dengan nama {table_name} di database {database_name}")
        return Exception(f"Tidak ada database dengan nama {database_name}")

    def initialize_index_structure(self, database_name:str, table_name:str, column:str) -> None:
        """
        Struktur index hasil load_indexes :
        1. Jika kolom tidak memiliki index : self.indexes[database_name][table_name][column]
        2. Jika kolom memiliki index B+ tree : self.indexes[database_name][table_name][column]["bplus"][tree]
        3. Jika kolom memiliki index Hash : self.indexes[database_name][table_name][column]["hash"][hash table]
        Sebuah kolom bisa tidak memiliki index, memiliki salah satu, ataupun keduanya.
        """
        if database_name not in self.indexes:
            self.indexes[database_name] = {}
        if table_name not in self.indexes[database_name]:
            self.indexes[database_name][table_name] = {}
        if column not in self.indexes[database_name][table_name]:
            self.indexes[database_name][table_name][column] = {}

    def read_block(self, data_retrieval:DataRetrieval, database_name:str, transaction_id:int) -> Rows|Exception:
        """
        Bakal ngeread block dan akan mereturn tipe bentukan Row (liat QueryProcessor/Rows.py)\n
        untuk argumennya silahkan liat tipe bentukan DataRetrieval di atas\n
        akan mencoba mereturn data hasil edit transaction_id, jika tidak ada, akan direturn data default.\n
        kalo mau ngambil data default, kasih transaction_id = -1 (atau angka apapun yang gaakan dipakai untuk transaction_id)
        """
        # error handling
        if database_name not in self.blocks:
            return Exception(f"Tidak ada database dengan nama {database_name}")
        for tabel in data_retrieval.table:
            if tabel not in self.blocks[database_name]:
                return Exception(f"Tidak ada tabel dengan nama {tabel}")
        column_tabel_query = []
        for tabel in data_retrieval.table:
            for kolom in self.blocks[database_name][tabel]["columns"]:
                column_tabel_query.append(kolom["name"])
        for kolom in data_retrieval.column:
            if kolom not in column_tabel_query:
                return Exception(f"Tidak ada kolom dengan nama {kolom}")
        if data_retrieval.conditions:
            for kondisi in data_retrieval.conditions:
                if kondisi.column not in column_tabel_query:
                    return Exception(f"Tidak ada kolom dengan nama {kondisi.column}")

        # di bawah ini, udah pasti tidak ada error dari input

        # cross terlebih dahulu dari tabel-tabel yang dipilih

        data_dibaca = self.buffer.get(transaction_id, copy.deepcopy(self.blocks))

        hasil_cross = []
        for blocks in data_dibaca[database_name][data_retrieval.table[0]]["values"]:
            for records in blocks:
                hasil_cross.append(records) 
        for tabel_lainnya in data_retrieval.table[1:]:
            temp = []
            for blocks in data_dibaca[database_name][tabel_lainnya]["values"]:
                for records in blocks:
                    temp.append(records)
            temp_hasil = []
            for row_hasil_cross in hasil_cross:
                for row_hasil_temp in temp:
                    temp_hasil.append({**row_hasil_cross, **row_hasil_temp})
            hasil_cross = temp_hasil

        # lalu hapus data dari hasil_cross yang tidak memenuhi kondisi
        hasil_operasi = []
        if data_retrieval.conditions:
            for kondisi in data_retrieval.conditions:
                for row in hasil_cross:
                    if kondisi.evaluate(row[kondisi.column]):
                        hasil_operasi.append(row)
        else:
            hasil_operasi = hasil_cross

        # lalu ambil hanya kolom yang diinginkan
        if data_retrieval.column:
            hasil_akhir = [{key: d[key] for key in data_retrieval.column if key in d} for d in hasil_operasi]
        else: 
            hasil_akhir = hasil_operasi
        # return akhir
        return Rows(hasil_akhir, len(hasil_akhir), str(data_retrieval.table))

    def write_block(self, data_write: DataWrite, database_name: str, transaction_id: int) -> int | Exception:
        """
        Bakal ngewrite block yang masuk condition (operasinya AND) dan akan mereturn berapa row affected\n
        untuk argumennya silahkan liat tipe bentukan DataWrite di atas\n
        akan mencoba mengedit data hasil transaksi sebelumnya di transaction_id\n
        jika tidak ada, akan mengedit data default dan hasilnya disimpan di buffer transaction_id
        """
        if database_name not in self.blocks:
            return Exception(f"Tidak ada database dengan nama {database_name}")
        
        affected_rows_total = 0  # Total baris yang diubah

        for table in data_write.table:
            if table not in self.blocks[database_name]:
                return Exception(f"Tidak ada tabel dengan nama {table} di database {database_name}")
            
            column_tabel_query = [col["name"] for col in self.blocks[database_name][table]["columns"]]
            if data_write.conditions:
                for kondisi in data_write.conditions:
                    if kondisi.column not in column_tabel_query:
                        return Exception(f"Tidak ada kolom dengan nama {kondisi.column} di tabel {table}")
            if not all(key in column_tabel_query for key in data_write.column):
                return Exception(f"Beberapa kolom yang akan diubah tidak ada di tabel {table}")
            
            # Tidak ada error, lanjutkan proses untuk tabel ini
            affected_rows = 0
            data_baru = []
            tempData = self.buffer.get(transaction_id, copy.deepcopy(self.blocks))
            for block in tempData[database_name][table]["values"]:
                block_baru = []
                for record in block:
                    update_row = False
                    recordBaru = copy.deepcopy(record)
                    if data_write.conditions:
                        # Cek apakah row memenuhi semua kondisi
                        update_row = all(kondisi.evaluate(recordBaru[kondisi.column]) for kondisi in data_write.conditions)
                    else:
                        # Jika tidak ada kondisi, semua baris akan diupdate
                        update_row = True

                    # Update nilai jika memenuhi kondisi
                    if update_row:
                        for col, value in zip(data_write.column, data_write.new_value):
                            recordBaru[col] = value
                        affected_rows += 1

                    block_baru.append(recordBaru)
                data_baru.append(block_baru)

            tempData[database_name][table]["values"] = data_baru
            self.buffer[transaction_id] = tempData

            affected_rows_total += affected_rows  # Tambahkan jumlah baris yang diubah untuk tabel ini
        
        print(f"Data berhasil diupdate, total {affected_rows_total} baris diubah di semua tabel")
        return affected_rows_total


    def delete_block(self, data_deletion:DataDeletion, database_name:str, transaction_id:int) -> int:
        """
        Bakal ngedelete data yang masuk condition (operasinya AND) dan akan mereturn berapa row affected\n
        untuk argumennya silahkan liat tipe bentukan DataDeletion di atas\n
        akan mencoba mengdelete data hasil transaksi sebelumnya di transaction_id\n
        jika tidak ada, akan mengdelete data default dan hasilnya disimpan di buffer transaction_id
        """
        # error handling
        if database_name not in self.blocks:
            return Exception(f"Tidak ada database dengan nama {database_name}")  
        if data_deletion.table not in self.blocks[database_name]:
            return Exception(f"Tidak ada tabel dengan nama {data_deletion.table}")
        column_tabel_query = []
        for kolom in self.blocks[database_name][data_deletion.table]["columns"]:
            column_tabel_query.append(kolom["name"])


        if data_deletion.conditions:
            for kondisi in data_deletion.conditions:
                if kondisi.column not in column_tabel_query:
                    return Exception(f"Tidak ada kolom dengan nama {kondisi.column}")
                
        # seharusnya tidak ada error di sini
        data_baru = []
        affected_row = 0
        tempData = self.buffer.get(transaction_id, copy.deepcopy(self.blocks))
        for block in tempData[database_name][data_deletion.table]["values"]:
            block_baru = []
            for record in block:
                if data_deletion.conditions:
                    if not (all(kondisi.evaluate(record[kondisi.column]) for kondisi in data_deletion.conditions)):
                        # berarti tidak memenuhi kondisi, bakal dicopy
                        block_baru.append(record)
                    else:
                        affected_row += 1
                else:
                    block_baru.append(record)
            data_baru.append(block_baru)
        
        # self.buffer[transaction_id] = copy.deepcopy(self.blocks)
        tempData[database_name][data_deletion.table]["values"] = data_baru 
        self.buffer[transaction_id] = tempData
        print(f"Data berhasil dihapus, {affected_row} baris dihapus")
        return affected_row
    
    def get_stats(self, database_name:str , table_name: str, block_size=4096) -> Statistic | Exception:
        """
        Mengembalikan statistik dari sebuah tabel
        Param : database_name (string), table_name (string)

        Contoh : storageEngine.get_stats("database1", "users")

        Statistik yang dihasilkan :
        1. n_r : int ==> jumlah tuple dalam tabel
        2. b_r : int ==> jumlah blok yang berisi tuple dalam tabel
        3. l_r : int ==> ukuran satu tuple dalam tabel
        4. f_r : int ==> blocking factor (jumlah tuple dalam satu blok)
        5. V_a_r : dict[str, int] ==> jumlah nilai unik dari setiap atribut dalam tabel
                            contoh keluaran : {"id_user" : 100, "nama_user" : 50}
        6. col_data_type: dict[str, str]  ==> tipe data dari setiap kolom dalam tabel
                            contoh keluaran : {"id_user" : "INTEGER", "nama_user" : "TEXT"}
        7. col_index : dict[str, [int, int]] ==> index yang ada pada setiap kolom dalam tabel
                            format keluaran : 
                            - nama kolom (str)
                            - ada index bplus atau tidak (0 = tidak ada, 1 = ada)
                            - ada index hash atau tidak (0 = tidak ada, 1 = ada)
                            contoh keluaran : {"id_user" : [1,1], "nama_user" : [0,1]}
        8. col_bplus_tree_level : dict[str, int] ==> level dari B+ tree yang ada pada setiap kolom dalam tabel
                            contoh keluaran : {"id_user" : 2, "nama_user" : 3}
        """

        if database_name not in self.blocks:
            raise ValueError(f"Tidak ada database dengan nama {database_name}")
        if table_name not in self.blocks[database_name]:
            raise ValueError(f"Tidak ada table dengan nama {table_name}")
        
        table = self.blocks[database_name][table_name]
        rows = table["values"]
        columns = table["columns"]

        # 1. nr
        nr = sum(len(block) for block in rows)

        # 2. lr
        type_size = {
        "INTEGER": 4,  # byte integer
        "TEXT": 50,  #misal max string lenth 50 char
        "FLOAT" : 4
        }

        lr = sum(type_size.get(col["type"], 0) for col in columns)

        # 3. fr
        fr = block_size // lr if lr > 0 else 0

        # 4. number of blocks
        br = (nr + fr -1) // fr if fr > 0 else 0

        # 5. V(A,r)
        V_a_r = {}

        for col in columns:
            attribute = col["name"]
            V_a_r[attribute] = len(set(row[attribute] for row in rows if attribute in row))

        return Statistic(n_r=nr, b_r=br, l_r=lr, f_r=fr, V_a_r=V_a_r)
    
    """
    ==============  INDEX FOR USE   ========================================================================================
    """
    
     # setindex ke buffer
    def set_index(self, database_name: str, table_name: str, column: str, transaction_id:int,index_type) -> None:
        if transaction_id not in self.buffer_index:
            self.buffer_index[transaction_id] = copy.deepcopy(self.indexes)
        if database_name not in self.buffer_index[transaction_id]:
            self.buffer_index[transaction_id][database_name] = {}
        if table_name not in self.buffer_index[transaction_id][database_name]:
            self.buffer_index[transaction_id][database_name][table_name] = {}
        if column not in self.buffer_index[transaction_id][database_name][table_name]:
            self.buffer_index[transaction_id][database_name][table_name][column] = {}
        if "bplus" not in self.buffer_index[transaction_id][database_name][table_name][column]:
            self.buffer_index[transaction_id][database_name][table_name][column]["bplus"] = None
        if "hash" not in self.buffer_index[transaction_id][database_name][table_name][column]:  
            self.buffer_index[transaction_id][database_name][table_name][column]["hash"] = None

        table = self.blocks[database_name][table_name]
        if index_type == "bplus":
            bplus_tree = self.create_bplus_index(table, column)
            self.buffer_index[transaction_id][database_name][table_name][column]["bplus"] = bplus_tree
        elif index_type == "hash":
            hash_index = self.create_hash_index(table, column)
            self.buffer_index[transaction_id][database_name][table_name][column]["hash"] = hash_index
        else:
            raise ValueError("Invalid index type. Only 'bplus' and 'hash' are supported.")
        print(f"Index of type '{index_type}' created for column '{column}' in table '{table_name}'.")

    def insert_key_value_to_index(self, database_name:str, table_name:str, column:str, key, block_index, offset, transaction_id:int) -> None:
        if self.is_bplus_index_exist(database_name, table_name, column, transaction_id):
            self.insert_bplus_index(database_name, table_name, column, key, block_index, offset, transaction_id)
        if self.is_hash_index_exist(database_name, table_name, column, transaction_id):
            self.insert_hash_index(database_name, table_name, column, key, block_index, offset, transaction_id)
    
    
    # def update_key_to_index(self, database_name:str, table_name:str, column:str, key, block_index, offset, transaction_id:int) -> None:
    #     if self.is_bplus_index_exist(database_name, table_name, column):
    #         self.update_bplus_index(database_name, table_name, column, key, block_index, offset, transaction_id)
    #     if self.is_hash_index_exist(database_name, table_name, column):
    #         self.update_key_hash_index(database_name, table_name, column, old_key, block_index, offset, transaction_id)

    def delete_key_value_from_index(self, database_name:str, table_name:str, column:str, key, transaction_id:int) -> None:
        if self.is_bplus_index_exist(database_name, table_name, column):
            self.delete_bplus_index(database_name, table_name, column, key, transaction_id)
        if self.is_hash_index_exist(database_name, table_name, column):
            self.delete_hash_index(database_name, table_name, column, key, transaction_id)

    def print_index_structure(self, database_name: str, table_name: str, column: str, transaction_id: int) -> None:
        # Check if a hash index exists in the block
        if self.is_hash_index_in_block(database_name, table_name, column):
            print("Hash Table in Block Index:")
            hash_index = self.indexes[database_name][table_name][column].get("hash")
            if hash_index is not None:
                hash_index.print_table()
            else:
                print("No hash index found in block.")
            print()

        # Check if a hash index exists in the buffer
        elif self.is_hash_index_in_buffer(database_name, table_name, column, transaction_id):
            print("Hash Table in Buffer Index:")
            hash_index = self.buffer_index[transaction_id][database_name][table_name][column].get("hash")
            if hash_index is not None:
                hash_index.print_table()
            else:
                print("No hash index found in buffer.")
            print()

        # Check if a BPlus index exists in the block
        if self.is_bplus_index_in_block(database_name, table_name, column):
            print("BPlus Tree in Block Index:")
            bplus_index = self.indexes[database_name][table_name][column].get("bplus")
            if bplus_index is not None:
                bplus_index.print_tree()
            else:
                print("No BPlus index found in block.")
            print()

        # Check if a BPlus index exists in the buffer
        elif self.is_bplus_index_in_buffer(database_name, table_name, column, transaction_id):
            print("BPlus Tree in Buffer Index:")
            bplus_index = self.buffer_index[transaction_id][database_name][table_name][column].get("bplus")
            if bplus_index is not None:
                bplus_index.print_tree()
            else:
                print("No BPlus index found in buffer.")
            print()

    """
    ==========================================================================================================================
    """
    def validate_column_buffer(self, database_name: str, table_name: str, column: str, trancaction_id:int) -> None:
        temp = self.buffer.get(trancaction_id, self.blocks)
        if database_name not in temp:
            if database_name not in self.blocks :
                raise ValueError(f"Database '{database_name}' does not exist.")
        if table_name not in temp[database_name] :
            if table_name not in self.blocks[database_name]:
                raise ValueError(f"Table '{table_name}' does not exist.")
            else :
                table = self.blocks[database_name][table_name]
        else :
            table = temp[database_name][table_name] 
        if not any(col["name"] == column for col in table["columns"]):
            raise ValueError(f"Column '{column}' does not exist in table '{table_name}'.")
        
    def bplus_locator(self, database_name: str, table_name: str, column: str, transaction_id:int) -> None:
        self.validate_column_buffer(database_name, table_name, column, transaction_id)
        if self.is_bplus_index_in_buffer(database_name, table_name, column, transaction_id): # index adanya di buffer
            return self.buffer_index[transaction_id][database_name][table_name][column]["bplus"]
        elif self.is_bplus_index_in_block(database_name, table_name, column): # index adanya di block
            return self.indexes[database_name][table_name][column]["bplus"]
        else :
            raise ValueError("BPlus index not found")
        
    def hash_locator(self, database_name: str, table_name: str, column: str, transaction_id:int) -> None :
        self.validate_column_buffer(database_name, table_name, column, transaction_id)
        if self.is_hash_index_in_buffer(database_name, table_name, column, transaction_id):
            return self.buffer_index[transaction_id][database_name][table_name][column]["hash"]
        elif self.is_hash_index_in_block(database_name, table_name, column):
            return self.indexes[database_name][table_name][column]["hash"]
        else :
            raise ValueError("Hash index not found")

    def is_hash_index_in_buffer(self, database_name: str, table_name: str, column: str, transaction_id:int) -> bool:
        try:
            return (
                transaction_id in self.buffer_index and
                database_name in self.buffer_index[transaction_id] and
                table_name in self.buffer_index[transaction_id][database_name] and
                column in self.buffer_index[transaction_id][database_name][table_name] and
                "hash" in self.buffer_index[transaction_id][database_name][table_name][column]
            )
        except KeyError:
            return False
    
    def is_hash_index_in_block(self, database_name: str, table_name: str, column: str) -> bool:
        if database_name in self.indexes and \
            table_name in self.indexes[database_name] and \
            column in self.indexes[database_name][table_name]:
            return self.indexes[database_name][table_name][column].get("hash") is not None
        # Return False if any part of the path is missing
        return False
    
    def is_bplus_index_in_buffer(self, database_name: str, table_name: str, column: str, transaction_id:int) -> bool:
        try:
            return (
                transaction_id in self.buffer_index and
                database_name in self.buffer_index[transaction_id] and
                table_name in self.buffer_index[transaction_id][database_name] and
                column in self.buffer_index[transaction_id][database_name][table_name] and
                "bplus" in self.buffer_index[transaction_id][database_name][table_name][column]
            )
        except KeyError:
            return False
    
    def is_bplus_index_in_block(self, database_name: str, table_name: str, column: str) -> bool:
        return self.indexes[database_name][table_name][column]["bplus"] is not None

    def create_bplus_index(self, table : dict, column: str):
        bplus_tree = BPlusTree(order=4)
        for block_index, block in enumerate(table["values"]):
            for offset, row in enumerate(block):
                if column not in row:
                    raise ValueError(f"Column '{column}' is missing in a row of the table.")
                key = row[column]
                bplus_tree.insert(key,(block_index,offset))
        return bplus_tree
    
    # setelah insert delete
    def is_bplus_index_exist(self, database_name: str, table_name: str, column: str, transaction_id: int) -> bool:
        temp = self.buffer_index.get(transaction_id, self.indexes)
        # for _, dbs in self.buffer_index.items():
        #     if database_name not in dbs:
        #         continue
        #     if table_name not in dbs[database_name]:
        #         continue
        #     if column not in dbs[database_name][table_name]:
        #         continue
        #     if "bplus" in dbs[database_name][table_name][column]:
        #         if dbs[database_name][table_name][column]["bplus"] is not None:
        #             return True
        for _, dbs in temp.items():
            if table_name not in dbs:
                continue
            if column not in dbs[table_name]:
                continue
            if "bplus" in dbs[table_name][column]:
                if dbs[table_name][column]["bplus"] is not None:
                    return True
        return False
    
    def is_hash_index_exist(self, database_name: str, table_name: str, column: str, transaction_id: int) -> bool:
        temp = self.buffer_index.get(transaction_id, self.indexes)
        # for transaction_id, dbs in self.buffer_index.items():
        #     if database_name not in dbs:
        #         continue
        #     if table_name not in dbs[database_name]:
        #         continue
        #     if column not in dbs[database_name][table_name]:
        #         continue
        #     if "bplus" in dbs[database_name][table_name][column]:
        #         if dbs[database_name][table_name][column]["hash"] is not None:
        #             return True
        for _, dbs in temp.items():
            if table_name not in dbs:
                continue
            if column not in dbs[table_name]:
                continue
            if "bplus" in dbs[table_name][column]:
                if dbs[table_name][column]["bplus"] is not None:
                    return True
        return False
    
    def insert_bplus_index(self,database_name:str,table_name:str,column:str,key,block_index,offset,transaction_id : int):
        if transaction_id not in self.buffer_index:
            self.buffer_index[transaction_id] = copy.deepcopy(self.indexes)
        index : BPlusTree = self.buffer_index[transaction_id][database_name][table_name][column]['bplus']
        index.insert(key,(block_index,offset))

    def delete_bplus_index(self,database_name:str,table_name:str,column:str,key,transaction_id : int):
        if transaction_id not in self.buffer_index:
            self.buffer_index[transaction_id] = copy.deepcopy(self.indexes)
        index : BPlusTree = self.buffer_index[transaction_id][database_name][table_name][column]['bplus']
        index.delete(key)

    # panggil kalau yang diupdate search keynya
    def update_bplus_index(self,database_name:str,table_name:str,column:str,key,block_index,offset,transaction_id : int):
        self.delete_bplus_index(database_name,table_name,column,key,transaction_id)
        self.insert_bplus_index(database_name,table_name,column,key,block_index,offset,transaction_id)

    def search_bplus_index(self,database_name:str,table_name:str,column:str,key,transaction_id : int) -> list:
        self.validate_column_buffer(database_name,table_name,column,transaction_id)
        if transaction_id not in self.buffer_index:
            self.buffer_index[transaction_id] = copy.deepcopy(self.indexes)
        index : BPlusTree = self.buffer_index[transaction_id][database_name][table_name][column]['bplus']
        result_indices = index.search(key)
        if result_indices :
            real_value = self.get_value_for_position(database_name, table_name, result_indices[0], result_indices[1], transaction_id)
            return real_value
        else :
            return None
        # return result_indices

    def search_bplus_index_range(self, database_name:str,table_name:str, column:str,  transaction_id:int,start,end) -> list:
        self.validate_column_buffer(database_name,table_name,column,transaction_id)
        if transaction_id not in self.buffer_index:
            self.buffer_index[transaction_id] = copy.deepcopy(self.indexes)
        index : BPlusTree = self.buffer_index[transaction_id][database_name][table_name][column]['bplus']
        result_indices = index.search_range(start, end)
        if result_indices :
            real_values = []
            for result in result_indices:
                real_value = self.get_value_for_position(database_name, table_name, result[0], result[1], transaction_id)
                real_values.append(real_value)
            return real_values
        else :
            return None
    
    def create_hash_index(self, table: dict, column: str):
        hash_index = HashTable(size=10)
        for block_index, block in enumerate(table["values"]):
            for offset, row in enumerate(block):
                if column not in row:
                    raise ValueError(f"Column '{column}' is missing in a row of the table.")
                key = row[column]
                hash_index.insert(key,(block_index,offset))
        return hash_index
    
    def insert_hash_index(self, database_name:str, table_name:str, column:str, key, block_index, offset, transaction_id : int):
        index = self.hash_locator(database_name, table_name, column, transaction_id)
        index.insert(key, (block_index, offset))
        if index.search(key).count((block_index, offset)) == 0:
            raise ValueError("Error in inserting to hash index")

    def search_hash_index(self,database_name:str,table_name:str,column:str,key,transaction_id : int):  
        index = self.hash_locator(database_name, table_name, column, transaction_id)
        result_indices = index.search(key)
        if result_indices:
            real_values = []
            for result in result_indices:
                real_value = self.get_value_for_position(database_name, table_name, result[0], result[1], transaction_id)
                real_values.append(real_value)
            return real_values
        else :
            return None

    def delete_hash_index(self, database_name:str, table_name:str, column:str, key, transaction_id : int):
        index = self.hash_locator(database_name, table_name, column, transaction_id)
        removed_value = index.delete_key(key)
        return removed_value

    def update_key_hash_index(self,database_name:str,table_name:str,column:str, old_key, new_key, transaction_id : int):
        removed_value = self.delete_hash_index(database_name,table_name,column, old_key,transaction_id)
        for value in removed_value :
            self.insert_hash_index(database_name, table_name, column, new_key, value[0], value[1], transaction_id)
    
    def get_value_for_position(self, database_name:str, table_name:str, block_index, offset, transaction_id:int):
        if transaction_id not in self.buffer_index:
            self.buffer_index[transaction_id] = copy.deepcopy(self.indexes)
        data = self.buffer[transaction_id][database_name][table_name]["values"]
        return data[block_index][offset]

    def debug(self):
        """cuma fungsi debug, literally ngeprint variabel"""
        print(self.blocks)

    def debug_buffer(self):
        print(self.buffer)

    def debug_indexes(self):
        """cuma fungsi debug, literally ngeprint variabel"""
        print(self.indexes)

    def debug_buffer_index(self):
        print(self.buffer_index)