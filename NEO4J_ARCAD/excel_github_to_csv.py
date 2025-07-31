#!/usr/bin/env python3
"""
Script Python - Lecture directe des Excel ARCAD depuis GitHub
Génération des CSV optimisés pour Neo4j
Auteur: Assistant IA
Date: 2025
"""

import pandas as pd
import requests
import io
import os
from pathlib import Path
from datetime import datetime

# Configuration GitHub
GITHUB_BASE_URL = "https://raw.githubusercontent.com/LCOUTELLEC/IBMiNeo4jData/main/NEO4J_ARCAD/"
OUTPUT_DIR = "csv_neo4j"

# Fichiers Excel ARCAD sur GitHub
EXCEL_FILES = {
    "sources": "IBMi_RefArcaddesSources.xlsx",
    "objets": "IBMi_RefArcaddesObjets.xlsx", 
    "xref": "IBMi_RefArcaddesXREF.xlsx"
}

def download_excel_from_github(filename):
    """Télécharge un fichier Excel depuis GitHub"""
    url = GITHUB_BASE_URL + filename
    print(f"Téléchargement de {filename} depuis GitHub...")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        # Lire le contenu Excel directement depuis la mémoire
        excel_data = pd.ExcelFile(io.BytesIO(response.content))
        print(f"✓ {filename} téléchargé avec succès ({len(response.content)} bytes)")
        return excel_data
        
    except Exception as e:
        print(f"✗ Erreur lors du téléchargement de {filename}: {str(e)}")
        return None

def clean_string(value):
    """Nettoie les chaînes de caractères"""
    if pd.isna(value):
        return ""
    return str(value).strip()

def convert_date_arcad(date_value):
    """Convertit les dates ARCAD (AAAAMMJJ ou timestamp) vers format ISO"""
    if pd.isna(date_value) or date_value == 0:
        return ""
    
    try:
        # Si c'est déjà un timestamp pandas
        if hasattr(date_value, 'strftime'):
            return date_value.strftime('%Y-%m-%d')
            
        # Si c'est un nombre (format ARCAD AAAAMMJJ)
        date_str = str(int(date_value))
        if len(date_str) == 8:
            return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
        elif len(date_str) == 6:  # AAMMJJ
            return f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}"
            
    except:
        pass
        
    return ""

