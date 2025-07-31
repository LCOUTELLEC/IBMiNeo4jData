#!/usr/bin/env python3
"""
Script de préparation des fichiers Excel ARCAD vers CSV pour Neo4j
Auteur: Assistant IA
Date: 2025
"""

import pandas as pd
import os
from pathlib import Path

def clean_string(value):
    """Nettoie les chaînes de caractères"""
    if pd.isna(value):
        return ""
    return str(value).strip()

def convert_date(date_value):
    """Convertit les dates ARCAD (AAAAMMJJ) vers format ISO"""
    if pd.isna(date_value) or date_value == 0:
        return ""
    
    date_str = str(int(date_value))
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return ""

def prepare_sources_csv(input_file, output_dir):
    """Prépare le fichier des sources"""
    print(f"Programmes sauvegardés: {len(df_programmes)} lignes -> {output_programmes}")
    
    # Tables (*FILE avec PF ou TABLE)
    df_tables = df_filtered[
        (df_filtered['LST_CTYPE'] == '*FILE') & 
        (df_filtered['LST_CATR'].isin(['PF', 'TABLE']))
    ].copy()
    output_tables = os.path.join(output_dir, 'IBMi_RefArcaddesObjets_Tables.csv')
    df_tables.to_csv(output_tables, index=False, encoding='utf-8')
    print(f"Tables sauvegardées: {len(df_tables)} lignes -> {output_tables}")
    
    return df_filtered, df_programmes, df_tables

def prepare_xref_csv(input_file, output_dir):
    """Prépare le fichier des références croisées"""
    print("Traitement du fichier XREF...")
    
    # Lecture du fichier Excel
    df = pd.read_excel(input_file, sheet_name=0)
    
    # Nettoyage des données
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(clean_string)
    
    # Filtrage des références pertinentes
    # Garder les relations Programme->Programme et Programme->Table
    df_filtered = df[
        ((df['OXR_FROM_TYPE'] == '*PGM') & (df['OXR_TO_TYPE'] == '*PGM')) |
        ((df['OXR_FROM_TYPE'] == '*PGM') & (df['OXR_TO_TYPE'] == '*FILE'))
    ].copy()
    
    # Sauvegarde
    output_file = os.path.join(output_dir, 'IBMi_RefArcaddesXREF.csv')
    df_filtered.to_csv(output_file, index=False, encoding='utf-8')
    print(f"XREF filtrées sauvegardées: {len(df_filtered)} lignes -> {output_file}")
    
    return df_filtered

def create_metadata_csvs(output_dir, df_objets):
    """Crée les fichiers CSV de métadonnées"""
    print("Création des fichiers de métadonnées...")
    
    # Applications uniques
    applications = df_objets['LST_CAPP'].unique()
    applications = [app for app in applications if app and app.strip()]
    df_apps = pd.DataFrame({
        'name': applications,
        'description': [f'Application {app}' for app in applications]
    })
    
    app_file = os.path.join(output_dir, 'applications.csv')
    df_apps.to_csv(app_file, index=False, encoding='utf-8')
    print(f"Applications sauvegardées: {len(df_apps)} lignes -> {app_file}")
    
    # Types IBMi uniques
    types_ibmi = df_objets['LST_CTYPE'].unique()
    types_ibmi = [t for t in types_ibmi if t and t.strip()]
    df_types_ibmi = pd.DataFrame({
        'type_name': types_ibmi,
        'description': [f'Type IBMi {t}' for t in types_ibmi]
    })
    
    types_ibmi_file = os.path.join(output_dir, 'types_ibmi.csv')
    df_types_ibmi.to_csv(types_ibmi_file, index=False, encoding='utf-8')
    print(f"Types IBMi sauvegardés: {len(df_types_ibmi)} lignes -> {types_ibmi_file}")
    
    # Types ARCAD uniques
    types_arcad = df_objets['LST_CCPLT'].unique()
    types_arcad = [t for t in types_arcad if t and t.strip()]
    df_types_arcad = pd.DataFrame({
        'type_name': types_arcad,
        'description': [f'Type ARCAD {t}' for t in types_arcad]
    })
    
    types_arcad_file = os.path.join(output_dir, 'types_arcad.csv')
    df_types_arcad.to_csv(types_arcad_file, index=False, encoding='utf-8')
    print(f"Types ARCAD sauvegardés: {len(df_types_arcad)} lignes -> {types_arcad_file}")
    
    # Attributs uniques
    attributs = df_objets['LST_CATR'].unique()
    attributs = [a for a in attributs if a and a.strip()]
    df_attributs = pd.DataFrame({
        'attr_name': attributs,
        'description': [f'Attribut {a}' for a in attributs]
    })
    
    attributs_file = os.path.join(output_dir, 'attributs.csv')
    df_attributs.to_csv(attributs_file, index=False, encoding='utf-8')
    print(f"Attributs sauvegardés: {len(df_attributs)} lignes -> {attributs_file}")

