### Testing

1. Test REST API
    ```
    curl http://localhost:5001/
    ```

2. Test socket connection
    ```
    import socketio

    sio = socketio.Client()

    @sio.on('connection_response')
    def on_connection(data):
        print('Connected:', data)  # Should print: {'status': 'connected'}

    sio.connect('http://localhost:5001')
    sio.wait()
    ```

3. Stop the server
    ```
    pkill -f "python3 app.py"
    ```