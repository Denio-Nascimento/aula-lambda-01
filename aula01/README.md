# README.md

## Descrição do Projeto

Esta Lambda Function é acionada por eventos S3 para registrar o nome do arquivo, bucket, `versionId`, e o timestamp no DynamoDB. Além disso, ela envia uma notificação SNS formatada contendo os detalhes do evento em um formato de texto legível.

## Recursos Necessários

Para implementar essa solução, você precisará dos seguintes recursos na AWS:

### 1. Lambda Function

- **Nome**: `S3EventProcessorLambda`
- **Runtime**: Python 3.x
- **Handler**: `lambda_function.lambda_handler`
- **Código-fonte**:

***

```python
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
```

### 2. S3 Bucket

- **Nome**: `lab-s3notification-01123` (ou nome que preferir)
- **Configuração de Notificação**: 
  - Configurar evento S3 para `ObjectCreated:Put` que dispara a Lambda `S3EventProcessorLambda`.

### 3. DynamoDB

- **Tabela**: `RegistroArquivosTable`
- **Chave Primária**: `object_key` (Partition Key)
- **Chave de Ordenação**: `version_id` (Sort Key)
- **Outros Atributos**: `bucketName`, `timestamp`

### 4. SNS Topic

- **Nome**: `Lambda_notification`
- **ARN**: `arn:aws:sns:us-east-1:ACCOUNT_ID:Lambda_notification` (ou seu próprio ARN)
- **Permitir que a Lambda publique mensagens neste tópico**

## Permissões Necessárias

### Lambda Execution Role:

A role associada à Lambda precisa das seguintes permissões:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "sns:Publish"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:ACCOUNT_ID:table/RegistroArquivosTable",
        "arn:aws:sns:us-east-1:ACCOUNT_ID:Lambda_notification"
      ]
    }
  ]
}
```

## Deploy

1. Crie a **Lambda Function** com o código fornecido.
2. Configure o **S3 Bucket** para enviar eventos para a Lambda quando novos arquivos forem colocados.
3. Crie a **tabela DynamoDB** com as chaves primárias e de ordenação corretas.
4. Crie o **SNS Topic** e configure a Lambda para publicar nesse tópico.
5. Aplique as permissões necessárias para que a Lambda possa interagir com o DynamoDB e SNS.

