# Função Lambda Invocada via SNS

Este projeto descreve uma função Lambda que será invocada por um tópico SNS. A função processa o conteúdo de arquivos JSON de pedidos, que são enviados ao S3, e insere os dados no DynamoDB.

## Recursos Necessários

1. **Amazon S3**: Bucket onde os arquivos JSON de pedidos serão armazenados.
2. **Amazon SNS**: Tópico SNS que enviará notificações para a função Lambda.
3. **AWS Lambda**: Função que processará os pedidos e os inserirá no DynamoDB.
4. **Amazon DynamoDB**: Tabela onde os pedidos serão armazenados.

### Permissões Necessárias

A função Lambda precisará das seguintes permissões:

1. **SNS**: Permissão para invocar a função Lambda.
2. **DynamoDB**: Permissão para inserir itens na tabela.
3. **S3**: Permissão para ler o conteúdo do bucket.

### Política de Permissão para o SNS Invocar a Lambda

Abaixo está um exemplo de política de recurso para permitir que o SNS invoque a função Lambda:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sns.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "arn:aws:lambda:us-east-1:0123456789ABC:function:NomeDaSuaLambda",
      "Condition": {
        "ArnLike": {
          "aws:SourceArn": "arn:aws:sns:us-east-1:0123456789ABC:pedidos-json"
        }
      }
    }
  ]
}
```

### Código da Lambda

Abaixo está o código da função Lambda:

```
import json
import boto3
import logging

# Inicializando os clientes do DynamoDB e S3
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table = dynamodb.Table('PedidosTable')  # Substituir pelo nome da tabela DynamoDB

# Setup do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info(f"Evento recebido: {json.dumps(event)}")  # Logando o evento completo para depuração
    
    try:
        # Extraindo informações do evento S3
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']
        object_key = s3_event['object']['key']
        
        # Fazendo download do arquivo JSON do S3
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        file_content = response['Body'].read().decode('utf-8')
        pedidos = json.loads(file_content)
        
        # Verificando se é um único pedido ou uma lista de pedidos
        if isinstance(pedidos, list):
            for pedido in pedidos:
                inserir_pedido_dynamodb(pedido)
        else:
            inserir_pedido_dynamodb(pedidos)
        
        return {
            'statusCode': 200,
            'body': json.dumps(f"Arquivo {object_key} processado com sucesso!")
        }
    
    except Exception as e:
        logger.error(f"Erro ao processar o arquivo do S3: {e}")
        raise e

def inserir_pedido_dynamodb(pedido):
    try:
        # Inserindo o pedido no DynamoDB
        table.put_item(
            Item={
                'orderId': str(pedido['orderId']),
                'status': pedido['status'],
                'customerName': pedido['customerName'],
                'customerEmail': pedido['customerEmail'],
                'totalAmount': str(pedido['totalAmount']),
                'orderDate': pedido['orderDate']
            }
        )
        logger.info(f"Pedido {pedido['orderId']} com status {pedido['status']} inserido no DynamoDB")
    
    except Exception as e:
        logger.error(f"Erro ao inserir o pedido {pedido['orderId']} no DynamoDB: {e}")
        raise e
```

### Configuração do S3 Notification para Publicar no SNS

- No bucket S3, configure uma notificação para enviar eventos ao tópico SNS assim que um arquivo JSON de pedidos for carregado.
- Certifique-se de que o bucket S3 e o SNS têm as permissões corretas.
