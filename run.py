from flask_app.database_config import setup_app
from flask_app.views import app_blueprint

app = setup_app()

# Register the blueprint
app.register_blueprint(app_blueprint)

if __name__ == '__main__':
    print(app.url_map)
    app.run(debug=True)