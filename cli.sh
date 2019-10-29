#!/usr/bin/env bash

set -e

function test() {
    pytest --cov=argser --no-cov-on-fail --cov-report html --cov-report term-missing
}

function docs() {
    make -C docs clean
    make -C docs html
}

$@
