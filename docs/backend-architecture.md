# Backend Architecture (Layered + Compatibility)

## Cible

Le backend est maintenant organisé en couches:

- `app/web`: HTTP routes, Socket.IO events, présentation.
- `app/application`: use cases, orchestration métier, ports.
- `app/domain`: règles métier pures (policies).
- `app/infrastructure`: persistance, mail, fichiers, implémentations techniques.
- `app/shared`: objets et erreurs transverses.

## Arborescence active

```text
app/
  web/
    routes/
    sockets/
  application/
    use_cases/
    ports/
  domain/
  infrastructure/
    persistence/sqlalchemy/
  shared/
  services/   # wrappers legacy -> application.use_cases
  routes/     # wrappers legacy -> web.routes
```

## Compatibilité maintenue

- `app/services/*` reste disponible, mais redirige vers `app/application/use_cases/*`.
- `app/routes/*` reste disponible, mais redirige vers `app/web/routes/*`.
- `app/routes/__init__.py` expose toujours `register_blueprints`.

Objectif: éviter un "big bang" et permettre une migration progressive du code appelant.

## Ce qui est déjà basculé

- `create_app()` enregistre les blueprints via `app.web.routes`.
- Les événements Socket.IO sont enregistrés via `app.web.sockets`.
- Le web layer consomme directement `app.application.use_cases`.

## Prochaine étape recommandée

1. Remplacer les accès ORM directs dans les use cases par les `ports` + `infrastructure` (repositories + unit of work).
2. Introduire des tests de smoke (`create_app`, blueprints, flux critique combat/campagne).
3. Renommer progressivement les classes `*Service` en `*UseCase` (avec alias de compatibilité).
