import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "12345",  # Ajuste aqui se sua senha for diferente
    "database": "grip"
}

def test_db():
    print("Tentando conectar ao banco de dados...")
    try:
        connection = pymysql.connect(**DB_CONFIG)
        print("✅ Conexão bem-sucedida!")
        
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"Tabelas encontradas: {tables}")
            
        connection.close()
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    test_db()
