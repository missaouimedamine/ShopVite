# Reflection - Prompt Engineering

## Justification du prompt engineering

Le prompt a été conçu pour garantir des réponses fiables dans un système RAG. Des règles strictes obligent le modèle à utiliser uniquement le contexte fourni afin de limiter les hallucinations. Les exemples few-shot permettent de guider le format et le ton des réponses. La logique de raisonnement interne améliore la pertinence sans être affichée à l’utilisateur. Enfin, l’obligation de citer les sources renforce la traçabilité et la confiance dans les réponses.

## Améliorations possibles

Avec plus de temps, j’ajouterais un reranking des documents pour améliorer la qualité du contexte récupéré. Je mettrais aussi en place une mémoire conversationnelle pour gérer les échanges multi-tours. Le prompt pourrait être versionné et testé automatiquement pour optimiser ses performances.

## Limitation actuelle

Le principal problème est la dépendance à la qualité du retrieval : si les documents récupérés sont incomplets ou peu pertinents, la réponse finale est limitée. Il n’y a pas non plus de vérification automatique des sources, ce qui peut laisser passer du bruit dans le contexte.