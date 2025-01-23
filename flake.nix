{
  description = "Development Environment for Arbitre";
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-23.11";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }: 
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ (import ./overlay.nix) ];
        };
        
        pythonEnv = pkgs.my_python.withPackages (ps: with ps; [
          celery
          channels
          channels-redis
          coverage
          daphne
          django
          django-celery-beat
          django-cors-headers
          django-environ
          django-extensions
          django-types
          django-stubs-ext
          djangorestframework
          djangorestframework-api-key
          djangorestframework-simplejwt
          drf-yasg
          mozilla-django-oidc
          packaging
          psycopg2
          pyjwt
          pylama
          python-keycloak
          pyyaml
          redis
          requests
        ]);
      in
      {
        packages.pythonEnv = pythonEnv;
        
        devShells.default = pkgs.mkShell {
          buildInputs = [ pythonEnv pkgs.nodejs pkgs.nodePackages.serve pkgs.rabbitmq-server ];
        };
      }
    ) // {
      nixosModules.default = { config, lib, pkgs, ... }: {
        imports = [];
        nixpkgs.overlays = [ (import ./overlay.nix) ];
        # You could even move your service definitions here
      };
    };
}
