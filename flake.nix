{
  inputs = {
    nixpkgs.url = github:NixOS/nixpkgs/5a1fae64da2be3d09a8f289c6257146997827d1d;
    flake-utils.url = github:numtide/flake-utils;

    poetry2nix = {
      url = github:nix-community/poetry2nix;
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    ...
  } @ inputs: (flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs {
      inherit system;

      overlays = [
        (final: prev: {
          poetry2nix = inputs.poetry2nix.lib.mkPoetry2Nix {pkgs = prev;};
        })
      ];
    };

    poetryEnv = pkgs.poetry2nix.mkPoetryEnv {
      projectDir = ./.;

      preferWheels = true;

      overrides = pkgs.poetry2nix.defaultPoetryOverrides.extend (self: super: {
        reportlab = super.reportlab.overridePythonAttrs (old: {
          postPatch = "";
        });
      });
    };

    src = pkgs.lib.fileset.toSource {
      root = ./.;

      fileset = pkgs.lib.fileset.unions [
        ./pyproject.toml
        (pkgs.lib.fileset.fileFilter (file: file.hasExt "py") ./fs_schema_validator)
        (pkgs.lib.fileset.fileFilter (file: file.hasExt "py") ./tests)
        ./tests/fixtures
      ];
    };
  in {
    devShells.default = pkgs.mkShell {
      packages = [
        poetryEnv
        pkgs.poetry
        pkgs.just
      ];
    };

    checks = {
      lint = pkgs.runCommand "lint" {} ''
        cp -r ${src}/* .

        ${poetryEnv}/bin/ruff format --diff --check .
        ${poetryEnv}/bin/ruff check .

        touch $out
      '';

      deptry = pkgs.runCommand "deptry" {} ''
        cp -r ${src}/* .

        ${poetryEnv}/bin/deptry .

        touch $out
      '';

      typecheck = pkgs.runCommand "typecheck" {} ''
        cp -r ${src}/* .

        ${poetryEnv}/bin/mypy .

        touch $out
      '';

      test = pkgs.runCommand "test" {} ''
        cp -r ${src}/* .

        ${poetryEnv}/bin/pytest

        touch $out
      '';
    };

    formatter = pkgs.alejandra;
  }));
}
