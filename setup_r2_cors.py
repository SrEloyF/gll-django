import boto3
from botocore.exceptions import ClientError

s3 = boto3.client(
    service_name= 's3',
    region_name= 'auto',
    endpoint_url="https://pub-c92815cc58c049aead5810a0c963d399.r2.dev",
    aws_access_key_id="5609f12472882f152594edadc81e35c0",
    aws_secret_access_key="34c4967bf69d66d5831c02eda55e454ae452070d3c4645271e1e1c99545774ac"
)

bucket_name = 'prueba-gll'
cors_configuration = {
    'CORSRules': [
        {
            'AllowedOrigins': ['http://127.0.0.1:8000', 'http://localhost:8000'],  # Agrega tu origen local; usa ['*'] para todo (menos seguro en prod)
            'AllowedMethods': ['GET', 'PUT', 'POST', 'HEAD', 'DELETE'],  # Incluye POST para presigned
            'AllowedHeaders': ['*'],  # O ['content-type', 'x-amz-*'] para más restricción
            'ExposeHeaders': ['ETag'],  # Opcional, para ver resultados
            'MaxAgeSeconds': 3000  # Cache del preflight (50 min)
        }
    ]
}

try:
    # Aplica la política
    response = s3.put_bucket_cors(
        Bucket=bucket_name,
        CORSConfiguration=cors_configuration
    )
    print("✅ CORS configurado exitosamente en el bucket '{}'".format(bucket_name))
    print("Respuesta:", response)

    # Verifica la configuración aplicada
    cors_info = s3.get_bucket_cors(Bucket=bucket_name)
    print("Configuración actual:", cors_info['CORSRules'])

except ClientError as e:
    print("❌ Error configurando CORS:", e)
    if e.response['Error']['Code'] == 'NoSuchBucket':
        print("El bucket no existe. Créalo en el dashboard de Cloudflare.")