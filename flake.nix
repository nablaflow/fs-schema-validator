{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    systems.url = "github:nix-systems/default-linux";

    flake-utils = {
      url = "github:numtide/flake-utils";
      inputs.systems.follows = "systems";
    };

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";

      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        nixpkgs.follows = "nixpkgs";
      };
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";

      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    uv2nix,
    pyproject-nix,
    pyproject-build-systems,
    ...
  } @ inputs: (flake-utils.lib.eachDefaultSystem (system: let
    pkgs = import nixpkgs {
      inherit system;
    };

    workspace = uv2nix.lib.workspace.loadWorkspace {workspaceRoot = ./.;};

    overlay = workspace.mkPyprojectOverlay {
      sourcePreference = "wheel";
    };

    pyprojectOverrides = final: prev: {
      pycairo = prev.pycairo.overrideAttrs (old: {
        nativeBuildInputs =
          (old.nativeBuildInputs or [])
          ++ (with prev; [meson-python packaging pyproject-metadata])
          ++ (with pkgs; [meson ninja pkg-config]);

        buildInputs = (old.buildInputs or [])
          ++ (with pkgs; [cairo]);
      });
    };

    pythonSet =
      (pkgs.callPackage pyproject-nix.build.packages {
        python = pkgs.python312;
      }).overrideScope
      (
        pkgs.lib.composeManyExtensions [
          pyproject-build-systems.overlays.default
          overlay
          pyprojectOverrides
        ]
      );

    pythonEnv = pythonSet.mkVirtualEnv "env" workspace.deps.all;

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
      env = {
        UV_NO_SYNC = "1";
        UV_PYTHON = pythonSet.python.interpreter;
        UV_PYTHON_DOWNLOADS = "never";
      };

      shellHook = ''
        unset PYTHONPATH
      '';

      packages = with pkgs; [
        just
        uv
        pythonEnv
      ];
    };

    checks = {
      lint = pkgs.stdenvNoCC.mkDerivation {
        name = "lint";

        inherit src;

        nativeBuildInputs = [
          pythonEnv
        ];

        dontConfigure = true;
        dontFixup = true;
        dontInstall = true;

        buildPhase = ''
          ruff format --diff --check .
          ruff check .

          touch $out
        '';
      };

      deptry = pkgs.stdenvNoCC.mkDerivation {
        name = "deptry";

        inherit src;

        nativeBuildInputs = [
          pythonEnv
        ];

        dontConfigure = true;
        dontFixup = true;
        dontInstall = true;

        buildPhase = ''
          deptry .

          touch $out
        '';
      };

      typecheck = pkgs.stdenvNoCC.mkDerivation {
        name = "typecheck";

        inherit src;

        nativeBuildInputs = [
          pythonEnv
        ];

        dontConfigure = true;
        dontFixup = true;
        dontInstall = true;

        buildPhase = ''
          mypy .

          touch $out
        '';
      };

      test = pkgs.stdenvNoCC.mkDerivation {
        name = "test";

        inherit src;

        nativeBuildInputs = [
          pythonEnv
        ];

        dontConfigure = true;
        dontFixup = true;
        dontInstall = true;

        buildPhase = ''
          pytest

          touch $out
        '';
      };
    };

    formatter = pkgs.alejandra;
  }));
}
