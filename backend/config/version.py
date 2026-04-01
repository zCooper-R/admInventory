"""
Application version — single source of truth.

Follows Semantic Versioning 2.0.0  (https://semver.org/)

  MAJOR — breaking API or data-model changes
  MINOR — new backward-compatible functionality
  PATCH — backward-compatible bug fixes

How to release
--------------
1. Bump VERSION and RELEASE_DATE here.
2. Update CHANGELOG.md.
3. Commit: git commit -m "release: vX.Y.Z"
4. Tag:    git tag vX.Y.Z && git push origin vX.Y.Z

Author : Литвин Олег Олегович <qucooper@yandex.ru>
"""

VERSION = "0.1.0"
RELEASE_DATE = "2026-03-29"
APP_NAME = "admInventory"
