# Rapport de synthèse - Intégration du patrimoine IBMi dans Neo4j

## Introduction

Ce document présente la démarche complète d'intégration des données du patrimoine IBMi dans Neo4j, permettant une visualisation et une analyse graphique des composants (programmes RPG, tables) et leurs relations. Le modèle de graphe mis en place permet d'analyser les dépendances, mesurer l'impact de modifications potentielles et identifier les composants critiques du système.

## 1. Modèle de données

Le modèle de graphe implémenté comprend :

**Nœuds :**
- `Program` : Représente les programmes RPG
- `Table` : Représente les tables/fichiers
- `Library` : Représente les bibliothèques IBMi

**Relations :**
- `CALLS` : Relation entre programmes (Programme A appelle Programme B)
- `USES` : Relation entre programmes et tables (Programme utilise Table)
- `BELONGS_TO` : Relation entre programmes/tables et bibliothèques

## 2. Données sources

Les données ont été extraites via des requêtes SQL depuis l'IBMi et exportées dans les fichiers CSV suivants :

1. `IBMi_PROGRAMMES.csv` : Liste des programmes RPG
2. `IBMi_TABLES.csv` : Liste des tables
3. `IBMi_XREF_PGM.csv` : Références croisées programme à programme
4. `IBMi_XREF_TABLES.csv` : Références croisées programme à tables

## 3. Scripts de chargement

### 3.1 Préparation de la base Neo4j

```cypher
// Nettoyer la base de données et supprimer les contraintes existantes
MATCH (n) DETACH DELETE n;
DROP CONSTRAINT program_id IF EXISTS;
DROP CONSTRAINT table_id IF EXISTS; 
DROP CONSTRAINT library_name IF EXISTS;

// Créer les contraintes
CREATE CONSTRAINT program_id IF NOT EXISTS FOR (p:Program) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT table_id IF NOT EXISTS FOR (t:Table) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT library_name IF NOT EXISTS FOR (l:Library) REQUIRE l.name IS UNIQUE;
```

### 3.2 Importation des bibliothèques

```cypher
// Création des bibliothèques à partir des données des programmes
LOAD CSV WITH HEADERS FROM 'https://github.com/LCOUTELLEC/IBMiNeo4jData/raw/refs/heads/main/IBMi_PROGRAMMES.csv' AS row FIELDTERMINATOR '#'
WITH DISTINCT row.OBJLIB AS libName
WHERE libName IS NOT NULL AND trim(libName) <> ''
MERGE (l:Library {name: libName});

// Création des bibliothèques à partir des données des tables
LOAD CSV WITH HEADERS FROM 'https://github.com/LCOUTELLEC/IBMiNeo4jData/raw/refs/heads/main/IBMi_TABLES.csv' AS row FIELDTERMINATOR '#'
WITH DISTINCT row.SYSTEM_TABLE_SCHEMA AS libName
WHERE libName IS NOT NULL AND trim(libName) <> ''
MERGE (l:Library {name: libName});
```

### 3.3 Importation des programmes RPG

```cypher
// Importation des programmes RPG avec gestion des NULL
LOAD CSV WITH HEADERS FROM 'https://github.com/LCOUTELLEC/IBMiNeo4jData/raw/refs/heads/main/IBMi_PROGRAMMES.csv' AS row FIELDTERMINATOR '#'
WITH row 
WHERE row.OBJNAME IS NOT NULL AND trim(row.OBJNAME) <> '' 
AND row.OBJLIB IS NOT NULL AND trim(row.OBJLIB) <> ''
MATCH (lib:Library {name: row.OBJLIB})
MERGE (p:Program {library: row.OBJLIB, name: row.OBJNAME})
ON CREATE SET 
    p.id = row.OBJLIB + '_' + row.OBJNAME,
    p.type = row.OBJTYPE,
    p.owner = row.OBJOWNER,
    p.description = row.OBJTEXT,
    p.size = CASE WHEN row.OBJSIZE IS NULL THEN null ELSE toInteger(row.OBJSIZE) END,
    p.sourceMember = row.SOURCE_MEMBER,
    p.changeDate = CASE WHEN row.CHANGE_DATE IS NULL OR trim(row.CHANGE_DATE) = '' THEN null ELSE date(row.CHANGE_DATE) END,
    p.sourceDate = CASE WHEN row.SOURCE_DATE IS NULL OR trim(row.SOURCE_DATE) = '' THEN null ELSE date(row.SOURCE_DATE) END,
    p.lastUsedDate = CASE WHEN row.LAST_USED_DATE IS NULL OR trim(row.LAST_USED_DATE) = '' THEN null ELSE date(row.LAST_USED_DATE) END,
    p.daysUsedCount = CASE WHEN row.DAYS_USED_COUNT IS NULL THEN null ELSE toInteger(row.DAYS_USED_COUNT) END,
    p.language = 'RPG'
MERGE (p)-[:BELONGS_TO]->(lib);
```

