{
  description = "Graviola LinkML generator — dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = [
            pkgs.python311
            pkgs.uv
            pkgs.ruff
          ];

          shellHook = ''
            echo "graviola-linkml-generator dev shell"
            echo "Python: $(python3 --version)"
            echo "uv:     $(uv --version)"
            uv sync --frozen 2>/dev/null || uv sync
            echo ""
            echo "Commands:"
            echo "  uv run pytest -v                     — run tests"
            echo "  uv run graviola-linkml <schema.yaml> — generate schema"
          '';
        };
      });
}
