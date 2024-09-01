# Invenio integration tests & oarepo builder

This repository contains integration tests 
for Invenio and oarepo builder.

## What it does

1. installs the latest version of invenio-app-rdm and extracts dependencies both for production and test builds
2. install plain RDM application
   1. via invenio-cli
   2. builds the invenio RDM
   3. installs all the required services
   4. creates a user, roles, permissions, ...
   5. runs the ui tests
3. inspects the content of `invenio-forks.yaml`, makes intersection with invenio-app-rdm requirements and creates a list of forked packages
4. for each fork, applies features from the `invenio-forks.yaml`, runs the tests and pushes to git as `oarepo-x.y.z` branch
5. creates an oarepo package with collected dependencies and forks
6. creates a simple repository out of the oarepo package
   1. runs pytests on it
   2. runs REST tests on it
   3. runs UI tests on it
7. pushes the oarepo package and let it build the distribution

## Forks and features

oarepo package might contain forked version of official invenio packages. 
The forks are descibed in `invenio-forks.yaml` file. 

To have a better visibility of the changes, the forks are divided into features.
Description of a fork/features:

```yaml
packages:
  - name: invenio-app-rdm
    oarepo: 12
    features:
      - name: removed-rdm-entrypoints
        base: v12.0.0
        invenio-version: "<12.0.5"
      - name: removed-rdm-entrypoints-12.0.5
        base: v12.0.5
        invenio-version: ">=12.0.5"
```

In the listing, package might occur multiple times, for each major version of oarepo/RDM.

The `features` are a list of changes that are applied to the forked package. It contains:
 
- `name` - name of the feature. The branch containing the feature must be named `oarepo-feature-<name>`
- `base` - the branch on which `oarepo-feature-<name>` is based on. All commits between the `baase` and `oarepo-feature-<name>` are applied to the forked package.
- `invenio-version` - the version of the package for which the feature is applied.

## Problems when running the build

### CONFLICT (content): Merge conflict in ...

When cherry-picking the changes from feature branches to the fork branch, there might be merge conflicts due to the changes made between the feature base and current version of the forked package. If you encounter them, look for the following block:

```
HEAD is now at f4928a14 release: v12.0.0
Previous HEAD position was f4928a14 release: v12.0.0

Switched to branch 'oarepo-12.0.5-temporary'             <-- this

git rev-list oarepo-feature-removed-rdm-entrypoints ^v12.0.0
5220bdec4572bce73c35c7d993d27f9b79fd1146

git cherry-pick --allow-empty --allow-empty-message
   oarepo-feature-removed-rdm-entrypoints ^v12.0.0       <-- this
```

Locally, perform the same steps:

```bash
gh repo clone invenio-app-rdm
cd invenio-app-rdm
gh repo sync
git fetch --all

# the number is from oarepo-12.0.5-temporary branch, not v12.0.0
git checkout v12.0.5    

# create a new feature branch starting here
git switch -c oarepo-feature-removed-rdm-entrypoints-from-v12.0.5

# do the cherry pick manually
git cherry-pick --allow-empty --allow-empty-message oarepo-feature-removed-rdm-entrypoints ^v12.0.0

git push oarepo-feature-removed-rdm-entrypoints-from-v12.0.5
```

Then add the fork to the `invenio-forks.yaml` file and run the build again.