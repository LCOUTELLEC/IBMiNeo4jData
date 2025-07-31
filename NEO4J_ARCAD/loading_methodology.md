# Méthodologie de Chargement Neo4j - Patrimoine IBMi

## Phase 1 : Préparation des Données

### 1.1 Transformation Excel → CSV
```bash
# Convertir les fichiers Excel en CSV pour optimiser les performances
# Utiliser un outil comme pandas ou xlsxtocsv
```

### 1.2 Nettoyage des Données
- Suppression des espaces en fin de chaîne (trim)
- Normalisation des dates (format ISO)
- Validation des champs obligatoires
- Résolution des valeurs nulles ou vides

### 1.3 Filtrage Métier
- **Sources :** Conserver uniquement les types pertinents (RPG, RPGLE, CLP, etc.)
- **Objets :** Séparer programmes (*PGM) et tables (*FILE/PF,TABLE)
- **XREF :** Valider la cohérence des références

## Phase 2 : Initialisation de la Base

### 2.1 Création des Contraintes et Index
```cypher
// Exécuter en premier pour optimiser les performances
// Voir le modèle de données pour la liste complète
```

### 2.2 Nettoyage de la Base (si nécessaire)
```cypher
MATCH (n) DETACH DELETE n;
```

## Phase 3 : Chargement des Nœuds (Ordre d'Exécution)

### 3.1 Applications (Métadonnées)
```cypher
LOAD CSV WITH HEADERS FROM 'file:///applications.csv' AS row
MERGE (app:Application {name: trim(row.LST_CAPP)})
SET app.environment = trim(row.LST_CENV),
    app.version = trim(row.LST_CVER);
```

### 3.2 Types et Attributs (Métadonnées)
```cypher
// TypeObjIBMi
LOAD CSV WITH HEADERS FROM 'file:///types_ibmi.csv' AS row
MERGE (type:TypeObjIBMi {name: trim(row.type_name)})
SET type.description = row.description;

// TypeObjARCAD
LOAD CSV WITH HEADERS FROM 'file:///types_arcad.csv' AS row
MERGE (type:TypeObjARCAD {name: trim(row.type_name)})
SET type.description = row.description;

// Attributs
LOAD CSV WITH HEADERS FROM 'file:///attributs.csv' AS row
MERGE (attr:Attribut {name: trim(row.attr_name)})
SET attr.description = row.description;
```

### 3.3 Sources
```cypher
LOAD CSV WITH HEADERS FROM 'file:///sources_filtered.csv' AS row
WITH row WHERE row.LST_CELTTY = 'M' AND row.LST_CTYPE IN ['RPG', 'RPGLE', 'SQLRPG', 'SQLRPGLE', 'CLP', 'CLLE', 'CBL', '*FILE']
MERGE (src:Source {
    name: trim(row.LST_JOBJ), 
    library: trim(row.LST_JLIB),
    sourceFile: trim(row.LST_JSRCF)
})
SET src.sourceType = trim(row.LST_CTYPE),
    src.description = trim(row.LST_CTXT),
    src.lastModified = date(substring(toString(row.LST_TDATE), 0, 4) + '-' + 
                           substring(toString(row.LST_TDATE), 4, 2) + '-' + 
                           substring(toString(row.LST_TDATE), 6, 2)),
    src.lineCount = toInteger(row.LST_JZSEL1);
```

### 3.4 Programmes
```cypher
LOAD CSV WITH HEADERS FROM 'file:///objets_programmes.csv' AS row
WITH row WHERE row.LST_CELTTY = 'O' AND row.LST_CTYPE = '*PGM'
MERGE (pgm:Programme {
    name: trim(row.LST_JOBJ), 
    library: trim(row.LST_JLIB)
})
SET pgm.type = trim(row.LST_CTYPE),
    pgm.attribute = trim(row.LST_CATR),
    pgm.arcadType = trim(row.LST_CCPLT),
    pgm.description = trim(row.LST_CTXT),
    pgm.lastModified = date(substring(toString(row.LST_TDATE), 0, 4) + '-' + 
                           substring(toString(row.LST_TDATE), 4, 2) + '-' + 
                           substring(toString(row.LST_TDATE), 6, 2));
```

### 3.5 Tables
```cypher
LOAD CSV WITH HEADERS FROM 'file:///objets_tables.csv' AS row
WITH row WHERE row.LST_CELTTY = 'O' AND row.LST_CTYPE = '*FILE' 
         AND row.LST_CATR IN ['PF', 'TABLE']
MERGE (tbl:Table {
    name: trim(row.LST_JOBJ), 
    library: trim(row.LST_JLIB)
})
SET tbl.type = trim(row.LST_CTYPE),
    tbl.attribute = trim(row.LST_CATR),
    tbl.arcadType = trim(row.LST_CCPLT),
    tbl.description = trim(row.LST_CTXT),
    tbl.lastModified = date(substring(toString(row.LST_TDATE), 0, 4) + '-' + 
                           substring(toString(row.LST_TDATE), 4, 2) + '-' + 
                           substring(toString(row.LST_TDATE), 6, 2));
```

