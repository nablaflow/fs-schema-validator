{
  description = "";

  inputs = {
    nixpkgs = { url = "github:NixOS/nixpkgs/nixpkgs-unstable"; };
    flake-utils = { url = "github:numtide/flake-utils"; };
    poetry2nix = { url = "github:nix-community/poetry2nix"; };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    {
      overlays.default = nixpkgs.lib.composeManyExtensions [
        poetry2nix.overlay
        (final: prev: {
          devEnv = prev.poetry2nix.mkPoetryEnv {
            python = prev.python310;
            projectDir = ./.;
            editablePackageSources = {
              "fs_schema_validator" = ./fs_schema_validator;
            };
          };
        })
      ];
    } // (flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ self.overlays.default ];
        };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.devEnv
            pkgs.poetry
          ];
        };

        formatter = pkgs.nixpkgs-fmt;
      }));
}
