// 1. CRÉATION DES CONTRAINTES ET INDEX POUR ASSURER L'UNICITÉ
// =================================================================

// Contrainte sur les nœuds Programme
CREATE CONSTRAINT programme_id_unique IF NOT EXISTS
FOR (p:Programme)
REQUIRE p.id IS UNIQUE;

// Contrainte sur les nœuds Entite
CREATE CONSTRAINT entite_id_unique IF NOT EXISTS
FOR (e:Entite)
REQUIRE e.id IS UNIQUE;

// Contrainte sur les nœuds Index
CREATE CONSTRAINT index_id_unique IF NOT EXISTS
FOR (i:Index)
REQUIRE i.id IS UNIQUE;

// Contrainte sur les nœuds Propriete
CREATE CONSTRAINT propriete_id_unique IF NOT EXISTS
FOR (p:Propriete)
REQUIRE p.id IS UNIQUE;

// 2. IMPORTATION DES PROGRAMMES
// =================================================================
LOAD CSV WITH HEADERS FROM 'file:///Adelia_Programmes.csv' AS ligne FIELDTERMINATOR '#'
CREATE (p:Programme {
  id: ligne.ID_Base_Adelia + '::' + ligne.Nom_Interne_Programme,
  nom: ligne.Nom_Externe_Programme,
  libelle: ligne.Libelle_Objet,
  typeServeur: ligne.Type_Serveur,
  typeProgramme: ligne.Type_Programme,
  dateModification: ligne.Date_Modification,
  codeVisibilite: toInteger(coalesce(ligne.Code_Visibilite, '0')),
  modeGeneration: ligne.Mode_Generation,
  dateCreation: ligne.Date_Creation,
  commentaireQualite: ligne.Commentaire_Qualite,
  numeroVersion: ligne.Numero_Version,
  numeroRelease: ligne.Numero_Release,
  numeroModification: ligne.Numero_Modification,
  numeroBuild: ligne.Numero_Build
});

// 3. IMPORTATION DES ENTITÉS (TABLES)
// =================================================================
LOAD CSV WITH HEADERS FROM 'file:///Adelia_Entites.csv' AS ligne FIELDTERMINATOR '#'
CREATE (e:Entite {
  id: ligne.ID_Base_Adelia + '::' + ligne.ID_Adelia_Entite,
  type: ligne.Type_Objet_Entite, 
  nom: ligne.Nom_Adelia_Entite,
  libelle: ligne.Libelle_Entite,
  dateCreation: ligne.Date_Creation_Entite,
  dateModification: ligne.Date_Modification_Entite,
  codeVisibilite: toInteger(coalesce(ligne.Code_Visibilite_Entite, '0')),
  typeOrigine: ligne.Type_Origine_Entite,
  nomAS400: ligne.Nom_AS400_Entite,
  nomLogique: ligne.Nom_Logique_Entite,
  nomInterne: ligne.Nom_Interne_Entite,
  nomSQL: ligne.Nom_SQL_Entite,
  nomSchemaSQL: ligne.Nom_Schema_SQL_Entite
});

// 4. IMPORTATION DES INDEX
// =================================================================
LOAD CSV WITH HEADERS FROM 'file:///Adelia_Index.csv' AS ligne FIELDTERMINATOR '#'
CREATE (i:Index {
  id: ligne.ID_Base_Adelia + '::' + ligne.ID_Adelia_Index,
  type: ligne.Type_Objet_Index,
  nom: ligne.Nom_Adelia_Index,
  libelle: ligne.Libelle_Index,
  dateCreation: ligne.Date_Creation_Index,
  dateModification: ligne.Date_Modification_Index,
  flagCleUnique: ligne.Flag_CleUnique_Index,
  dateGeneration: ligne.Date_Generation_Index
});