## Phase 4 : Création des Relations

### 4.1 Relations BELONGS_TO
```cypher
// Sources → Applications
MATCH (src:Source), (app:Application)
WHERE EXISTS {
    MATCH (obj) WHERE obj.name = src.name AND obj.library = src.library
    WITH obj MATCH (obj)-[:BELONGS_TO]->(a:Application {name: app.name})
}
MERGE (src)-[:BELONGS_TO]->(app);

// Programmes → Applications  
LOAD CSV WITH HEADERS FROM 'file:///objets_programmes.csv' AS row
MATCH (pgm:Programme {name: trim(row.LST_JOBJ), library: trim(row.LST_JLIB)})
MATCH (app:Application {name: trim(row.LST_CAPP)})
MERGE (pgm)-[:BELONGS_TO]->(app);

// Tables → Applications
LOAD CSV WITH HEADERS FROM 'file:///objets_tables.csv' AS row
MATCH (tbl:Table {name: trim(row.LST_JOBJ), library: trim(row.LST_JLIB)})
MATCH (app:Application {name: trim(row.LST_CAPP)})
MERGE (tbl)-[:BELONGS_TO]->(app);
```

### 4.2 Relations GENERATES
```cypher
// Sources → Programmes/Tables via correspondance nom/bibliothèque
MATCH (src:Source), (pgm:Programme)
WHERE src.name = pgm.name AND src.library = pgm.library
    AND src.sourceType IN ['RPG', 'RPGLE', 'SQLRPG', 'SQLRPGLE', 'CLP', 'CLLE', 'CBL']
MERGE (src)-[:GENERATES]->(pgm);

MATCH (src:Source), (tbl:Table)
WHERE src.name = tbl.name AND src.library = tbl.library
    AND (src.sourceFile = 'QDDSSRC' OR src.sourceFile = 'QSQLSRC')
MERGE (src)-[:GENERATES]->(tbl);
```

### 4.3 Relations CALLS et USES (Références Croisées)
```cypher
// Relations CALLS (Programme → Programme)
LOAD CSV WITH HEADERS FROM 'file:///xref.csv' AS row
WITH row WHERE row.OXR_FROM_TYPE = '*PGM' AND row.OXR_TO_TYPE = '*PGM'
MATCH (fromPgm:Programme {name: trim(row.OXR_FROM_OBJ), library: trim(row.OXR_FROM_LIB)})
MATCH (toPgm:Programme {name: trim(row.OXR_TO_OBJ), library: trim(row.OXR_TO_LIB)})
MERGE (fromPgm)-[r:CALLS]->(toPgm)
SET r.callType = 'CALL';

// Relations USES (Programme → Table)
LOAD CSV WITH HEADERS FROM 'file:///xref.csv' AS row
WITH row WHERE row.OXR_FROM_TYPE = '*PGM' AND row.OXR_TO_TYPE = '*FILE'
MATCH (pgm:Programme {name: trim(row.OXR_FROM_OBJ), library: trim(row.OXR_FROM_LIB)})
MATCH (tbl:Table {name: trim(row.OXR_TO_OBJ), library: trim(row.OXR_TO_LIB)})
MERGE (pgm)-[r:USES]->(tbl)
SET r.usageType = 'USE',
    r.logicalFile = CASE WHEN trim(row.OXR_TO_LF_OBJ) <> '' 
                        THEN trim(row.OXR_TO_LF_OBJ) 
                        ELSE null END;
```

### 4.4 Relations de Typage
```cypher
// TYPED_AS_IBM
MATCH (pgm:Programme), (type:TypeObjIBMi {name: pgm.type})
MERGE (pgm)-[:TYPED_AS_IBM]->(type);

MATCH (tbl:Table), (type:TypeObjIBMi {name: tbl.type})
MERGE (tbl)-[:TYPED_AS_IBM]->(type);

// TYPED_AS_ARCAD
MATCH (pgm:Programme), (type:TypeObjARCAD {name: pgm.arcadType})
MERGE (pgm)-[:TYPED_AS_ARCAD]->(type);

MATCH (tbl:Table), (type:TypeObjARCAD {name: tbl.arcadType})
MERGE (tbl)-[:TYPED_AS_ARCAD]->(type);

// HAS_ATTRIBUTE
MATCH (pgm:Programme), (attr:Attribut {name: pgm.attribute})
MERGE (pgm)-[:HAS_ATTRIBUTE]->(attr);

MATCH (tbl:Table), (attr:Attribut {name: tbl.attribute})
MERGE (tbl)-[:HAS_ATTRIBUTE]->(attr);
```

