[![Tests & Quality Checks](https://github.com/Oz-NoXIII/XpathQueryContainment/actions/workflows/tests.yml/badge.svg)](https://github.com/Oz-NoXIII/XpathQueryContainment/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/Oz-NoXIII/XpathQueryContainment/badge.svg?branch=main)](https://coveralls.io/github/Oz-NoXIII/XpathQueryContainment?branch=main)

## Visualisation graphique des `TreePatternQuery`

Le projet inclut maintenant un visualiseur HTML interactif et dynamique :

### Mode interactif (défaut)

```powershell
python main.py
```

Génère `tpq_visualization.html` avec :
- **Rendu dynamique** : Les nœuds apparaissent progressivement lors du parcours de l'arbre
- **Simulation physique** : Les nœuds se repoussent entre eux et les arêtes les attirent pour un layout équilibré
- **Drag-and-drop** : Déplacez les nœuds à la souris pour réorganiser le graphe
- **Stabilisation automatique** : L’animation se met en pause quand le graphe est stabilisé
- **Nœuds persistants** : Un nœud déplacé reste à l’emplacement choisi
- **Contrôles** : Boutons pour pause/play et réinitialisation de l'animation
- **Hiérarchie préservée** : La racine reste en haut et chaque `parent` / `ancestor` est toujours au-dessus de ses `child` / `descendant`

### Mode statique

Pour une version SVG statique plus légère :

```powershell
python main.py --static -o mon_graphe_static.html
```

### Options avancées

```powershell
python main.py "(self[(lab = a)]/child[(lab = b)])" -o mon_graphe.html

# Sans ouvrir le navigateur
python main.py --no-open
```

### Légende visuelle

- **Nœuds** : Cercles contenant le label du nœud
- **Ligne simple** : Relation `child/parent` (arête directe `/`)
- **Double ligne** : Relation `descendant/ancestor` (arête indirecte `//`)

### Légende de l'interface interactive

- **Glisser-déposer** : Cliquez et maintenez pour déplacer un nœud
- **Pause/Play** : Pausez l'animation pour figer les positions
- **Réinitialiser** : Remet les nœuds en position initiale
