import json
import boto3
import logging

# Inicializando o cliente DynamoDB e SNS
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('RegistroArquivosTable')  # Substituir pelo nome da sua tabela DynamoDB
sns = boto3.client('sns')
sns_topic_arn = 'arn:aws:sns:us-east-1:my_account:Lambda_notification'  # Substituir pelo ARN do seu tópico SNS

# Setup de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info(f"Evento recebido: {json.dumps(event)}")  # Logando o evento completo para depuração
    
    try:
        # Extraindo informações do evento S3
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']
        object_key = s3_event['object']['key']
        version_id = s3_event['object'].get('versionId', 'N/A')  # Captura o versionId, se existir
        
        # Extraindo o timestamp do evento
        event_time = event['Records'][0]['eventTime']
        
        # Salvando no DynamoDB usando os nomes corretos das chaves
        table.put_item(
            Item={
                'object_key': object_key,  # Partition Key (ajustada para object_key)
                'version_id': version_id,  # Sort Key (ajustada para version_id)
                'bucketName': bucket_name,
                'timestamp': event_time
            }
        )
        logger.info(f"Registrado arquivo {object_key} com versionId {version_id} do bucket {bucket_name} no DynamoDB com timestamp {event_time}")
        
        # Formatando uma mensagem legível para o SNS
        sns_message = (
            f"Novo arquivo registrado no S3:\n\n"
            f"Bucket: {bucket_name}\n"
            f"Objeto: {object_key}\n"
            f"VersionId: {version_id}\n"
            f"Timestamp do evento: {event_time}\n"
        )
        
        # Enviando a mensagem formatada para o SNS
        sns.publish(
            TopicArn=sns_topic_arn,
            Message=sns_message,  # Mensagem legível
            Subject=f"Arquivo {object_key} registrado",
            MessageStructure='string'
        )
        logger.info(f"Notificação SNS enviada para o tópico: {sns_topic_arn}")
    
    except KeyError as e:
        logger.error(f"Erro: {e}")
        raise e
    except Exception as e:
        logger.error(f"Erro ao registrar o arquivo no DynamoDB ou enviar SNS: {e}")
        raise e

    return {
        'statusCode': 200,
        'body': json.dumps(f"Arquivo {object_key} registrado e notificação enviada com sucesso!")
    }
