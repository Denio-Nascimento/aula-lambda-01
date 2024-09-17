import json
import boto3
import logging
from decimal import Decimal

# Inicializando os clientes do DynamoDB, S3 e SQS
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
sqs = boto3.client('sqs')
table = dynamodb.Table('PedidosTable')  # Substituir pelo nome da tabela DynamoDB

# Setup do logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Lista de status permitidos
STATUS_PERMITIDOS = ['Pendente', 'Concluído', 'Cancelado']

# URL da fila SQS para pedidos inválidos (substituir pela URL da sua fila)
INVALID_ORDERS_SQS_URL = 'https://sqs.us-east-1.amazonaws.com/ID_DA_CONTA/NOME_DA_FILA'

def lambda_handler(event, context):
    logger.info(f"Evento recebido: {json.dumps(event)}")  # Logando o evento completo para depuração
    
    try:
        # Extraindo informações do evento S3
        s3_event = event['Records'][0]['s3']
        bucket_name = s3_event['bucket']['name']
        object_key = s3_event['object']['key']
        
        # Baixar o arquivo JSON do S3
        json_content = baixar_arquivo_s3(bucket_name, object_key)
        
        # Processar o arquivo JSON
        total_pedidos = processar_arquivo(json_content)
        
        logger.info(f"Total de {total_pedidos} pedidos processados do arquivo {object_key}.")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f"Arquivo {object_key} processado com sucesso! Total de pedidos: {total_pedidos}")
        }
    
    except Exception as e:
        logger.error(f"Erro ao processar o arquivo do S3: {e}")
        raise e

def baixar_arquivo_s3(bucket_name, object_key):
    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        return response['Body'].read().decode('utf-8')
    except s3.exceptions.NoSuchKey as e:
        logger.error(f"O arquivo {object_key} não foi encontrado no bucket {bucket_name}. Erro: {e}")
        raise e
    except Exception as e:
        logger.error(f"Erro ao baixar o arquivo do S3: {e}")
        raise e

def processar_arquivo(json_content):
    try:
        pedidos = json.loads(json_content)
        total_pedidos = 0
        
        # Verificar se é um único pedido ou uma lista de pedidos
        if isinstance(pedidos, list):
            total_pedidos = len(pedidos)
            for pedido in pedidos:
                try:
                    validar_pedido(pedido)
                    inserir_pedido_dynamodb(pedido)
                except ValueError as ve:
                    logger.error(f"Pedido inválido encontrado: {pedido}. Erro: {ve}")
                    enviar_para_sqs(pedido)
        else:
            try:
                validar_pedido(pedidos)
                inserir_pedido_dynamodb(pedidos)
                total_pedidos = 1
            except ValueError as ve:
                logger.error(f"Pedido inválido encontrado: {pedidos}. Erro: {ve}")
                enviar_para_sqs(pedidos)
        
        return total_pedidos

    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar o arquivo JSON: {e}")
        raise e
    except Exception as e:
        logger.error(f"Erro ao processar o arquivo: {e}")
        raise e

def validar_pedido(pedido):
    campos_obrigatorios = ['orderId', 'status', 'customerName', 'customerEmail', 'totalAmount', 'orderDate']
    for campo in campos_obrigatorios:
        if campo not in pedido:
            raise ValueError(f"O campo {campo} está faltando no pedido {pedido.get('orderId', 'desconhecido')}")
    
    # Validação do status do pedido
    if pedido['status'] not in STATUS_PERMITIDOS:
        raise ValueError(f"Status inválido {pedido['status']} no pedido {pedido['orderId']}. Status permitidos: {STATUS_PERMITIDOS}")

def inserir_pedido_dynamodb(pedido):
    try:
        # Inserindo o pedido no DynamoDB com o valor total usando Decimal
        table.put_item(
            Item={
                'orderId': str(pedido['orderId']),
                'status': pedido['status'],
                'customerName': pedido['customerName'],
                'customerEmail': pedido['customerEmail'],
                'totalAmount': Decimal(str(pedido['totalAmount'])),  # Usando Decimal para valores monetários
                'orderDate': pedido['orderDate']
            }
        )
        logger.info(f"Pedido {pedido['orderId']} com status {pedido['status']} inserido no DynamoDB")
    
    except Exception as e:
        logger.error(f"Erro ao inserir o pedido {pedido['orderId']} no DynamoDB: {e}")
        raise e

def enviar_para_sqs(pedido):
    try:
        response = sqs.send_message(
            QueueUrl=INVALID_ORDERS_SQS_URL,
            MessageBody=json.dumps(pedido)
        )
        logger.info(f"Pedido inválido {pedido['orderId']} enviado para a fila SQS.")
    except Exception as e:
        logger.error(f"Erro ao enviar o pedido {pedido['orderId']} para a fila SQS: {e}")
        raise e
