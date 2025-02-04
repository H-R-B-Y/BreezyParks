from app import app, socketio

# if __name__ == "__main__":
# 	socketio.run(app)

if __name__ == "__main__":
	app.run(host="0.0.0.0",port="5000",debug=True, use_reloader=False)