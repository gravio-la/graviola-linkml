{
  description = "Reproducible Nix flake for Graviola LinkML generation";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    pyproject-nix.url = "github:pyproject-nix/pyproject.nix";
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.uv2nix.follows = "uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      pyproject-nix,
      uv2nix,
      pyproject-build-systems,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        lib = pkgs.lib;

        workspace = uv2nix.lib.workspace.loadWorkspace {
          workspaceRoot = ./.;
        };

        python = lib.head (
          pyproject-nix.lib.util.filterPythonInterpreters {
            inherit (workspace) requires-python;
            inherit (pkgs) pythonInterpreters;
          }
        );

        pythonBase = pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        };

        overlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };

        pyprojectOverrides = final: prev: {
          pytest-logging = prev.pytest-logging.overrideAttrs (old: {
            nativeBuildInputs =
              (old.nativeBuildInputs or [ ])
              ++ final.resolveBuildSystem {
                setuptools = [ ];
              };
          });

          cfgraph = prev.cfgraph.overrideAttrs (old: {
            nativeBuildInputs =
              (old.nativeBuildInputs or [ ])
              ++ final.resolveBuildSystem {
                setuptools = [ ];
              };
          });

          antlr4-python3-runtime = prev.antlr4-python3-runtime.overrideAttrs (old: {
            nativeBuildInputs =
              (old.nativeBuildInputs or [ ])
              ++ final.resolveBuildSystem {
                setuptools = [ ];
              };
          });
        };

        pythonSet = pythonBase.overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.wheel
            overlay
            pyprojectOverrides
          ]
        );

        venv = pythonSet.mkVirtualEnv "graviola-linkml-env" {
          graviola-linkml = [ ];
        };
        inherit (pkgs.callPackage pyproject-nix.build.util { }) mkApplication;

        graviola-linkml = mkApplication {
          inherit venv;
          package = pythonSet.graviola-linkml;
        };

        generate = pkgs.writeShellApplication {
          name = "generate";
          runtimeInputs = [ graviola-linkml ];
          text = ''
            exec graviola-linkml generate "$@"
          '';
        };

        side-schema = pkgs.writeShellApplication {
          name = "side-schema";
          runtimeInputs = [ graviola-linkml ];
          text = ''
            exec graviola-linkml side-schema "$@"
          '';
        };
      in
      {
        packages = {
          default = graviola-linkml;
          graviola-linkml = graviola-linkml;
          generate = generate;
          side-schema = side-schema;
        };

        apps = {
          default = {
            type = "app";
            program = "${graviola-linkml}/bin/graviola-linkml";
          };

          generate = {
            type = "app";
            program = "${generate}/bin/generate";
          };

          side-schema = {
            type = "app";
            program = "${side-schema}/bin/side-schema";
          };
        };

        devShells.default = pkgs.mkShell {
          packages = [
            venv
            pkgs.uv
            pkgs.ruff
          ];

          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = python.interpreter;
            UV_PYTHON_DOWNLOADS = "never";
          };
        };
      }
    );
}
