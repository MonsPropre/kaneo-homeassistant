# Kaneo – Intégration Home Assistant

Intégration Home Assistant pour [Kaneo](https://kaneo.app), un gestionnaire de tâches open-source.

---

## Fonctionnalités

- **Config Flow** : configuration entièrement via l'interface graphique de HA
- **Sensor** : un capteur `sensor.kaneo_taches` exposant le nombre total de tâches
- **Attributs** : liste complète des tâches (titre, statut, priorité, date d'échéance, projet, assigné…)
- **Options** : intervalle de mise à jour configurable (par défaut : 5 minutes)
- **Multi-instances** : plusieurs workspaces Kaneo supportés simultanément

---

## Installation

### Via HACS (recommandé)

1. Ouvrez HACS dans Home Assistant
2. Allez dans **Intégrations** → menu `⋮` → **Dépôts personnalisés**
3. Ajoutez l'URL de ce dépôt avec la catégorie **Integration**
4. Installez **Kaneo**
5. Redémarrez Home Assistant

### Manuellement

1. Copiez le dossier `custom_components/kaneo/` dans votre répertoire `config/custom_components/`
2. Redémarrez Home Assistant

---

## Configuration

1. Allez dans **Paramètres** → **Appareils & Services** → **Ajouter une intégration**
2. Recherchez **Kaneo**
3. Remplissez les champs :

| Champ | Description | Exemple |
|-------|-------------|---------|
| **URL de l'instance** | URL de votre Kaneo | `https://cloud.kaneo.app` ou votre instance self-hosted |
| **Token d'API** | Bearer token de votre compte | `eyJhbGci...` |
| **ID du Workspace** | Identifiant de votre workspace | `ws_abc123` |

### Obtenir votre Token d'API

1. Connectez-vous à votre instance Kaneo
2. Allez dans **Profil** → **Paramètres** → **API Tokens**
3. Créez un nouveau token et copiez-le

### Trouver votre Workspace ID

L'ID du workspace est visible dans l'URL de votre instance Kaneo ou dans les paramètres du workspace.

---

## Entités créées

### `sensor.kaneo_taches`

| Propriété | Valeur |
|-----------|--------|
| **État** | Nombre total de tâches |
| **Unité** | tâches |
| **Icône** | `mdi:checkbox-marked-outline` |

**Attributs disponibles :**

```yaml
total_tasks: 42
tasks:
  - id: "task_abc"
    title: "Corriger le bug #123"
    status: "En cours"
    priority: "high"
    due_date: "2025-04-15"
    project: "Mon Projet"
    assignee: "Jean Dupont"
    created_at: "2025-03-01T10:00:00Z"
    description: "Description de la tâche"
    number: 42
  - ...
```

---

## Exemples d'automatisations

### Notification si des tâches sont en retard

```yaml
automation:
  - alias: "Kaneo - Tâches en retard"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: notify.mobile_app
        data:
          title: "Tâches Kaneo"
          message: "Vous avez {{ states('sensor.kaneo_taches') }} tâches actives."
```

### Template sensor pour filtrer par priorité

```yaml
template:
  - sensor:
      - name: "Kaneo Tâches Haute Priorité"
        state: >
          {{ state_attr('sensor.kaneo_taches', 'tasks')
             | selectattr('priority', 'eq', 'high')
             | list | count }}
        unit_of_measurement: "tâches"
```

---

## Options

Après configuration, vous pouvez modifier l'intervalle de mise à jour via **Paramètres** → **Appareils & Services** → **Kaneo** → **Configurer**.

- **Intervalle minimum** : 60 secondes
- **Intervalle maximum** : 86400 secondes (24h)
- **Valeur par défaut** : 300 secondes (5 minutes)

---

## Structure des fichiers

```
custom_components/kaneo/
├── __init__.py          # Setup de l'intégration
├── api.py               # Client API Kaneo
├── config_flow.py       # Config flow UI
├── const.py             # Constantes
├── coordinator.py       # DataUpdateCoordinator
├── manifest.json        # Métadonnées HA
├── sensor.py            # Plateforme sensor
├── strings.json         # Chaînes de traduction
└── translations/
    └── fr.json          # Traduction française
```
