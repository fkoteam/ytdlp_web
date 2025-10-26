# Usa una imagen base de Python oficial
FROM python:3.13-slim-bullseye

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala ffmpeg, necesario para yt-dlp para extraer audio y post-procesamiento
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Copia el resto de los archivos de la aplicación
COPY app/ .

# Expone el puerto en el que se ejecutará la aplicación Flask
EXPOSE 8080

# Define el comando para ejecutar la aplicación cuando se inicie el contenedor
ENTRYPOINT ["/entrypoint.sh"]
