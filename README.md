# picopili

### Purpose

* Expand [ricopili](https://github.com/Nealelab/ricopili) to support GWAS of family data, from sib-pairs to extended pedigrees

### Changelog

* Improve handling of impute2's output format with 3 probabilities (see [impprob_to_2dos](https://github.com/Nealelab/picopili/blob/dev/rp_bin/impprob_to_2dos))
* Avoid (rarely) losing SNPs when merging chunk results (see [dameta_cat](https://github.com/Nealelab/picopili/blob/dev/rp_bin/dameta_cat)) 

### Install alongside Ricopili

##### 1. The following assumes:

* You're working on the Broad cluster (though can probably be adapted)

* You've already installed [ricopili](https://github.com/Nealelab/ricopili).

* You have git configured with a github account.

##### 2. Download picopili from github

```
mkdir ~/github
cd ~/github
git clone https://github.com/Nealelab/picopili.git
git checkout dev
```

Note: the 'dev' branch is currently intended to be the stable picopili branch, with the 'master' branch reserved for pulling updates from new releases of ricopili.

##### 3. Create dotkits for ricopili and picopili

This will allow switching between ricopili and picopili as desired.

First, setup a folder for personal dotkits.

```
mkdir ~/.kits
cd ~/.kits
```

Next, create a dotkit for picopili.

```
echo "
#c personal
#d fork of ricopili for family data, loaded from github folder

dk_alter PATH $HOME/github/picopili/rp_bin
dk_alter PATH $HOME/github/picopili/rp_bin/pdfjam
" > picopili.dk
```

Also create a dotkit for ricopili (change the install location as needed)

```
echo "
#c personal
#d gwas pipeline

dk_alter PATH $HOME/rp_bin
dk_alter PATH $HOME/rp_bin/pdfjam
" > ricopili.dk
```

You should now have entries for ricopili and picopili in you list of available dotkits (`use -la`)

##### 4. Switch how ricopili loads

In `~/.my.bashrc` (or equivalent for your shell) remove the lines

```
PATH=/home/unix/<username>/rp_bin:$PATH
PATH=/home/unix/<username>/rp_bin/pdfjam:$PATH
```

(or similar, depending on where you've installed ricopili), and replace them with


and replace them with

```
use ricopili
```

##### 5. Logout and log back in.

Applies the changes in `~/.my.bashrc`.

### Using ricopili/picopili

Once the above install is done, analyses will still be done with ricopili by default. 

*  **To use picopili:** change `use ricopili` to `use picopili` in your `~/.my.bashrc` (or equivalent) and run

```
unuse ricopili
use picopili
```

* **To use ricopili:** change `use picopili` to `use ricopili` in your `~/.my.bashrc` (or equivalent) and run

```
unuse picopili
use ricopili
```

