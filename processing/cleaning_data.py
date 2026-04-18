import uuid,json,xmltodict
import polars as pl


def rename_columns(df: pl.DataFrame, mapping: dict) -> pl.DataFrame:
    if mapping:
        columns_to_rename = {k: v for k, v in mapping.items() if k in df.columns}
        return df.rename(columns_to_rename)
    return df

def add_source_columns(df: pl.DataFrame, source_name: str) -> pl.DataFrame:
    if "source" not in df.columns:
        return df.with_columns(pl.lit(source_name).alias("source"))
    return df

def format_date_columns(df: pl.DataFrame, date_columns: list[str]) -> pl.DataFrame:
    if date_columns:
        for col_names in date_columns:
            if col_names in df.columns:
                df = df.with_columns(pl.col(col_names).cast(pl.Date, strict=False))
    return df

def column_to_drop(df: pl.DataFrame, target_columns: list[str]) -> pl.DataFrame:
    if target_columns:
        df = df.drop(target_columns)
    return df

import uuid

def generate_deterministic_uuid(df: pl.DataFrame, url_column: str = "id") -> pl.DataFrame:
    """
    Prend l'URL (qui est temporairement dans la colonne 'id' ou autre),
    la copie dans 'uri', puis remplace 'id' par un UUID déterministe.
    """
    if url_column not in df.columns:
        return df

    # On utilise map_elements pour appliquer uuid5 à chaque URL
    # On spécifie return_dtype=pl.String pour Polars
    df = df.with_columns(
        # 1. On sauvegarde l'URL d'origine dans la colonne 'uri'
        pl.col(url_column).alias("uri"),
        
        # 2. On transforme la colonne 'id' en UUID
        pl.col(url_column).map_elements(
            lambda url: str(uuid.uuid5(uuid.NAMESPACE_URL, str(url))),
            return_dtype=pl.String
        ).alias("id")
    )
    
    return df

def normalize_data(
        raw_data: list[dict], 
        source_name: str, 
        column_mapping: dict = None,
        date_columns: list[str] = None,
        columns_drop: list[str] = None
) -> list[dict]:
    """
    Normalise les données brutes. Le renommage des colonnes (column_mapping) est optionnel.
    """
    if not raw_data:
        return []
    df = pl.DataFrame(raw_data)
    
    df = rename_columns(df, column_mapping)
    df = add_source_columns(df, source_name)
    df = format_date_columns(df, date_columns)
    df = column_to_drop(df,columns_drop)
    df = generate_deterministic_uuid(df, url_column="id")
    return df.to_dicts()