## Phase 5 : Validation et Optimisation

### 5.1 Contrôles de Cohérence
```cypher
// Vérification du nombre de nœuds créés
MATCH (n) RETURN labels(n)[0] as NodeType, count(n) as Count;

// Vérification des relations
MATCH ()-[r]->() RETURN type(r) as RelationType, count(r) as Count;

// Identification des nœuds isolés
MATCH (n) WHERE NOT (n)--() RETURN labels(n)[0] as NodeType, count(n) as IsolatedCount;
```

### 5.2 Nettoyage des Données Incohérentes
```cypher
// Suppression des nœuds sans propriétés essentielles
MATCH (n:Programme) WHERE n.name IS NULL OR n.library IS NULL DELETE n;
MATCH (n:Table) WHERE n.name IS NULL OR n.library IS NULL DELETE n;
MATCH (n:Source) WHERE n.name IS NULL OR n.library IS NULL DELETE n;
```

### 5.3 Statistiques Finales
```cypher
// Rapport de chargement complet
CALL {
    MATCH (app:Application) RETURN 'Applications' as Type, count(app) as Count
    UNION
    MATCH (pgm:Programme) RETURN 'Programmes' as Type, count(pgm) as Count
    UNION
    MATCH (tbl:Table) RETURN 'Tables' as Type, count(tbl) as Count
    UNION
    MATCH (src:Source) RETURN 'Sources' as Type, count(src) as Count
    UNION
    MATCH ()-[r:CALLS]->() RETURN 'Relations CALLS' as Type, count(r) as Count
    UNION
    MATCH ()-[r:USES]->() RETURN 'Relations USES' as Type, count(r) as Count
    UNION
    MATCH ()-[r:GENERATES]->() RETURN 'Relations GENERATES' as Type, count(r) as Count
}
RETURN Type, Count ORDER BY Type;
```

## Phase 6 : Scripts d'Analyse Post-Chargement

### 6.1 Requêtes de Validation Métier
```cypher
// Top 10 des programmes les plus appelés
MATCH (pgm:Programme)<-[:CALLS]-(caller)
RETURN pgm.name, pgm.library, count(caller) as CallCount
ORDER BY CallCount DESC LIMIT 10;

// Top 10 des tables les plus utilisées
MATCH (tbl:Table)<-[:USES]-(pgm)
RETURN tbl.name, tbl.library, count(pgm) as UserCount
ORDER BY UserCount DESC LIMIT 10;

// Programmes sans sources identifiées
MATCH (pgm:Programme)
WHERE NOT EXISTS { MATCH (src:Source)-[:GENERATES]->(pgm) }
RETURN pgm.name, pgm.library, pgm.attribute;
```

### 6.2 Analyse d'Impact
```cypher
// Impact d'une modification de table
MATCH path = (tbl:Table {name: 'NOMTABLE'})<-[:USES*1..3]-(pgm:Programme)
RETURN path LIMIT 50;

// Analyse des dépendances d'un programme
MATCH path = (pgm:Programme {name: 'NOMPGM'})-[:CALLS|USES*1..2]->(target)
RETURN path LIMIT 50;
```

## Configuration et Optimisation

### Paramètres Neo4j Recommandés
```properties
# neo4j.conf
dbms.memory.heap.initial_size=2G
dbms.memory.heap.max_size=4G
dbms.memory.pagecache.size=2G

# Pour les gros chargements
dbms.tx_log.rotation.retention_policy=false
dbms.checkpoint.interval.time=30m
```

### Monitoring du Chargement
```cypher
// Suivi des performances pendant le chargement
CALL dbms.listTransactions() YIELD transactionId, status, elapsedTimeMillis
WHERE elapsedTimeMillis > 10000
RETURN transactionId, status, elapsedTimeMillis;
```

## Gestion des Erreurs

### Rollback en Cas d'Échec
```cypher
// Sauvegarde avant chargement majeur
CALL apoc.export.graphml.all("backup_before_load.graphml", {});

// Restauration si nécessaire
MATCH (n) DETACH DELETE n;
CALL apoc.import.graphml("backup_before_load.graphml", {});
```

### Log des Erreurs
- Utiliser des transactions par batch (1000-5000 lignes)
- Logger les échecs de MERGE pour investigation
- Prévoir des reprises partielles par type de nœud