### 3.4 Importation des tables

```cypher
// Importation des tables avec gestion des NULL
LOAD CSV WITH HEADERS FROM 'https://github.com/LCOUTELLEC/IBMiNeo4jData/raw/refs/heads/main/IBMi_TABLES.csv' AS row FIELDTERMINATOR '#'
WITH row
WHERE row.SYSTEM_TABLE_NAME IS NOT NULL AND trim(row.SYSTEM_TABLE_NAME) <> '' 
AND row.SYSTEM_TABLE_SCHEMA IS NOT NULL AND trim(row.SYSTEM_TABLE_SCHEMA) <> ''
MATCH (lib:Library {name: row.SYSTEM_TABLE_SCHEMA})
MERGE (t:Table {library: row.SYSTEM_TABLE_SCHEMA, name: row.SYSTEM_TABLE_NAME})
ON CREATE SET 
    t.id = row.SYSTEM_TABLE_SCHEMA + '_' + row.SYSTEM_TABLE_NAME,
    t.tableType = row.TABLE_TYPE,
    t.columnCount = CASE WHEN row.COLUMN_COUNT IS NULL THEN null ELSE toInteger(row.COLUMN_COUNT) END,
    t.logicalName = row.TABLE_NAME,
    t.fileType = row.FILE_TYPE,
    t.description = row.TABLE_TEXT,
    t.rowLength = CASE WHEN row.ROW_LENGTH IS NULL THEN null ELSE toInteger(row.ROW_LENGTH) END,
    t.lastAlteredDate = CASE WHEN row.LAST_ALTERED_DATE IS NULL OR trim(row.LAST_ALTERED_DATE) = '' THEN null ELSE date(row.LAST_ALTERED_DATE) END,
    t.rowCount = CASE WHEN row.NUMBER_ROWS IS NULL THEN null ELSE toInteger(row.NUMBER_ROWS) END,
    t.dataSize = CASE WHEN row.DATA_SIZE IS NULL THEN null ELSE toInteger(row.DATA_SIZE) END,
    t.lastChangeDate = CASE WHEN row.LAST_CHANGE_DATE IS NULL OR trim(row.LAST_CHANGE_DATE) = '' THEN null ELSE date(row.LAST_CHANGE_DATE) END,
    t.lastUsedDate = CASE WHEN row.LAST_USED_DATE IS NULL OR trim(row.LAST_USED_DATE) = '' THEN null ELSE date(row.LAST_USED_DATE) END,
    t.daysUsedCount = CASE WHEN row.DAYS_USED_COUNT IS NULL THEN null ELSE toInteger(row.DAYS_USED_COUNT) END,
    t.distinctIndexCount = CASE WHEN row.NUMBER_DISTINCT_INDEXES IS NULL THEN null ELSE toInteger(row.NUMBER_DISTINCT_INDEXES) END,
    t.physicalReads = CASE WHEN row.PHYSICAL_READS IS NULL THEN null ELSE toInteger(row.PHYSICAL_READS) END,
    t.logicalReads = CASE WHEN row.LOGICAL_READS IS NULL THEN null ELSE toInteger(row.LOGICAL_READS) END,
    t.insertOperations = CASE WHEN row.INSERT_OPERATIONS IS NULL THEN null ELSE toInteger(row.INSERT_OPERATIONS) END,
    t.updateOperations = CASE WHEN row.UPDATE_OPERATIONS IS NULL THEN null ELSE toInteger(row.UPDATE_OPERATIONS) END,
    t.openOperations = CASE WHEN row.OPEN_OPERATIONS IS NULL THEN null ELSE toInteger(row.OPEN_OPERATIONS) END,
    t.closeOperations = CASE WHEN row.CLOSE_OPERATIONS IS NULL THEN null ELSE toInteger(row.CLOSE_OPERATIONS) END
MERGE (t)-[:BELONGS_TO]->(lib);
```

### 3.5 Importation des références croisées programme à programme