def generate_statistics_report(df_sources, df_objets, df_xref, output_dir):
    """Génère un rapport de statistiques"""
    print("Génération du rapport de statistiques...")
    
    stats = []
    
    # Statistiques générales
    stats.append("=== STATISTIQUES GÉNÉRALES ===")
    stats.append(f"Sources totales: {len(df_sources):,}")
    stats.append(f"Objets totaux: {len(df_objets):,}")
    stats.append(f"Références croisées: {len(df_xref):,}")
    stats.append("")
    
    # Applications
    apps = df_objets['LST_CAPP'].value_counts()
    stats.append("=== RÉPARTITION PAR APPLICATION ===")
    for app, count in apps.head(10).items():
        stats.append(f"{app}: {count:,} objets")
    stats.append("")
    
    # Types d'objets
    types_obj = df_objets['LST_CTYPE'].value_counts()
    stats.append("=== TYPES D'OBJETS ===")
    for type_obj, count in types_obj.items():
        stats.append(f"{type_obj}: {count:,}")
    stats.append("")
    
    # Attributs d'objets
    attributs = df_objets['LST_CATR'].value_counts()
    stats.append("=== ATTRIBUTS D'OBJETS ===")
    for attr, count in attributs.head(15).items():
        stats.append(f"{attr}: {count:,}")
    stats.append("")
    
    # Types de sources
    types_src = df_sources['LST_CTYPE'].value_counts()
    stats.append("=== TYPES DE SOURCES ===")
    for type_src, count in types_src.items():
        stats.append(f"{type_src}: {count:,}")
    stats.append("")
    
    # Fichiers sources
    fichiers_src = df_sources['LST_JSRCF'].value_counts()
    stats.append("=== FICHIERS SOURCES ===")
    for fichier, count in fichiers_src.head(10).items():
        stats.append(f"{fichier}: {count:,}")
    stats.append("")
    
    # Références croisées
    ref_types = df_xref.groupby(['OXR_FROM_TYPE', 'OXR_TO_TYPE']).size()
    stats.append("=== TYPES DE RÉFÉRENCES CROISÉES ===")
    for (from_type, to_type), count in ref_types.items():
        stats.append(f"{from_type} -> {to_type}: {count:,}")
    stats.append("")
    
    # Programmes les plus appelés (si données disponibles)
    if len(df_xref) > 0:
        most_called = df_xref[df_xref['OXR_TO_TYPE'] == '*PGM']['OXR_TO_OBJ'].value_counts()
        stats.append("=== TOP 10 PROGRAMMES LES PLUS APPELÉS ===")
        for pgm, count in most_called.head(10).items():
            stats.append(f"{pgm}: {count:,} appels")
        stats.append("")
        
        # Tables les plus utilisées
        most_used = df_xref[df_xref['OXR_TO_TYPE'] == '*FILE']['OXR_TO_OBJ'].value_counts()
        stats.append("=== TOP 10 TABLES LES PLUS UTILISÉES ===")
        for tbl, count in most_used.head(10).items():
            stats.append(f"{tbl}: {count:,} utilisations")
    
    # Sauvegarde du rapport
    report_file = os.path.join(output_dir, 'statistiques_patrimoine.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(stats))
    
    print(f"Rapport de statistiques sauvegardé: {report_file}")
    
    # Affichage du rapport
    print("\n" + "\n".join(stats[:50]))  # Afficher les 50 premières lignes

def main():
    """Fonction principale"""
    print("=== PRÉPARATION DES FICHIERS CSV POUR NEO4J ===\n")
    
    # Configuration des chemins
    input_dir = "."  # Répertoire contenant les fichiers Excel
    output_dir = "csv_output"
    
    # Création du répertoire de sortie
    Path(output_dir).mkdir(exist_ok=True)
    
    # Fichiers d'entrée
    sources_file = "IBMi_RefArcaddesSources.xlsx"
    objets_file = "IBMi_RefArcaddesObjets.xlsx"
    xref_file = "IBMi_RefArcaddesXREF.xlsx"
    
    # Vérification de l'existence des fichiers
    for file in [sources_file, objets_file, xref_file]:
        if not os.path.exists(file):
            print(f"ERREUR: Fichier manquant: {file}")
            return
    
    try:
        # Traitement des fichiers
        df_sources = prepare_sources_csv(sources_file, output_dir)
        df_objets, df_programmes, df_tables = prepare_objets_csv(objets_file, output_dir)
        df_xref = prepare_xref_csv(xref_file, output_dir)
        
        # Création des métadonnées
        create_metadata_csvs(output_dir, df_objets)
        
        # Génération du rapport
        generate_statistics_report(df_sources, df_objets, df_xref, output_dir)
        
        print(f"\n=== TRAITEMENT TERMINÉ ===")
        print(f"Fichiers CSV générés dans: {output_dir}")
        print("\nFichiers créés:")
        for file in os.listdir(output_dir):
            if file.endswith('.csv'):
                print(f"  - {file}")
        
        print(f"\nVous pouvez maintenant:")
        print(f"1. Copier les fichiers CSV dans le répertoire 'import' de Neo4j")
        print(f"2. Exécuter le script Cypher de chargement")
        print(f"3. Analyser le patrimoine avec les requêtes fournies")
        
    except Exception as e:
        print(f"ERREUR lors du traitement: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

# =================================================================
# INSTRUCTIONS D'UTILISATION
# =================================================================
"""
1. Placez ce script dans le même répertoire que vos fichiers Excel ARCAD
2. Installez pandas si nécessaire: pip install pandas openpyxl
3. Exécutez le script: python prepare_csv.py
4. Copiez les fichiers CSV générés dans le répertoire import de Neo4j
   (généralement: <NEO4J_HOME>/import/)
5. Exécutez le script Cypher de chargement dans Neo4j Browser
6. Utilisez les requêtes d'analyse pour explorer le patrimoine

Structure des fichiers générés:
- IBMi_RefArcaddesSources.csv : Sources filtrées
- IBMi_RefArcaddesObjets.csv : Tous les objets
- IBMi_RefArcaddesObjets_Programmes.csv : Programmes uniquement
- IBMi_RefArcaddesObjets_Tables.csv : Tables uniquement
- IBMi_RefArcaddesXREF.csv : Références croisées filtrées
- applications.csv : Liste des applications
- types_ibmi.csv : Types d'objets IBMi
- types_arcad.csv : Types d'objets ARCAD
- attributs.csv : Attributs d'objets
- statistiques_patrimoine.txt : Rapport d'analyse
"""("Traitement du fichier des sources...")
    
    # Lecture du fichier Excel
    df = pd.read_excel(input_file, sheet_name=0)
    
    # Nettoyage des données
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(clean_string)
    
    # Conversion des dates
    if 'LST_TDATE' in df.columns:
        df['LST_TDATE'] = df['LST_TDATE'].apply(convert_date)
    
    # Filtrage des sources pertinentes (M = membres sources)
    df_filtered = df[df['LST_CELTTY'] == 'M'].copy()
    
    # Types de sources à conserver
    types_programmes = ['RPG', 'RPGLE', 'SQLRPG', 'SQLRPGLE', 'CLP', 'CLLE', 'CBL']
    fichiers_sources_tables = ['QDDSSRC', 'QSQLSRC']
    
    df_filtered = df_filtered[
        (df_filtered['LST_CTYPE'].isin(types_programmes)) |
        (df_filtered['LST_JSRCF'].isin(fichiers_sources_tables)) |
        (df_filtered['LST_CTYPE'] == '*FILE')
    ]
    
    # Sauvegarde
    output_file = os.path.join(output_dir, 'IBMi_RefArcaddesSources.csv')
    df_filtered.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Sources filtrées sauvegardées: {len(df_filtered)} lignes -> {output_file}")
    
    return df_filtered

def prepare_objets_csv(input_file, output_dir):
    """Prépare le fichier des objets"""
    print("Traitement du fichier des objets...")
    
    # Lecture du fichier Excel
    df = pd.read_excel(input_file, sheet_name=0)
    
    # Nettoyage des données
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(clean_string)
    
    # Conversion des dates
    if 'LST_TDATE' in df.columns:
        df['LST_TDATE'] = df['LST_TDATE'].apply(convert_date)
    
    # Filtrage des objets (O = objets)
    df_filtered = df[df['LST_CELTTY'] == 'O'].copy()
    
    # Sauvegarde du fichier complet des objets
    output_file = os.path.join(output_dir, 'IBMi_RefArcaddesObjets.csv')
    df_filtered.to_csv(output_file, index=False, encoding='utf-8')
    print(f"Objets sauvegardés: {len(df_filtered)} lignes -> {output_file}")
    
    # Création des fichiers spécialisés
    
    # Programmes (*PGM)
    df_programmes = df_filtered[df_filtered['LST_CTYPE'] == '*PGM'].copy()
    output_programmes = os.path.join(output_dir, 'IBMi_RefArcaddesObjets_Programmes.csv')
    df_programmes.to_csv(output_programmes, index=False, encoding='utf-8')
    print