def process_sources_excel(excel_data, output_dir):
    """Traite le fichier Excel des sources"""
    print("Traitement du fichier des sources...")
    
    try:
        # Lire la première feuille
        df = pd.read_excel(excel_data, sheet_name=0)
        print(f"Sources lues: {len(df)} lignes")
        
        # Afficher les colonnes pour diagnostic
        print(f"Colonnes trouvées: {list(df.columns)}")
        
        # Nettoyage des données
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(clean_string)
        
        # Conversion des dates
        if 'LST_TDATE' in df.columns:
            df['LST_TDATE'] = df['LST_TDATE'].apply(convert_date_arcad)
        
        # Filtrage des sources pertinentes
        if 'LST_CELTTY' in df.columns:
            df_filtered = df[df['LST_CELTTY'] == 'M'].copy()
        else:
            print("⚠️ Colonne LST_CELTTY non trouvée - conservation de toutes les lignes")
            df_filtered = df.copy()
        
        # Types de sources à conserver
        types_programmes = ['RPG', 'RPGLE', 'SQLRPG', 'SQLRPGLE', 'CLP', 'CLLE', 'CBL']
        fichiers_sources_tables = ['QDDSSRC', 'QSQLSRC']
        
        if 'LST_CTYPE' in df.columns:
            df_filtered = df_filtered[
                (df_filtered['LST_CTYPE'].isin(types_programmes)) |
                (df_filtered['LST_JSRCF'].isin(fichiers_sources_tables) if 'LST_JSRCF' in df.columns else False) |
                (df_filtered['LST_CTYPE'] == '*FILE')
            ]
        
        print(f"Sources filtrées: {len(df_filtered)} lignes")
        
        # Sauvegarde
        output_file = os.path.join(output_dir, 'IBMi_RefArcaddesSources.csv')
        df_filtered.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ Sources sauvegardées: {output_file}")
        
        return df_filtered
        
    except Exception as e:
        print(f"✗ Erreur lors du traitement des sources: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def process_objets_excel(excel_data, output_dir):
    """Traite le fichier Excel des objets"""
    print("Traitement du fichier des objets...")
    
    try:
        # Lire la première feuille
        df = pd.read_excel(excel_data, sheet_name=0)
        print(f"Objets lus: {len(df)} lignes")
        
        # Afficher les colonnes pour diagnostic
        print(f"Colonnes trouvées: {list(df.columns)}")
        
        # Nettoyage des données
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(clean_string)
        
        # Conversion des dates
        if 'LST_TDATE' in df.columns:
            df['LST_TDATE'] = df['LST_TDATE'].apply(convert_date_arcad)
        
        # Filtrage des objets (O = objets)
        if 'LST_CELTTY' in df.columns:
            df_filtered = df[df['LST_CELTTY'] == 'O'].copy()
        else:
            print("⚠️ Colonne LST_CELTTY non trouvée - conservation de toutes les lignes")
            df_filtered = df.copy()
            
        print(f"Objets filtrés: {len(df_filtered)} lignes")
        
        # Sauvegarde du fichier complet
        output_file = os.path.join(output_dir, 'IBMi_RefArcaddesObjets.csv')
        df_filtered.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ Objets complets sauvegardés: {output_file}")
        
        # Création des fichiers spécialisés
        
        # Programmes (*PGM)
        if 'LST_CTYPE' in df.columns:
            df_programmes = df_filtered[df_filtered['LST_CTYPE'] == '*PGM'].copy()
            output_programmes = os.path.join(output_dir, 'IBMi_RefArcaddesObjets_Programmes.csv')
            df_programmes.to_csv(output_programmes, index=False, encoding='utf-8')
            print(f"✓ Programmes sauvegardés: {len(df_programmes)} lignes -> {output_programmes}")
        else:
            df_programmes = pd.DataFrame()
            print("⚠️ Impossible de filtrer les programmes - colonne LST_CTYPE non trouvée")
        
        # Tables (*FILE avec PF ou TABLE)
        if 'LST_CTYPE' in df.columns and 'LST_CATR' in df.columns:
            df_tables = df_filtered[
                (df_filtered['LST_CTYPE'] == '*FILE') & 
                (df_filtered['LST_CATR'].isin(['PF', 'TABLE']))
            ].copy()
            output_tables = os.path.join(output_dir, 'IBMi_RefArcaddesObjets_Tables.csv')
            df_tables.to_csv(output_tables, index=False, encoding='utf-8')
            print(f"✓ Tables sauvegardées: {len(df_tables)} lignes -> {output_tables}")
        else:
            df_tables = pd.DataFrame()
            print("⚠️ Impossible de filtrer les tables - colonnes LST_CTYPE ou LST_CATR non trouvées")
        
        return df_filtered, df_programmes, df_tables
        
    except Exception as e:
        print(f"✗ Erreur lors du traitement des objets: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None, None

def process_xref_excel(excel_data, output_dir):
    """Traite le fichier Excel des références croisées"""
    print("Traitement du fichier des références croisées...")
    
    try:
        # Lire la première feuille
        df = pd.read_excel(excel_data, sheet_name=0)
        print(f"XREF lues: {len(df)} lignes")
        
        # Afficher les colonnes pour diagnostic
        print(f"Colonnes trouvées: {list(df.columns)}")
        
        # Nettoyage des données
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].apply(clean_string)
        
        # Filtrage des références pertinentes
        if all(col in df.columns for col in ['OXR_FROM_TYPE', 'OXR_TO_TYPE']):
            df_filtered = df[
                ((df['OXR_FROM_TYPE'] == '*PGM') & (df['OXR_TO_TYPE'] == '*PGM')) |
                ((df['OXR_FROM_TYPE'] == '*PGM') & (df['OXR_TO_TYPE'] == '*FILE'))
            ].copy()
        else:
            print("⚠️ Colonnes OXR_FROM_TYPE ou OXR_TO_TYPE non trouvées - conservation de toutes les lignes")
            df_filtered = df.copy()
        
        print(f"XREF filtrées: {len(df_filtered)} lignes")
        
        # Sauvegarde
        output_file = os.path.join(output_dir, 'IBMi_RefArcaddesXREF.csv')
        df_filtered.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✓ XREF sauvegardées: {output_file}")
        
        return df_filtered
        
    except Exception as e:
        print(f"✗ Erreur lors du traitement des XREF: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def create_metadata_csvs(output_dir, df_objets):
    """Crée les fichiers CSV de métadonnées"""
    print("Création des fichiers de métadonnées...")
    
    try:
        # Applications uniques
        if 'LST_CAPP' in df_objets.columns:
            applications = df_objets['LST_CAPP'].unique()
            applications = [app for app in applications if app and app.strip()]
            df_apps = pd.DataFrame({
                'name': applications,
                'description': [f'Application {app}' for app in applications]
            })
            
            app_file = os.path.join(output_dir, 'applications.csv')
            df_apps.to_csv(app_file, index=False, encoding='utf-8')
            print(f"✓ Applications: {len(df_apps)} -> {app_file}")
        else:
            print("⚠️ Colonne LST_CAPP non trouvée - pas d'applications générées")
        
        # Types IBMi uniques
        if 'LST_CTYPE' in df_objets.columns:
            types_ibmi = df_objets['LST_CTYPE'].unique()
            types_ibmi = [t for t in types_ibmi if t and t.strip()]
            df_types_ibmi = pd.DataFrame({
                'type_name': types_ibmi,
                'description': [f'Type IBMi {t}' for t in types_ibmi]
            })
            
            types_ibmi_file = os.path.join(output_dir, 'types_ibmi.csv')
            df_types_ibmi.to_csv(types_ibmi_file, index=False, encoding='utf-8')
            print(f"✓ Types IBMi: {len(df_types_ibmi)} -> {types_ibmi_file}")
        
        # Types ARCAD uniques
        if 'LST_CCPLT' in df_objets.columns:
            types_arcad = df_objets['LST_CCPLT'].unique()
            types_arcad = [t for t in types_arcad if t and t.strip()]
            df_types_arcad = pd.DataFrame({
                'type_name': types_arcad,
                'description': [f'Type ARCAD {t}' for t in types_arcad]
            })
            
            types_arcad_file = os.path.join(output_dir, 'types_arcad.csv')
            df_types_arcad.to_csv(types_arcad_file, index=False, encoding='utf-8')
            print(f"✓ Types ARCAD: {len(df_types_arcad)} -> {types_arcad_file}")
        
        # Attributs uniques
        if 'LST_CATR' in df_objets.columns:
            attributs = df_objets['LST_CATR'].unique()
            attributs = [a for a in attributs if a and a.strip()]
            df_attributs = pd.DataFrame({
                'attr_name': attributs,
                'description': [f'Attribut {a}' for a in attributs]
            })
            
            attributs_file = os.path.join(output_dir, 'attributs.csv')
            df_attributs.to_csv(attributs_file, index=False, encoding='utf-8')
            print(f"✓ Attributs: {len(df_attributs)} -> {attributs_file}")
        
    except Exception as e:
        print(f"✗ Erreur lors de la création des métadonnées: {str(e)}")

def generate_statistics_report(df_sources, df_objets, df_xref, output_dir):
    """Génère un rapport de statistiques"""
    print("Génération du rapport de statistiques...")
    
    try:
        stats = []
        
        # En-tête
        stats.append(f"RAPPORT DE STATISTIQUES - PATRIMOINE IBMi ARCAD")
        stats.append(f"Généré le: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        stats.append("=" * 60)
        stats.append("")
        
        # Statistiques générales
        stats.append("=== STATISTIQUES GÉNÉRALES ===")
        stats.append(f"Sources totales: {len(df_sources) if df_sources is not None else 0:,}")
        stats.append(f"Objets totaux: {len(df_objets) if df_objets is not None else 0:,}")
        stats.append(f"Références croisées: {len(df_xref) if df_xref is not None else 0:,}")
        stats.append("")
        
        if df_objets is not None and len(df_objets) > 0:
            # Applications
            if 'LST_CAPP' in df_objets.columns:
                apps = df_objets['LST_CAPP'].value_counts()
                stats.append("=== RÉPARTITION PAR APPLICATION ===")
                for app, count in apps.head(10).items():
                    stats.append(f"{app}: {count:,} objets")
                stats.append("")
            
            # Types d'objets
            if 'LST_CTYPE' in df_objets.columns:
                types_obj = df_objets['LST_CTYPE'].value_counts()
                stats.append("=== TYPES D'OBJETS ===")
                for type_obj, count in types_obj.items():
                    stats.append(f"{type_obj}: {count:,}")
                stats.append("")
            
            # Attributs d'objets
            if 'LST_CATR' in df_objets.columns:
                attributs = df_objets['LST_CATR'].value_counts()
                stats.append("=== ATTRIBUTS D'OBJETS ===")
                for attr, count in attributs.head(15).items():
                    stats.append(f"{attr}: {count:,}")
                stats.append("")
        
        # Types de sources
        if df_sources is not None and len(df_sources) > 0 and 'LST_CTYPE' in df_sources.columns:
            types_src = df_sources['LST_CTYPE'].value_counts()
            stats.append("=== TYPES DE SOURCES ===")
            for type_src, count in types_src.items():
                stats.append(f"{type_src}: {count:,}")
            stats.append("")
        
        # Références croisées
        if df_xref is not None and len(df_xref) > 0:
            if all(col in df_xref.columns for col in ['OXR_FROM_TYPE', 'OXR_TO_TYPE']):
                ref_types = df_xref.groupby(['OXR_FROM_TYPE', 'OXR_TO_TYPE']).size()
                stats.append("=== TYPES DE RÉFÉRENCES CROISÉES ===")
                for (from_type, to_type), count in ref_types.items():
                    stats.append(f"{from_type} -> {to_type}: {count:,}")
                stats.append("")
        
        # Sauvegarde du rapport
        report_file = os.path.join(output_dir, 'rapport_statistiques.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(stats))
        
        print(f"✓ Rapport sauvegardé: {report_file}")
        
        # Affichage du résumé
        print("\n=== APERÇU DU RAPPORT ===")
        print("\n".join(stats[:30]))
        
    except Exception as e:
        print(f"✗ Erreur lors de la génération du rapport: {str(e)}")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("TRAITEMENT DES FICHIERS EXCEL ARCAD DEPUIS GITHUB")
    print("Génération des CSV pour Neo4j")
    print("=" * 60)
    print()
    
    # Création du répertoire de sortie
    Path(OUTPUT_DIR).mkdir(exist_ok=True)
    print(f"Répertoire de sortie: {os.path.abspath(OUTPUT_DIR)}")
    print()
    
    try:
        # Phase 1: Téléchargement et traitement des sources
        sources_excel = download_excel_from_github(EXCEL_FILES["sources"])
        if sources_excel is None:
            print("⚠️ Fichier des sources non accessible - continuons avec les autres fichiers")
            df_sources = None
        else:
            df_sources = process_sources_excel(sources_excel, OUTPUT_DIR)
        print()
        
        # Phase 2: Téléchargement et traitement des objets
        objets_excel = download_excel_from_github(EXCEL_FILES["objets"])
        if objets_excel is None:
            print("✗ Impossible de continuer sans le fichier des objets")
            return 1
            
        df_objets, df_programmes, df_tables = process_objets_excel(objets_excel, OUTPUT_DIR)
        if df_objets is None:
            print("✗ Erreur lors du traitement des objets")
            return 1
        print()
        
        # Phase 3: Téléchargement et traitement des XREF
        xref_excel = download_excel_from_github(EXCEL_FILES["xref"])
        if xref_excel is None:
            print("⚠️ Fichier XREF non accessible - relations limitées")
            df_xref = None
        else:
            df_xref = process_xref_excel(xref_excel, OUTPUT_DIR)
        print()
        
        # Phase 4: Création des métadonnées
        if df_objets is not None:
            create_metadata_csvs(OUTPUT_DIR, df_objets)
        print()
        
        # Phase 5: Génération du rapport
        if df_sources is not None or df_objets is not None or df_xref is not None:
            generate_statistics_report(df_sources, df_objets, df_xref, OUTPUT_DIR)
        print()
        
        # Résumé final
        print("=" * 60)
        print("TRAITEMENT TERMINÉ")
        print("=" * 60)
        print(f"Répertoire de sortie: {os.path.abspath(OUTPUT_DIR)}")
        print()
        print("Fichiers CSV générés:")
        
        if os.path.exists(OUTPUT_DIR):
            csv_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.csv')]
            for file in sorted(csv_files):
                file_path = os.path.join(OUTPUT_DIR, file)
                file_size = os.path.getsize(file_path)
                print(f"  ✓ {file} ({file_size:,} bytes)")
            
            print()
            print("PROCHAINES ÉTAPES:")
            print("1. Vérifiez les fichiers CSV générés")
            print("2. Uploadez-les dans votre repository GitHub ou serveur Neo4j")
            print("3. Exécutez le script Cypher de chargement")
            print("4. Utilisez les requêtes d'analyse pour explorer le patrimoine")
        else:
            print("Aucun fichier généré")
        
        return 0
        
    except Exception as e:
        print(f"✗ ERREUR CRITIQUE: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    exit_code = main()
    sys.exit(exit_code)