```cypher
// Importation des références croisées programme à programme
LOAD CSV FROM 'file:///IBMi_XREF_PGM.csv' AS row FIELDTERMINATOR '#'
with row
WHERE size(row) >= 8
WITH 
    row[0] AS sourceLib,
    row[1] AS sourcePgm,
    CASE WHEN row[2] IS NULL OR trim(row[2]) = '' THEN 0 ELSE toInteger(row[2]) END AS nbRel,
    row[3] AS targetLib,
    row[4] AS targetName,
    row[5] AS targetObjType,
    row[6] AS targetType,
    row[7] AS typePgm
WHERE targetType = '*PGM' AND nbRel > 0
AND sourceLib IS NOT NULL AND trim(sourceLib) <> ''
AND sourcePgm IS NOT NULL AND trim(sourcePgm) <> ''
AND targetLib IS NOT NULL AND trim(targetLib) <> ''
AND targetName IS NOT NULL AND trim(targetName) <> ''
OPTIONAL MATCH (source:Program {library: sourceLib, name: sourcePgm})
OPTIONAL MATCH (target:Program {library: targetLib, name: targetName})
WITH source, target, nbRel
WHERE source IS NOT NULL AND target IS NOT NULL
MERGE (source)-[r:CALLS {count: nbRel}]->(target);
```

### 3.6 Importation des références croisées programme à tables

```cypher
// Importation des références croisées programme à tables depuis IBMi_XREF_TABLES.csv
LOAD CSV WITH HEADERS FROM 'https://github.com/LCOUTELLEC/IBMiNeo4jData/raw/refs/heads/main/IBMi_XREF_TABLES.csv' AS row
WITH row['SOURCELIB#"SOURCEPGMNAME"#"NBRELATION"#"CIBLELIB"#"CIBLENAME"#"CIBLEOBJECTTYPE"#"CIBLETYPE"#"TYPEPGM"#"PFCIBLELIB"#"PFCIBLENOM"'] AS fullLine
WHERE fullLine IS NOT NULL
WITH split(replace(replace(fullLine, '"', ''), ' ', ''), '#') AS parts
WHERE size(parts) >= 10
WITH 
    parts[0] AS sourceLib,
    parts[1] AS sourcePgm,
    CASE WHEN parts[2] IS NULL OR trim(parts[2]) = '' THEN 0 ELSE toInteger(parts[2]) END AS nbRel,
    parts[3] AS targetLib,
    parts[4] AS targetName,
    parts[5] AS targetObjType,
    parts[6] AS targetType,
    parts[7] AS typePgm,
    parts[8] AS pfTargetLib,
    parts[9] AS pfTargetName
WHERE targetType = '*FILE' AND nbRel > 0
AND sourceLib IS NOT NULL AND trim(sourceLib) <> ''
AND sourcePgm IS NOT NULL AND trim(sourcePgm) <> ''
OPTIONAL MATCH (source:Program {library: sourceLib, name: sourcePgm})
WHERE source IS NOT NULL
WITH source, targetLib, targetName, pfTargetLib, pfTargetName, nbRel,
     CASE 
         WHEN pfTargetLib IS NOT NULL AND trim(pfTargetLib) <> '' THEN pfTargetLib 
         ELSE targetLib 
     END as finalLib,
     CASE 
         WHEN pfTargetName IS NOT NULL AND trim(pfTargetName) <> '' THEN pfTargetName 
         ELSE targetName 
     END as finalName
WHERE finalLib IS NOT NULL AND trim(finalLib) <> ''
AND finalName IS NOT NULL AND trim(finalName) <> ''
OPTIONAL MATCH (target:Table {library: finalLib, name: finalName})
WHERE target IS NOT NULL
WITH source, target, nbRel
WHERE source IS NOT NULL AND target IS NOT NULL
MERGE (source)-[r:USES {count: nbRel}]->(target);
```

## 4. Scripts de contrôle et d'analyse

### 4.1 Vérification des données importées

```cypher
// Vérifier le nombre de nœuds par type
MATCH (n)
RETURN labels(n) AS Type, count(n) AS Nombre
ORDER BY Nombre DESC;

// Vérifier le nombre de relations par type
MATCH ()-[r]->()
RETURN type(r) AS Type, count(r) AS Nombre
ORDER BY Nombre DESC;

// Vérifier les programmes importés
MATCH (p:Program)
RETURN count(p) AS NombreProgrammes;

// Vérifier les tables importées
MATCH (t:Table)
RETURN count(t) AS NombreTables;

// Vérifier les bibliothèques importées
MATCH (l:Library)
RETURN count(l) AS NombreBibliothèques;

// Vérifier les relations CALLS
MATCH ()-[r:CALLS]->()
RETURN count(r) AS NombreRelationsCALLS;

// Vérifier les relations USES
MATCH ()-[r:USES]->()
RETURN count(r) AS NombreRelationsUSES;
```

