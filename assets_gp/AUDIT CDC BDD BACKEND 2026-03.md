# 🔎 Audit global de conformité — Cahier des charges vs BDD & Backend

_Date : 2026-03-14_

## 1) Objectif et périmètre

Cet audit repasse sur l’ensemble du **`Cahier des charges.md`** pour vérifier :

1. la conformité du **modèle de données** (SQLAlchemy / migrations),
2. la conformité du **backend** (routes, règles d’accès, séparation MJ/PJ, sécurité),
3. les écarts restants et leur niveau de criticité.

Sources analysées en priorité :
- `assets_gp/Cahier des charges.md`
- `assets_gp/AUDIT LOT 4.md`
- modèles `app/models/*`
- routes `app/web/routes/*`
- use cases `app/application/use_cases/*`
- sécurité transverse (`app/utils/decorators.py`, `config.py`, `app/extensions.py`)

---

## 2) Résultat exécutif

## ✅ Progression globale depuis LOT 4

Par rapport à `AUDIT LOT 4.md`, plusieurs écarts critiques ont été corrigés :
- statut `is_public` des campagnes en place,
- demandes d’adhésion bloquées sur campagnes privées,
- listing des campagnes publiques pour non-connectés,
- contrôle MJ sur la création/gestion des combats rattachés à campagne,
- ajout d’un flux de notes privées MJ sur PJ.

## ⚠️ Niveau de conformité actuel (estimation)

- **Conformité BDD (structure)** : **~82%**
- **Conformité Backend (droits / sécurité métier)** : **~78%**
- **Conformité globale au CDC** : **~80%**

> Le socle est solide, mais il reste des points structurants avant validation “pleinement conforme”, surtout autour de la modélisation PJ multi-campagnes et de certaines surfaces de sécurité backend.

---

## 3) Vérification du modèle BDD vs cahier des charges

## 3.1 Utilisateurs / rôles

- **Conforme globalement** : compte, authentification, rôle utilisateur, capacité MJ/PJ.
- Remarque : le CDC ne demande pas explicitement `Admin`, mais ce rôle additionnel n’est pas bloquant.

**État** : ✅ Conforme

## 3.2 Campagnes

- Le modèle `Campaign` couvre : nom, description, propriétaire MJ, public/privé, activité.
- Modèles d’association présents pour membres, invitations, demandes d’adhésion.

**État** : ✅ Conforme

## 3.3 Arcs narratifs

- Rattachement campagne + données métier alignées.

**État** : ✅ Conforme

## 3.4 Personnages PJ / PNJ

- Le cœur des attributs perso est bien présent (stats, CA, initiative, XP, notes, fichiers).
- La gestion de visibilité PNJ est présente (`visibility_level`).
- **Écart majeur** : le CDC demande qu’un PJ puisse être ajouté à **une ou plusieurs campagnes**.
  - Le modèle possède une table many-to-many (`character_campaign_association`),
  - mais le backend principal continue surtout d’utiliser `character.campaign_id` (association mono-campagne).

**État** : ⚠️ Partiellement conforme (écart structurel + usage)

## 3.5 Combats / logs / stats

- Modèle `Combat` : rounds/tours, rattachement campagne + arc (nullable), timestamps, fermeture.
- Modèle `CombatLog` adapté à la traçabilité et à l’agrégation.

**État** : ✅ Conforme (avec nuance d’usage backend sur combats non rattachés)

---

## 4) Vérification backend vs cahier des charges (droits, visibilité, sécurité)

## 4.1 Accès non connecté / campagnes publiques

- Page d’accueil publique et listing de campagnes publiques implémentés.
- Flux de demande d’adhésion disponible et protégé côté service (campagne publique requise).

**État** : ✅ Conforme

## 4.2 Droits MJ propriétaire de campagne

- Création/modification/suppression campagne : contrôles MJ présents.
- Gestion invitations + approbation/rejet demandes : contrôles MJ présents.
- Gestion arcs narratifs : MJ uniquement.

**État** : ✅ Conforme

## 4.3 Droits joueurs

- Joueur peut demander à rejoindre (campagne publique), accepter/refuser invitation, accéder vue player combat (si membre).
- Participation au combat en mode “player view” bien séparée de la vue MJ.

**État** : ✅ Conforme

## 4.4 Personnages : droits d’édition et visibilité

