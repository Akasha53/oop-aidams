# OOP & Design patterns in Python (AIDAMS 2A)

Exercices du cours Object Oriented Programming ISDS51040, CentraleSupélec.

| Dossier | Slide | Énoncé | Contenu |
|---|---|---|---|
| `OOP_exo/` | 67 | [gist](https://gist.github.com/bdallard/b2f2c910e3a9b564a30c86991c97b4fc) | Surcharge d'opérateurs (`Complex`, `Vector`, `Circle`, `Point`, `Matrix`…) et héritage (`Vehicle`, `Person`, `BankAccount`) |
| `GIT_exo/` | 26 | [gist](https://gist.github.com/bdallard/8bdbdd70f234f94823c0c2cde9515388) | Réponses de l'exo Git. Le dépôt final de la partie 11 est [bash-installer](https://github.com/Akasha53/bash-installer) |
| `UML_exo/` | 68 | [gist](https://gist.github.com/bdallard/2d2407c4de4c182afca6d3ec7235e9eb) | Diagrammes UML en Mermaid (`SOLUTION.md`) et implémentation : Hospital Management System, ABCD Records |
| `DesignPatterns_exo/` | 84 | pages [creational](https://courses.dallard.tech/sys_design/creational_pattern/), [structural](https://courses.dallard.tech/sys_design/structural_pattern/), [behavioral](https://courses.dallard.tech/sys_design/behavioral_pattern/) | Les sept exercices de refactoring (Factory, Builder, Singleton, Adapter, Decorator, Strategy, Template Method), diagrammes Mermaid dans le README du dossier |
| `Mocking_exo/` | 93 | [testing intro](https://courses.dallard.tech/ci_cd/testing_python_intro/#mocking) | Tester `ask_groq()` sans appeler l'API Groq : `unittest.mock`, panne simulée, nouvel essai |

Python 3.10 ou plus récent, aucune dépendance.

```bash
cd OOP_exo && python3 -m unittest -v
cd UML_exo && python3 -m unittest -v
cd DesignPatterns_exo && python3 -m unittest -v
cd Mocking_exo && python3 -m unittest -v
```