### 4.2 Analyse des programmes

```cypher
// Programmes les plus utilisés (appelés par d'autres programmes)
MATCH (p:Program)<-[r:CALLS]-()
RETURN p.name AS ProgramName, p.library AS Library, count(r) AS CallCount
ORDER BY CallCount DESC
LIMIT 20;

// Programmes qui utilisent le plus de tables/programmes (complexité)
MATCH (p:Program)-[r]->(target)
RETURN p.name AS ProgramName, p.library AS Library, 
       count(DISTINCT CASE WHEN type(r)='CALLS' THEN target END) AS ProgramCallCount, 
       count(DISTINCT CASE WHEN type(r)='USES' THEN target END) AS TableUsageCount,
       count(r) AS TotalDependencies
ORDER BY TotalDependencies DESC
LIMIT 20;

// Programmes isolés (non appelés par d'autres programmes)
MATCH (p:Program)
WHERE NOT (p)<-[:CALLS]-()
RETURN p.name AS ProgramName, p.library AS Library
LIMIT 50;

// Programmes les plus récemment modifiés
MATCH (p:Program)
WHERE p.changeDate IS NOT NULL
RETURN p.library AS Bibliothèque, p.name AS Nom, p.description AS Description,
       p.changeDate AS DateModification
ORDER BY p.changeDate DESC
LIMIT 20;

// Programmes les plus utilisés (basé sur daysUsedCount)
MATCH (p:Program)
WHERE p.daysUsedCount IS NOT NULL
RETURN p.library AS Bibliothèque, p.name AS Nom, p.description AS Description,
       p.daysUsedCount AS NombreJoursUtilisé
ORDER BY p.daysUsedCount DESC
LIMIT 20;
```

### 4.3 Analyse des tables

```cypher
// Tables les plus utilisées par les programmes
MATCH (t:Table)<-[r:USES]-()
RETURN t.name AS TableName, t.library AS Library, count(r) AS UsageCount
ORDER BY UsageCount DESC
LIMIT 20;

// Tables non utilisées
MATCH (t:Table)
WHERE NOT (t)<-[:USES]-()
RETURN t.name AS TableName, t.library AS Library, t.description AS Description
LIMIT 50;

// Tables avec le plus de données
MATCH (t:Table)
WHERE t.rowCount IS NOT NULL AND t.dataSize IS NOT NULL
RETURN t.library AS Library, t.name AS TableName, 
       t.rowCount AS RowCount, t.dataSize AS DataSize
ORDER BY t.dataSize DESC
LIMIT 20;

// Tables les plus fréquemment modifiées
MATCH (t:Table)
WHERE t.updateOperations IS NOT NULL AND t.insertOperations IS NOT NULL
RETURN t.library AS Library, t.name AS TableName,
       t.updateOperations AS Updates, t.insertOperations AS Inserts,
       t.updateOperations + t.insertOperations AS TotalModifications
ORDER BY TotalModifications DESC
LIMIT 20;
```

### 4.4 Analyses d'impact et de dépendances

```cypher
// Analyse d'impact pour une table spécifique
// Remplacez 'TABLE_NAME' par le nom de votre table
MATCH (t:Table {name: 'TABLE_NAME'})<-[:USES]-(p:Program)
OPTIONAL MATCH (p)<-[:CALLS*1..2]-(caller:Program)
WITH t, p, collect(DISTINCT caller.name) AS callers
RETURN t.library AS TableLibrary, t.name AS TableName,
       p.library AS ProgramLibrary, p.name AS ProgramName,
       callers AS ProgramsIndirectlyAffected,
       size(callers) AS IndirectImpactCount
ORDER BY IndirectImpactCount DESC;

// Analyse d'impact pour un programme spécifique
// Remplacez 'PROGRAM_NAME' par le nom de votre programme
MATCH (p:Program {name: 'PROGRAM_NAME'})
OPTIONAL MATCH (p)-[:CALLS*1..2]->(called:Program)
RETURN p.library AS Library, p.name AS ProgramName,
       COUNT(DISTINCT called) AS DependencyCount,
       COLLECT(DISTINCT called.name) AS DependentPrograms;

// Visualisation du graphe de dépendances pour un programme
// Remplacez 'PROGRAM_NAME' par le nom de votre programme
MATCH path = (p:Program {name: 'PROGRAM_NAME'})-[:CALLS|USES*1..2]->()
RETURN path
LIMIT 100;

// Trouver des chemins de dépendance entre deux programmes
// Remplacez 'PROGRAM_A' et 'PROGRAM_B' par les noms de vos programmes
MATCH path = shortestPath((a:Program {name: 'PROGRAM_A'})-[:CALLS*]->(b:Program {name: 'PROGRAM_B'}))
RETURN path;
```

