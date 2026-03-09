from sqlalchemy import Table, Column, String, Text, DateTime, MetaData, JSON
from sqlalchemy import insert

def upsert_data(data : list[dict], index_elements, table : Table, engine):
    with engine.begin() as conn:
        #Insertion query for PostgresSQL
        stmt = insert(table).values(data)
        
        # On crée un dictionnaire qui dit : "Pour chaque colonne (sauf l'id), 
        # prends la nouvelle valeur qui a été 'exclue' et mets la à jour."
        update_dict = {
            col.name for col in stmt.excluded if col.name not in index_elements
        }

        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
        
        conn.execute(stmt)
        print(f"{len(data)} succesfuly treated inside table {table}")