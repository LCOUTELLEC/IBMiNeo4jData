# Modèle de Données Neo4j - Patrimoine IBMi/ARCAD

## Types de Nœuds (Labels)

### 1. Application
- **Propriétés :**
  - `name` : Nom de l'application ARCAD (LST_CAPP)
  - `environment` : Environnement (LST_CENV)
  - `version` : Version (LST_CVER)

### 2. Source
- **Propriétés :**
  - `name` : Nom du membre source (LST_JOBJ)
  - `library` : Bibliothèque (LST_JLIB)
  - `sourceFile` : Fichier source (LST_JSRCF)
  - `sourceType` : Type de source (LST_CTYPE)
  - `description` : Description (LST_CTXT)
  - `lastModified` : Date de modification (LST_TDATE)
  - `lineCount` : Nombre de lignes (LST_JZSEL1)

### 3. Programme
- **Propriétés :**
  - `name` : Nom du programme (LST_JOBJ)
  - `library` : Bibliothèque (LST_JLIB)
  - `type` : Type IBMi (LST_CTYPE = *PGM)
  - `attribute` : Attribut (LST_CATR : RPG, RPGLE, CLP, etc.)
  - `arcadType` : Type ARCAD (LST_CCPLT)
  - `description` : Description (LST_CTXT)
  - `lastModified` : Date de modification (LST_TDATE)

### 4. Table
- **Propriétés :**
  - `name` : Nom de la table (LST_JOBJ)
  - `library` : Bibliothèque (LST_JLIB)
  - `type` : Type IBMi (LST_CTYPE = *FILE)
  - `attribute` : Attribut (LST_CATR : PF, TABLE)
  - `arcadType` : Type ARCAD (LST_CCPLT)
  - `description` : Description (LST_CTXT)
  - `lastModified` : Date de modification (LST_TDATE)

### 5. TypeObjIBMi (Métadonnées)
- **Propriétés :**
  - `name` : Type IBMi (*PGM, *FILE, *SRVPGM, etc.)
  - `description` : Description du type

### 6. TypeObjARCAD (Métadonnées)
- **Propriétés :**
  - `name` : Type ARCAD (*PF, *PFTAB, etc.)
  - `description` : Description du type ARCAD

### 7. Attribut (Métadonnées)
- **Propriétés :**
  - `name` : Nom de l'attribut (RPG, PF, CLP, etc.)
  - `description` : Description de l'attribut

## Types de Relations

### 1. BELONGS_TO
- **Source :** Programme/Table/Source → Application
- **Propriétés :** Aucune

### 2. GENERATES
- **Source :** Source → Programme/Table
- **Propriétés :**
  - `compilationDate` : Date de compilation
  - `sourceFile` : Fichier source d'origine (LST_JSRCF)

### 3. CALLS
- **Source :** Programme → Programme
- **Propriétés :**
  - `callType` : Type d'appel (dérivé des données XREF)

### 4. USES
- **Source :** Programme → Table
- **Propriétés :**
  - `usageType` : Type d'utilisation (READ, WRITE, UPDATE)
  - `logicalFile` : Fichier logique utilisé (OXR_TO_LF_OBJ)

### 5. TYPED_AS_IBM
- **Source :** Programme/Table → TypeObjIBMi
- **Propriétés :** Aucune

### 6. TYPED_AS_ARCAD
- **Source :** Programme/Table → TypeObjARCAD  
- **Propriétés :** Aucune

### 7. HAS_ATTRIBUTE
- **Source :** Programme/Table → Attribut
- **Propriétés :** Aucune

## Règles de Filtrage

### Exclusions pour les Tables
- Exclure les DSPF (écrans)
- Exclure les PRTF (rapports)
- Conserver uniquement : PF, TABLE, LF

### Inclusion des Sources
- Sources de programmes : RPG, RPGLE, SQLRPG, SQLRPGLE, CLP, CLLE, CBL
- Sources de tables : DDS (QDDSSRC), SQL (QSQLSRC)

## Index Recommandés

```cypher
// Index sur les propriétés de recherche principales
CREATE INDEX FOR (n:Programme) ON (n.name, n.library);
CREATE INDEX FOR (n:Table) ON (n.name, n.library);
CREATE INDEX FOR (n:Source) ON (n.name, n.library);
CREATE INDEX FOR (n:Application) ON (n.name);

// Index pour les recherches par type
CREATE INDEX FOR (n:Programme) ON (n.attribute);
CREATE INDEX FOR (n:Table) ON (n.attribute);
```

## Contraintes d'Unicité

```cypher
// Contraintes d'unicité pour éviter les doublons
CREATE CONSTRAINT FOR (n:Programme) REQUIRE (n.name, n.library) IS UNIQUE;
CREATE CONSTRAINT FOR (n:Table) REQUIRE (n.name, n.library) IS UNIQUE;
CREATE CONSTRAINT FOR (n:Source) REQUIRE (n.name, n.library, n.sourceFile) IS UNIQUE;
CREATE CONSTRAINT FOR (n:Application) REQUIRE (n.name) IS UNIQUE;
```