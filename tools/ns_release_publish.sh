#!/usr/bin/env sh
set -eu
VERSION="${1:-}"
CONFIRM="${2:-}"
if [ -z "$VERSION" ]; then
  printf "%s\n" "ERROR: missing version argument. Example: ./ns release-publish 0.3.21 publish-v0.3.21"
  exit 2
fi
case "$VERSION" in
  v*) TAG="$VERSION"; PLAIN_VERSION="${VERSION#v}" ;;
  *) TAG="v$VERSION"; PLAIN_VERSION="$VERSION" ;;
esac
printf "\n\n\n"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "%s\n" "-------------------------------------------------------------------------"
printf "\n\n\n"
printf "NS RELEASE PUBLISH CYCLE %s\n\n" "$TAG"
printf "\n### SAFETY ###\n"
printf "Safety: publishing requires exact confirmation token: publish-%s\n" "$TAG"
if [ "$CONFIRM" != "publish-$TAG" ]; then
  printf "%s\n" "ERROR: refusing release publish without exact confirmation token."
  printf "Run: ./ns release-publish %s publish-%s\n" "$PLAIN_VERSION" "$TAG"
  printf "\n### RESULT: FAIL ###\n"
  exit 2
fi
printf "%s\n" "Publishing implementation is intentionally deferred to the next hardened slice."
printf "\n### RESULT: FAIL ###\n"
exit 1