### 4.5 Analyse par bibliothèque

```cypher
// Répartition des programmes et tables par bibliothèque
MATCH (l:Library)<-[:BELONGS_TO]-(n)
RETURN l.name AS LibraryName, 
       count(DISTINCT CASE WHEN n:Program THEN n END) AS ProgramCount,
       count(DISTINCT CASE WHEN n:Table THEN n END) AS TableCount
ORDER BY ProgramCount DESC;

// Dépendances entre bibliothèques
MATCH (caller:Program)-[:CALLS]->(called:Program)
WHERE caller.library <> called.library
RETURN caller.library AS CallerLibrary, called.library AS CalledLibrary,
       COUNT(DISTINCT caller) AS CallerCount, COUNT(DISTINCT called) AS CalledCount,
       COUNT(*) AS CallCount
ORDER BY CallCount DESC;

// Utilisation des tables entre bibliothèques
MATCH (p:Program)-[:USES]->(t:Table)
WHERE p.library <> t.library
RETURN p.library AS ProgramLibrary, t.library AS TableLibrary,
       COUNT(DISTINCT p) AS ProgramCount, COUNT(DISTINCT t) AS TableCount,
       COUNT(*) AS UseCount
ORDER BY UseCount DESC;
```

## 5. Visualisations et tableaux de bord recommandés

Pour une exploration efficace du graphe, voici quelques visualisations recommandées:

1. **Vue globale de l'architecture** - Visualisation limitée des principaux composants:
   ```cypher
   MATCH (p:Program)-[r]->(target)
   WHERE target:Program OR target:Table
   RETURN p, r, target LIMIT 100;
   ```

2. **Cartographie des dépendances par bibliothèque**:
   ```cypher
   MATCH (l1:Library)<-[:BELONGS_TO]-(p:Program)-[:CALLS]->(called:Program)-[:BELONGS_TO]->(l2:Library)
   WHERE l1 <> l2
   WITH DISTINCT l1, l2, COUNT(*) AS strength
   RETURN l1, l2, strength
   ORDER BY strength DESC
   LIMIT 50;
   ```

3. **Hub de dépendances des programmes critiques**:
   ```cypher
MATCH (p:Program)
WITH 
    p, 
    size([(c)-[:CALLS]->(p) | c]) AS inDegree, 
    size([(p)-[:CALLS]->(c) | c]) AS outDegree
WHERE inDegree > 5 OR outDegree > 5
OPTIONAL MATCH (caller)-[:CALLS]->(p)
OPTIONAL MATCH (p)-[:CALLS]->(called)
RETURN p, caller, called
LIMIT 200;

   ```

## 6. Recommandations

1. **Surveillance des composants critiques** : Établir une liste des programmes et tables les plus utilisés pour une attention particulière lors des modifications.

2. **Documentation automatisée** : Utiliser les requêtes présentées pour générer une documentation dynamique de l'architecture du système.

3. **Analyse d'impact préventive** : Mettre en place un processus pour analyser l'impact de toute modification à l'aide des requêtes d'analyse d'impact.

4. **Nettoyage du patrimoine** : Identifier les composants potentiellement obsolètes (non utilisés) pour évaluer leur pertinence dans le système.

5. **Modularisation** : Utiliser l'analyse des dépendances entre bibliothèques pour identifier les opportunités de modularisation du système.

## 7. Conclusion

L'intégration du patrimoine IBMi dans Neo4j offre une vision claire et exploitable de l'architecture du système. Les scripts fournis permettent d'importer les données, de les vérifier et de les analyser sous différents angles. Ces analyses facilitent la compréhension des dépendances, l'identification des composants critiques et l'évaluation de l'impact des modifications potentielles.

Cette approche graphique constitue un atout majeur pour la gestion et l'évolution du patrimoine IBMi, en fournissant une base solide pour les décisions techniques et stratégiques.
