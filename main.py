from flask import Flask, Blueprint
from src import blueprints
from pathlib import Path
import tomllib


def create_app(bls: list[Blueprint] = [blueprints.index_bp]) -> Flask:
    app = Flask(
        __name__,
        static_folder=Path("src/static"),
        template_folder=Path("src/templates"),
    )
    app.config.from_file(Path("config.toml"), tomllib.load, text=False)
    for bl in bls:
        app.register_blueprint(bl)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
