from flask import Flask, Blueprint
from src import blueprints


def create_app(bls: list[Blueprint] = [blueprints.index_bp]) -> Flask:
    app = Flask(
        __name__,
        static_folder="src/static",
        template_folder="src/templates",
    )
    for bl in bls:
        app.register_blueprint(bl)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
