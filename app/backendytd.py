import logging
from flask import Flask, request, Response
from flask_cors import CORS
import subprocess

app = Flask(__name__)

# Configura el logging para escribir en logs.txt
#logging.basicConfig(filename='logs.txt', level=logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

CORS(app)


@app.route('/web/remux')
def stream():
    video_url = request.args.get('url')
    if not video_url:
        return "Falta la URL del vídeo.", 400

    # Configura FFmpeg para remuxear y enviar en tiempo real
    command = [
        'ffmpeg',
        '-i', video_url,           # Entrada: URL del vídeo
        '-c', 'copy',              # Copiar sin transcodificación
        '-movflags', 'frag_keyframe+empty_moov', # Opciones para streaming MP4
        '-f', 'mp4',               # Salida en formato MP4
        'pipe:1'                   # Enviar salida por stdout
    ]

    def generate():
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while True:
                chunk = process.stdout.read(1024)
                if not chunk:
                    break
                yield chunk
        finally:
            process.terminate()

    return Response(generate(), mimetype='video/mp4')



@app.route('/web/stream')
def stream_video():
    app.logger.info("Solicitud recibida en /stream")  # Log inicial
    url = request.args.get('url')
    params = request.args.get('params', '-o -')
    
#    if not url:
#        app.logger.error("URL no proporcionada.")
#        return "URL no proporcionada", 400

    # Si los parámetros contienen "-o -", se envía como flujo
    if "-o -" in params:
        process = subprocess.Popen(
            ["yt-dlp"] + params.split() + [url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=10**6
        )

        def generate():
            try:
                while True:
                    data = process.stdout.read(8192)
                    if not data:
                        break
                    yield data
            except Exception as e:
                app.logger.error(f"Error en el stream: {e}")
            finally:
                process.terminate()

        app.logger.info("Iniciando transmisión de video en streaming")
        return Response(generate(), content_type="video/mp4")
    
    # Si no contiene "-o -", devuelve la salida completa en texto
    else:
        process = subprocess.Popen(
            ["yt-dlp"] + params.split() ,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        output, error = process.communicate()
        if error:
            app.logger.error(f"Error de yt-dlp: {error.decode()}")
        return f"<pre>{output.decode()}\n{error.decode()}</pre>"

#if __name__ == '__main__':
#    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)
