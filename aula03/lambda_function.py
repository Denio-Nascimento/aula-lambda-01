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
    logger.info(f"Evento SNS recebido: {json.dumps(event)}")  # Logando o evento completo para depuração
    
    try:
        # Extraindo a mensagem do SNS, que contém o evento S3
        sns_message = event['Records'][0]['Sns']['Message']
        s3_event = json.loads(sns_message)  # Convertendo a string JSON de volta para um objeto
        
        # Agora, podemos tratar o evento S3 normalmente
        bucket_name = s3_event['Records'][0]['s3']['bucket']['name']
        object_key = s3_event['Records'][0]['s3']['object']['key']
        
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
