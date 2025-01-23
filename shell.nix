{ pkgs ? import <nixpkgs> }:
pkgs.mkShell {
  buildInputs = with pkgs; [
    procps
    (my_python.withPackages (ps: with ps; [
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
    ]))
    nodejs
    nodePackages.serve
    rabbitmq-server
  ];
}
