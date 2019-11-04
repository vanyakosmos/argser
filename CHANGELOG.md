# Changelog

Versions follow [Semantic Versioning](https://semver.org) (`<major>.<minor>.<patch>`).

**But**. Currently project is in alpha stage (`0.0.*`) and any changes can potentially break existing code.


## Unpublished

- read factory functions from Args class 


## 0.0.12

### Features

- build parser based on function arguments
- build parser with sub-commands using multiple functions
- add constructor parameter for options


## 0.0.11

### Breaking changes

- rename classes: `Arg -> Opt`, `PosArg -> Arg`

### Features

- make argument holders classes reusable

### Bug Fixes

- help message colorization
- nargs and type defaults


## 0.0.10

### Bug Fixes

- fix shortcuts generation