- Édition PJ par propriétaire : ok.
- Édition PJ par MJ de campagne : prise en charge via `can_be_edited_by`.
- Notes privées MJ sur PJ : route dédiée présente.
- Visibilité PNJ (private/reduced/semi_complete/complete) : présente.

**État** : ✅ Conforme fonctionnellement, ⚠️ avec dette de conception multi-campagnes

## 4.5 Combats : contrôles d’accès

- Les actions de gestion combat sont correctement restreintes au MJ (ou Admin).
- La vue player est conditionnée à l’appartenance campagne.
- **Écart restant** : les combats non rattachés à une campagne restent possibles (`story_arc_id` optionnel) avec des règles plus permissives ; cela s’éloigne du CDC (“combat rattaché à un arc narratif”).

**État** : ⚠️ Partiellement conforme

## 4.6 Sécurité transverse

### Points positifs
- `login_required` robuste (session + utilisateur actif).
- Contrôles métier centralisés dans plusieurs routes/services.
- Cookies `HttpOnly`, option `Secure` configurable.

### Points de vigilance
1. **CSRF** : `WTF_CSRF_ENABLED=True` est configuré, mais pas d’initialisation visible de `CSRFProtect`.
   - Risque : endpoints POST potentiellement non protégés si aucun autre mécanisme n’est en place.
2. **Contrôle d’accès objet incomplet sur certains objets non scoped**
   - Ex.: templates de rencontres (`EncounterTemplate`) manipulables sans ownership explicite.
3. **Validation métier hétérogène**
   - Certains endpoints reposent surtout sur la route, moins sur un garde-fou de service/policy partagé.

**État** : ⚠️ À renforcer avant validation sécurité complète

---

## 5) Matrice de conformité synthétique (CDC)

| Domaine CDC | BDD | Backend | Statut |
|---|---:|---:|---|
| Utilisateurs (inscription/login/profil) | ✅ | ✅ | Conforme |
| Campagnes (public/privé, membres, invitations) | ✅ | ✅ | Conforme |
| Arcs narratifs (MJ only) | ✅ | ✅ | Conforme |
| PJ (cycle de vie + droits) | ⚠️ | ⚠️ | Partiel (multi-campagnes) |
| PNJ (MJ only + visibilité fine) | ✅ | ✅ | Conforme |
| Combats (MJ full / player limité) | ✅ | ⚠️ | Partiel (combats non rattachés) |
| Logs & agrégation (combat/arc/campagne) | ✅ | ✅ | Conforme |
| Isolation + sécurité transverse | ⚠️ | ⚠️ | Partiel (CSRF + ownership) |

---

## 6) Écarts prioritaires à traiter

## 🔥 Priorité 1 (critique)

1. **Aligner définitivement PJ multi-campagnes**
   - Basculer les usages backend/UI vers `character_campaign_association`.
   - Définir la campagne “active” d’un PJ si nécessaire (sans casser le M2M).

2. **Imposer le rattachement combat → arc/campagne**
   - Rendre obligatoire `story_arc_id` à la création (ou policy explicite documentée).
   - Interdire les combats “hors campagne” en production si non requis.

3. **Activer réellement la protection CSRF**
   - Initialiser `CSRFProtect(app)` (ou stratégie équivalente) et vérifier tous les formulaires/POST.

## ⚡ Priorité 2 (haute)

4. **Renforcer ownership/ACL des EncounterTemplate**
   - Ajouter `owner_id` et filtrer CRUD par propriétaire (ou par campagne).

5. **Centraliser les règles d’accès sensibles**
   - Extraire une policy unique (combat, personnage, campagne) pour limiter les divergences route/service.

## 📝 Priorité 3 (moyenne)

6. **Normaliser les champs “état”**
   - Revoir les champs incohérents (ex. `JoinRequest.is_public`) pour éviter ambiguïtés métier.

7. **Tests d’autorisation automatiques**
   - Ajouter des tests backend ciblant les scénarios MJ/PJ/non-connecté.

---

## 7) Conclusion

Le projet a clairement progressé depuis LOT 4, et une grande partie du CDC est désormais couverte.

La **principale dette fonctionnelle** reste la promesse “PJ multi-campagnes” (modèle présent mais usage partiel), et la **principale dette sécurité** est l’activation effective/confirmée de la protection CSRF + homogénéité ACL sur certains objets.

👉 Recommandation : traiter les priorités 1 en premier, puis rejouer un audit de conformité final pour valider le passage au lot suivant.
