import logging
from flask import Flask, request, Response
from flask_cors import CORS
import subprocess
import os
import sys

app = Flask(__name__)

# Configura el logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

CORS(app)

# HTML para la interfaz web (anteriormente en yt_php.txt)
# Nota: La lógica de iniciar/detener el proceso del backend NO puede ser manejada
# de forma segura por la propia aplicación Flask desde el navegador.
# Esta sección simula el estado, pero la gestión real del servicio debe ser externa (e.g., systemd).
INDEX_HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Streaming Video o Salida de Consola</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        h1 { color: #0056b3; }
        form { background-color: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; font-weight: bold; }
        input[type="text"] { width: calc(100% - 22px); padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 4px; }
        button { background-color: #007bff; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background-color: #0056b3; }
        #status-container { margin-bottom: 20px; display: flex; align-items: center; }
        #status-icon {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 10px;
            border: 1px solid #ccc; /* Añadido para visibilidad */
        }
        #status-icon.red { background-color: red; }
        #status-icon.green { background-color: green; }
        video { width: 100%; max-width: 800px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        #console-output {
            background-color: #333;
            color: #0f0;
            padding: 15px;
            border-radius: 8px;
            overflow-x: auto;
            max-height: 400px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
    </style>
</head>
<body>
    <h1>Ver Video en Streaming o Mostrar Salida de yt-dlp</h1>
    
    <div id="status-container">
        <span id="status-icon" class="red"></span> <!-- Inicialmente en rojo, se actualizará con JS -->
        <button onclick="location.reload()">Refrescar Estado del Servidor</button>
        <span style="margin-left: 10px;">(El servidor debe iniciarse/detenerse externamente)</span>
    </div>

    <form id="video-form">
        <label for="video-url">URL del Video:</label>
        <input type="text" id="video-url" placeholder="Introduce la URL" value="https://www.youtube.com/watch?v=dQw4w9WgXcQ">
        
        <label for="params">Parámetros yt-dlp:</label>
        <input type="text" id="params" placeholder='--concat-playlist always -o -' value="--concat-playlist always -o -">
        
        <button type="button" onclick="loadContent()">Ejecutar</button>
    </form>

    <!-- Video player, solo se muestra si es streaming -->
    <video id="video-player" controls autoplay style="display: none;"></video>
    
    <!-- Caja de texto para mostrar salida de consola -->
    <div id="console-output" style="display: none; white-space: pre-wrap; border: 1px solid #ccc; padding: 10px;"></div>

    <script>
        // Función para verificar si el servidor Flask está ejecutándose
        async function checkServerStatus() {
            try {
                // Intentar acceder a una ruta simple, como la raíz
                const response = await fetch('/', { method: 'HEAD' });
                const statusIcon = document.getElementById('status-icon');
                if (response.ok) {
                    statusIcon.className = 'green';
                    console.log('Backend está funcionando.');
                } else {
                    statusIcon.className = 'red';
                    console.log('Backend NO está funcionando (HTTP Status:', response.status, ').');
                }
            } catch (error) {
                const statusIcon = document.getElementById('status-icon');
                statusIcon.className = 'red';
                console.log('Error al conectar con el backend:', error);
            }
        }

        // Llamar a la función al cargar la página para establecer el estado inicial
        document.addEventListener('DOMContentLoaded', checkServerStatus);

        function loadContent() {
            const url = document.getElementById('video-url').value;
            const params = document.getElementById('params').value;
            
            const videoPlayer = document.getElementById('video-player');
            const consoleOutput = document.getElementById('console-output');
            
            if (!url) {
                alert("Por favor, introduce una URL de vídeo.");
                return;
            }

            // Determina si se usa streaming o salida de texto
            if (params.includes("-o -")) {
                // Configura el reproductor de video y oculta la salida de texto
                // Usamos window.location.origin para asegurarnos de que la URL base es correcta
                videoPlayer.src = `${window.location.origin}/web/stream?url=${encodeURIComponent(url)}&params=${encodeURIComponent(params)}`;
                videoPlayer.style.display = "block";
                consoleOutput.style.display = "none";
                videoPlayer.load();
                consoleOutput.textContent = ''; // Limpiar salida anterior
            } else {
                // Si no es streaming, solicita la salida en texto
                fetch(`${window.location.origin}/web/stream?url=${encodeURIComponent(url)}&params=${encodeURIComponent(params)}`)
                    .then(response => {
                        if (!response.ok) {
                            return response.text().then(text => Promise.reject(new Error(text || response.statusText)));
                        }
                        return response.text();
                    })
                    .then(text => {
                        consoleOutput.innerHTML = text; // Usar innerHTML para <pre> tags
                        consoleOutput.style.display = "block";
                        videoPlayer.style.display = "none";
                        videoPlayer.src = ''; // Detener video anterior
                    })
                    .catch(error => {
                        console.error('Error al obtener la salida:', error);
                        consoleOutput.innerHTML = `<pre style="color: red;">Error: ${error.message}</pre>`;
                        consoleOutput.style.display = "block";
                        videoPlayer.style.display = "none";
                        videoPlayer.src = '';
                    });
            }
        }

        // La función toggleProcess original de PHP no es aplicable directamente aquí
        // La gestión del servicio Flask (iniciar/detener) debe hacerse externamente.
        // El botón "Refrescar Estado" ahora simplemente recarga la página para reevaluar el estado.
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Sirve la interfaz web principal."""
    app.logger.info("Sirviendo la página principal.")
    return Response(INDEX_HTML, mimetype='text/html')

@app.route('/web/remux')
def remux_stream():
    """
    Ruta para remuxear y streamear un video directamente (sin yt-dlp).
    Útil para URLs directas de video que FFmpeg pueda manejar.
    """
    video_url = request.args.get('url')
    if not video_url:
        app.logger.error("Solicitud /web/remux sin URL proporcionada.")
        return "Falta la URL del vídeo.", 400

    app.logger.info(f"Solicitud /web/remux para URL: {video_url}")

    command = [
        'ffmpeg',
        '-i', video_url,           # Entrada: URL del vídeo
        '-c', 'copy',              # Copiar sin transcodificación
        '-movflags', 'frag_keyframe+empty_moov', # Opciones para streaming MP4
        '-f', 'mp4',               # Salida en formato MP4
        'pipe:1'                   # Enviar salida por stdout
    ]

    def generate_remux():
        process = None
        try:
            process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            while True:
                chunk = process.stdout.read(8192) # Leer en chunks más grandes
                if not chunk:
                    break
                yield chunk
        except Exception as e:
            app.logger.error(f"Error durante el remuxing: {e}")
        finally:
            if process and process.poll() is None: # Si el proceso sigue corriendo
                process.terminate()
                app.logger.info("Proceso FFmpeg terminado.")

    return Response(generate_remux(), mimetype='video/mp4')


@app.route('/web/stream')
def stream_video_with_ytdlp():
    """
    Ruta principal para procesar videos con yt-dlp.
    Puede streamear o devolver salida de consola.
    """
    app.logger.info("Solicitud recibida en /web/stream")
    url = request.args.get('url')
    params = request.args.get('params', '').strip() # .strip() para limpiar espacios

    if not url:
        app.logger.error("URL no proporcionada en /web/stream.")
        return "URL no proporcionada", 400

    # Construye el comando base de yt-dlp
    yt_dlp_command = ["yt-dlp"]
    if params:
        yt_dlp_command.extend(params.split())
    yt_dlp_command.append(url)

    app.logger.debug(f"Comando yt-dlp a ejecutar: {' '.join(yt_dlp_command)}")

    # Si los parámetros contienen "-o -", se envía como flujo
    if "-o -" in params:
        app.logger.info(f"Iniciando transmisión de video en streaming para URL: {url} con parámetros: {params}")
        process = None
        try:
            process = subprocess.Popen(
                yt_dlp_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # Capturamos stderr para loguear errores
                bufsize=10**6
            )

            # Leer stderr en un hilo separado para evitar bloqueos
            def log_stderr(pipe):
                for line in iter(pipe.readline, b''):
                    app.logger.warning(f"yt-dlp STDERR: {line.decode().strip()}")
                pipe.close()

            import threading
            stderr_thread = threading.Thread(target=log_stderr, args=(process.stderr,))
            stderr_thread.daemon = True # El hilo terminará con el programa principal
            stderr_thread.start()

            def generate_stream():
                try:
                    while True:
                        data = process.stdout.read(8192)
                        if not data:
                            break
                        yield data
                except Exception as e:
                    app.logger.error(f"Error durante la transmisión del stream: {e}")
                finally:
                    if process.poll() is None: # Si el proceso sigue corriendo
                        process.terminate()
                        app.logger.info("Proceso yt-dlp de streaming terminado.")
                    # Esperar a que el hilo de stderr termine si es necesario
                    # stderr_thread.join() # Esto podría bloquear si el proceso es muy largo
        
            return Response(generate_stream(), content_type="video/mp4")

        except Exception as e:
            app.logger.error(f"Fallo al iniciar el proceso yt-dlp para streaming: {e}")
            return f"Error al iniciar el streaming: {e}", 500

    # Si no contiene "-o -", devuelve la salida completa en texto
    else:
        app.logger.info(f"Obteniendo salida de consola de yt-dlp para URL: {url} con parámetros: {params}")
        process = None
        try:
            process = subprocess.Popen(
                yt_dlp_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            output, error = process.communicate(timeout=300) # Añadir un timeout
            
            output_decoded = output.decode(errors='replace')
            error_decoded = error.decode(errors='replace')

            if process.returncode != 0:
                app.logger.error(f"yt-dlp terminó con código {process.returncode}. STDERR: {error_decoded}")
                return Response(f"<pre style='color: red;'>Error (código {process.returncode}):\n{error_decoded}\n\nSTDOUT:\n{output_decoded}</pre>", status=500)
            else:
                app.logger.info("yt-dlp finalizó correctamente. Devolviendo salida.")
                return f"<pre>{output_decoded}\n{error_decoded}</pre>"
        except subprocess.TimeoutExpired:
            if process:
                process.kill()
                output, error = process.communicate()
            app.logger.error(f"El comando yt-dlp excedió el tiempo límite (300s) para URL: {url}")
            return Response(f"<pre style='color: red;'>Error: El comando yt-dlp excedió el tiempo límite.</pre>", status=504)
        except Exception as e:
            app.logger.error(f"Error general al ejecutar yt-dlp en modo consola: {e}")
            return Response(f"<pre style='color: red;'>Error inesperado: {e}</pre>", status=500)
        finally:
            if process and process.poll() is None: # Si el proceso sigue corriendo (aunque se haya capturado el output)
                process.terminate()


if __name__ == "__main__":
    # Asegúrate de que yt-dlp está disponible
    try:
        subprocess.run(["yt-dlp", "--version"], check=True, capture_output=True)
        app.logger.info("yt-dlp detectado y accesible.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        app.logger.error("yt-dlp no encontrado o no ejecutable. Por favor, asegúrate de que está instalado y en el PATH.")
        app.logger.error("Instálalo con: sudo apt install yt-dlp o pip install yt-dlp")
        # sys.exit(1) # Considera salir si yt-dlp es esencial

    # Asegúrate de que ffmpeg está disponible
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        app.logger.info("FFmpeg detectado y accesible.")
    except (subprocess.CalledProcessError, FileNotFoundError):
        app.logger.error("FFmpeg no encontrado o no ejecutable. Por favor, asegúrate de que está instalado y en el PATH.")
        app.logger.error("Instálalo con: sudo apt install ffmpeg")
        # sys.exit(1) # Considera salir si ffmpeg es esencial

    from waitress import serve
    app.logger.info("Iniciando servidor Flask con Waitress en 0.0.0.0:8081")
    serve(app, host="0.0.0.0", port=8081)
