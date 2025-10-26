<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Streaming Video o Salida de Consola</title>
    <style>
        #status-icon {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 10px;
        }
        #status-icon.red { background-color: red; }
        #status-icon.green { background-color: green; }
    </style>
</head>
<body>
    <h1>Ver Video en Streaming o Mostrar Salida de yt-dlp</h1>
    
    <?php
    function isProcessRunning($processName) {
        $output = shell_exec("pgrep -f \"$processName\"");
        return !empty($output);
    }

    $command = "python /var/www/html/web/backendytd.py";
    $isRunning = isProcessRunning($command);
    ?>

    <div>
        <span id="status-icon" class="<?= $isRunning ? 'green' : 'red' ?>"></span>
        <button onclick="toggleProcess()"><?= $isRunning ? 'Detener' : 'Iniciar' ?></button>
    </div>

    <form id="video-form">
        <label for="video-url">URL del Video:</label>
        <input type="text" id="video-url" placeholder="Introduce la URL">
        
        <label for="params">Parámetros yt-dlp:</label>
        <input type="text" id="params" placeholder='--concat-playlist always -o -' value="--concat-playlist always -o -">
        
        <button type="button" onclick="loadVideo()">Ejecutar</button>
    </form>

    <!-- Video player, solo se muestra si es streaming -->
    <video id="video-player" controls autoplay style="display: none;"></video>
    
    <!-- Caja de texto para mostrar salida de consola -->
    <div id="console-output" style="display: none; white-space: pre-wrap; border: 1px solid #ccc; padding: 10px;"></div>

    <script>
        function loadVideo() {
            const url = document.getElementById('video-url').value;
            const params = document.getElementById('params').value;
            
            // Aquí iría la lógica de video con yt-dlp
const videoPlayer = document.getElementById('video-player');
            const consoleOutput = document.getElementById('console-output');
            
            // Determina si se usa streaming o salida de texto
            if (params.includes("-o -")) {
                // Configura el reproductor de video y oculta la salida de texto
                videoPlayer.src = `http://zeronetproxy.duckdns.org:8080/web/stream?url=${encodeURIComponent(url)}&params=${encodeURIComponent(params)}`;
                videoPlayer.style.display = "block";
                consoleOutput.style.display = "none";
                videoPlayer.load();
            } else {
                // Si no es streaming, solicita la salida en texto
                fetch(`http://zeronetproxy.duckdns.org:8080/web/stream?url=${encodeURIComponent(url)}&params=${encodeURIComponent(params)}`)
                    .then(response => response.text())
                    .then(text => {
                        consoleOutput.textContent = text;
                        consoleOutput.style.display = "block";
                        videoPlayer.style.display = "none";
                    });
            }
        }

        function toggleProcess() {
            fetch('toggle_process.php')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'running') {
                        document.getElementById('status-icon').className = 'green';
                        document.querySelector('button').innerText = 'Detener';
                    } else {
                        document.getElementById('status-icon').className = 'red';
                        document.querySelector('button').innerText = 'Iniciar';
                    }
                })
                .catch(error => console.error('Error:', error));
        }
    </script>
</body>
</html>
