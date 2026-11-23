# Mocking (slide 93)

Énoncé : [Testing in Python, partie Mocking](https://courses.dallard.tech/ci_cd/testing_python_intro/#mocking), avec l'exemple de l'API Groq.

`groq_chat.py` reprend la fonction `ask_groq()` du cours et ajoute `ask_with_retry()`, qui retente quand l'API tombe. Les tests remplacent le client Groq par des `Mock` de `unittest.mock` : aucun appel réseau, aucune clé, aucun token dépensé, et le package `groq` n'a même pas besoin d'être installé.

```bash
python3 -m unittest -v   # 8 tests (pytest les lance aussi)
```

| Test | Technique |
|---|---|
| `test_returns_the_answer` | faux client qui a la même forme que la vraie réponse (`choices[0].message.content`) |
| `test_sends_the_right_request` | `assert_called_once_with` : on vérifie la requête envoyée (modèle, messages, `max_tokens`), pas la réponse du LLM |
| `test_empty_question_never_reaches_the_api` | `assert_not_called` : la validation passe avant l'appel |
| `test_api_down` | panne simulée avec `side_effect = Exception("API down")`, l'erreur remonte |
| `test_default_client_is_replaced_with_patch` | sans client passé en argument, `patch.dict(sys.modules, ...)` remplace tout le package `groq` |
| `test_succeeds_after_two_failures` | `side_effect` en liste : timeout, panne, puis réponse ; `call_count == 3` |
| `test_gives_up_after_the_last_attempt` | panne permanente : l'erreur remonte après le dernier essai |
| `test_bad_question_is_not_retried` | une question vide ne déclenche ni appel ni nouvel essai |

Le client est passé en paramètre (`client=None`), ce qui permet d'injecter le faux sans `patch`. `patch` ne sert que pour le cas où la fonction construit elle-même `Groq()`.

Règle du cours : on mocke ce qu'on ne contrôle pas (l'API, le réseau) et on teste ce qu'on a écrit (la validation, la requête construite, la gestion des pannes).
