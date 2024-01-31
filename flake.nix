{
  description = "";

  inputs = {
    nixpkgs = {url = "github:NixOS/nixpkgs/nixpkgs-unstable";};
    flake-utils = {url = "github:numtide/flake-utils";};
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    poetry2nix,
    ...
  }: (flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs {inherit system;};

    poetry2nix_ = poetry2nix.lib.mkPoetry2Nix {inherit pkgs;};

    devEnv = poetry2nix_.mkPoetryEnv {
      projectDir = ./.;

      preferWheels = true;

      overrides = poetry2nix_.defaultPoetryOverrides.extend (self: super: {
        types-pillow = super.types-pillow.overridePythonAttrs (
          old: {
            buildInputs = (old.buildInputs or []) ++ [self.setuptools];
          }
        );

        svgelements = super.svgelements.overridePythonAttrs (
          old: {
            buildInputs = (old.buildInputs or []) ++ [self.setuptools];
          }
        );
      });
    };
  in {
    devShells.default = pkgs.mkShell {
      packages = [
        devEnv
        pkgs.poetry
        pkgs.just
      ];
    };

    formatter = pkgs.alejandra;
  }));
}
