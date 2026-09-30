# Git mini exo : réponses (slide 26)

Énoncé : https://gist.github.com/bdallard/8bdbdd70f234f94823c0c2cde9515388
Résultat de la partie 11 : https://github.com/Akasha53/bash-installer

## Part 1 : Setup & config

```bash
git --version
git config --global user.name "Akasha53"
git config --global user.email "134799967+Akasha53@users.noreply.github.com"
```

## Part 2 : Create your first repository

```bash
mkdir my-first-repo
cd my-first-repo
git init
touch readme.txt
```

## Part 3 : Your first commit

1. `git status`
2. `git add readme.txt`
3. `git commit -m "Add readme file"`
4. `git log`

## Part 4 : Make changes

1. `echo "First line of text" >> readme.txt`
2. `git status` indique que `readme.txt` est modifié mais pas encore indexé (`Changes not staged for commit`). Git voit la différence avec le dernier commit, elle n'est pas encore sauvegardée.
3. `git add readme.txt && git commit -m "Add a line to readme"`
4. Deux commits.

## Part 5 : Exploration

- `git diff` affiche, ligne par ligne, les modifications du répertoire de travail qui ne sont pas encore indexées (`+` ajout, `-` suppression). `git diff --staged` fait la même chose pour ce qui est indexé.
- `git log --oneline` affiche l'historique avec une ligne par commit : hash court et message.

## Part 6 : Working with branches

1. `git branch`
2. `git branch feature-script`
3. `git switch feature-script` (ou `git checkout feature-script`)
4. `git switch -c dev` (ou `git checkout -b dev`)
5. `git switch feature-script`
6. `git branch` (la branche courante a une `*`) ou `git status` (`On branch feature-script`)

## Part 7 : Create a bash script on a branch

```bash
git branch                      # vérifier qu'on est sur feature-script
cat > install.sh <<'EOF'
#!/usr/bin/env bash
echo "Starting installation..."
sudo apt-get update
sudo apt-get install -y tree
echo "Installation complete!"
EOF
chmod +x install.sh
git add install.sh
git commit -m "Add install script"
git log --oneline
```

## Part 8 : Merge branches

1. `git switch main`
2. `ls` : `install.sh` n'est pas là. Il a été commité sur `feature-script`, et `main` ne contient pas encore ce commit.
3. `git merge feature-script`
4. `ls` : `install.sh` apparaît.
5. `git log --oneline` : le commit « Add install script » est maintenant dans l'historique de `main`. `main` n'avait pas bougé depuis la création de la branche, donc Git a fait un fast-forward : il a avancé le pointeur de `main` sans créer de commit de merge.
6. `git branch -d feature-script`

## Part 9 : Push to GitHub

Créer le dépôt sur github.com sans README (sinon l'historique distant diverge du local et le premier push est refusé).

```bash
git remote add origin git@github.com:Akasha53/my-first-repo.git
git push -u origin main
```

La page GitHub affiche `readme.txt`, `install.sh` et les 3 commits.

Avec `gh`, les deux étapes se font en une commande : `gh repo create my-first-repo --public --source=. --push`.

## Part 10 : Delete and clone

```bash
cd ..
rm -rf my-first-repo
git clone git@github.com:Akasha53/my-first-repo.git
cd my-first-repo && ls
```

## Part 11 : Full workflow practice

```bash
rm -rf my-first-repo
gh repo delete Akasha53/my-first-repo --yes   # ou via Settings > Delete this repository

mkdir bash-installer && cd bash-installer
git init -b main
# écrire README.md
git add README.md && git commit -m "Add README"
git switch -c feature-install
# copier install.sh
chmod +x install.sh
git add install.sh && git commit -m "Add install script"
git switch main
git merge feature-install
git branch -d feature-install
gh repo create bash-installer --public --source=. --remote=origin --push
```

Dans le dépôt publié, `install.sh` prend le paquet à installer en argument (`tree` par défaut) et fonctionne aussi sur macOS avec Homebrew.