// 5. IMPORTATION DES PROPRIÉTÉS (ATTRIBUTS)
// =================================================================
LOAD CSV WITH HEADERS FROM 'file:///Adelia_Proprietes.csv' AS ligne FIELDTERMINATOR '#'
CREATE (p:Propriete {
  id: ligne.ID_Base_Adelia + '::' + ligne.ID_Propriété,
  typeObjet: ligne.Type_Objet_Propriété,
  numeroOrdre: toInteger(coalesce(ligne.Numero_Ordre_Propriété, '0')),
  identifiant: ligne.Identifiant_Propriete,
  codeDDS: ligne.Code_DDS_Propriété,
  libelle: ligne.Libelle_Propriété,
  motDirecteur: ligne.MotDirecteur_Propriété,
  longueur: toInteger(coalesce(ligne.Longueur_Propriété, '0')),
  nbDecimales: toInteger(coalesce(ligne.Nb_Decimales_Propriété, '0')),
  nomTypeDonnee: ligne.Nom_Type_Donnee_Propriété,
  typeNumerique: ligne.Type_Numerique_Propriété,
  zoneVisibilite: toInteger(coalesce(ligne.Zone_Visibilite_Propriété, '0')),
  idConceptuel: ligne.ID_Conceptuel_Propriete
});

// 6. CRÉATION DES RELATIONS ENTRE INDEX ET ENTITÉS
// =================================================================
// Lier chaque index à son entité parent
LOAD CSV WITH HEADERS FROM 'file:///Adelia_Index.csv' AS ligne FIELDTERMINATOR '#'
MATCH (i:Index {id: ligne.ID_Base_Adelia + '::' + ligne.ID_Adelia_Index})
MATCH (e:Entite {id: ligne.ID_Base_Adelia + '::' + ligne.ID_Adelia_Entite})
CREATE (i)-[:INDEXE]->(e);

// 7. CRÉATION DES RELATIONS ENTRE PROPRIÉTÉS ET ENTITÉS
// =================================================================
// Lier chaque propriété à son entité parent
LOAD CSV WITH HEADERS FROM 'file:///Adelia_Proprietes.csv' AS ligne FIELDTERMINATOR '#'
MATCH (p:Propriete {id: ligne.ID_Base_Adelia + '::' + ligne.ID_Propriété})
MATCH (e:Entite {id: ligne.ID_Entite})
CREATE (e)-[:A_POUR_ATTRIBUT]->(p);

// 8. CRÉATION DES RELATIONS ENTRE PROGRAMMES (CALL)
// =================================================================
LOAD CSV WITH HEADERS FROM 'file:///Adelia_XREF_PGM_PGM.csv' AS ligne FIELDTERMINATOR '#'
MATCH (caller:Programme {id: ligne.ID_Base_Adelia + '::' + ligne.ID_Programme_Caller})
MATCH (callee:Programme {id: ligne.ID_Base_Adelia + '::' + ligne.ID_Objet_Callee})
CREATE (caller)-[:CALL {
  clientServer: toInteger(coalesce(ligne.Call_Client_Server, '0'))
}]->(callee);

// 9. CRÉATION DES RELATIONS ENTRE PROGRAMMES ET ENTITÉS (USE)
// =================================================================
LOAD CSV WITH HEADERS FROM 'file:///Adelia_XREF_PGM_Table.csv' AS ligne FIELDTERMINATOR '#'
MATCH (prog:Programme {id: ligne.ID_Base_Adelia + '::' + ligne.ID_Programme_Caller})
MATCH (ent:Entite {id: ligne.ID_Base_Adelia + '::' + ligne.ID_Objet_Callee})
CREATE (prog)-[:USE {
  clientServer: toInteger(coalesce(ligne.Call_Client_Server, '0'))
}]->(ent);

// 10. REQUÊTES UTILES
// =================================================================

// Obtenir les programmes qui utilisent une entité spécifique
// MATCH (p:Programme)-[:USE]->(e:Entite {nom: 'NOM_ENTITE'})
// RETURN p.nom, p.typeProgramme

// Obtenir les relations entre programmes
// MATCH (p1:Programme)-[r:CALL]->(p2:Programme)
// RETURN p1.nom, p2.nom, r.clientServer

// Obtenir les entités et leurs attributs
// MATCH (e:Entite)-[:A_POUR_ATTRIBUT]->(p:Propriete)
// RETURN e.nom, collect(p.libelle) as attributs

// Obtenir les entités et leurs index
// MATCH (i:Index)-[:INDEXE]->(e:Entite)
// RETURN e.nom, collect(i.nom) as indexes

// Trouver les programmes sans relation avec d'autres programmes
// MATCH (p:Programme)
// WHERE NOT (p)-[:CALL]->() AND NOT ()-[:CALL]->(p)
// RETURN p.nom
