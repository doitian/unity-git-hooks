#!/usr/bin/env bats

PRE_COMMIT="$BATS_TEST_DIRNAME/scripts/pre-commit"

setup() {
  git init repo >&2
  cd repo
  git config user.email "bats@ci"
  git config user.name "bats"
  mkdir Assets
}

teardown() {
  cd ..
  rm -rf repo
}

@test "ensuring .meta is commit" {
  touch Assets/assets
  git add Assets/assets
  run "$PRE_COMMIT"
  echo "$output"
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "Error: Missing meta file." ]

  touch Assets/assets.meta
  git add Assets/assets.meta
  "$PRE_COMMIT"
}

@test "ignoring assets file which starts with dot" {
  touch Assets/.assets
  git add --force Assets/.assets
  "$PRE_COMMIT"
}

@test "renaming directory" {
  mkdir Assets/dir
  touch Assets/dir/.gitkeep
  touch Assets/dir.meta
  git add --force --all
  git commit -n -m 'add Assets/dir'
  mv Assets/dir Assets/dir-new
  git add --force --all
  run "$PRE_COMMIT"
  echo "$output"
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "Error: Redudant meta file." ]
}
