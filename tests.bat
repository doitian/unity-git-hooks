#!/usr/bin/env bats

PRE_COMMIT="$BATS_TEST_DIRNAME/scripts/pre-commit"

setup() {
  git init repo >&2
  cd repo
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
  [ "$status" -eq 1 ]
  [ "${lines[0]}" = "Error: Missing meta file." ]

  touch Assets/assets.meta
  git add Assets/assets.meta
  run "$PRE_COMMIT"
  [ "$status" -eq 0 ]
}

@test "ignoring assets file which starts with dot" {
  touch Assets/.assets
  git add --force Assets/.assets
  run "$PRE_COMMIT"
  [ "$status" -eq 0 ]
}
