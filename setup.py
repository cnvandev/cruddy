from cruddy import Cruddy

if __name__ == "__main__":
    cruddy = Cruddy()
    app = cruddy.build_app()
    app.run(debug=True)