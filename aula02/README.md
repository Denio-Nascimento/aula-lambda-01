# Projeto AWS Lambda para Processar Pedidos de Arquivo JSON no S3

## Descrição do Projeto
Este projeto consiste em uma função AWS Lambda que é acionada por notificações do S3 quando um arquivo JSON contendo pedidos é carregado. A função faz o seguinte:

1. Baixa o arquivo JSON do bucket S3.
2. Processa os pedidos no arquivo e insere os dados na tabela DynamoDB.
3. Se houver erros durante o processamento, os erros serão registrados no CloudWatch Logs.

## Recursos Necessários

### 1. Bucket S3

Um bucket S3 será usado para armazenar os arquivos JSON de pedidos. Quando um novo arquivo for enviado, uma notificação S3 será acionada para invocar a função Lambda.

- **Nome do bucket**: Defina o nome do bucket S3 que será utilizado.
- **Notificação S3**: Configure uma notificação S3 para invocar a função Lambda sempre que um arquivo JSON for carregado.

Exemplo de política S3:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::NOME_DO_BUCKET/*"
    }
  ]
}
```

### 2. Tabela DynamoDB

A tabela DynamoDB será usada para armazenar os pedidos processados.

- **Nome da tabela**: `PedidosTable`
- **Chave de Partição**: `orderId` (String)
- **Chave de Ordenação**: `status` (String)

Exemplo de esquema da tabela:

| Atributo       | Tipo   | Chave         |
|----------------|--------|---------------|
| orderId        | String | Partition Key |
| status         | String | Sort Key      |
| customerName   | String |               |
| customerEmail  | String |               |
| totalAmount    | Number |               |
| orderDate      | String |               |

### 3. Função Lambda

A função Lambda faz o seguinte:

- **Recebe a notificação S3** quando um novo arquivo é carregado.
- **Baixa o arquivo JSON do S3** e processa os pedidos.
- **Insere os pedidos na tabela DynamoDB**.

### Permissões Necessárias

A função Lambda precisa das seguintes permissões:

1. **Permissões S3**: Para ler os arquivos JSON do bucket S3.
2. **Permissões DynamoDB**: Para inserir itens na tabela DynamoDB.

Exemplo de política IAM:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "dynamodb:PutItem"
      ],
      "Resource": [
        "arn:aws:s3:::NOME_DO_BUCKET/*",
        "arn:aws:dynamodb:REGIAO:ID_DA_CONTA:table/PedidosTable"
      ]
    }
  ]
}
```

### 4. Exemplo de Arquivo JSON

O arquivo JSON contendo os pedidos deve ter a seguinte estrutura:

``` 
{
  "orderId": "12345",
  "status": "Pendente",
  "customerName": "João Silva",
  "customerEmail": "joao.silva@email.com",
  "totalAmount": 150.75,
  "orderDate": "2024-09-15T18:09:50Z"
}
```

Ou uma lista de pedidos:

```
[
  {
    "orderId": "12345",
    "status": "Pendente",
    "customerName": "João Silva",
    "customerEmail": "joao.silva@email.com",
    "totalAmount": 150.75,
    "orderDate": "2024-09-15T18:09:50Z"
  },
  {
    "orderId": "12346",
    "status": "Concluído",
    "customerName": "Maria Souza",
    "customerEmail": "maria.souza@email.com",
    "totalAmount": 200.50,
    "orderDate": "2024-09-15T19:00:00Z"
  }
]
```

### 5. Logs

Os logs da função Lambda são registrados no Amazon CloudWatch Logs. A função registra o seguinte:

- Informações sobre o evento recebido.
- Informações sobre o sucesso ou falha ao inserir os pedidos no DynamoDB.
- Erros detalhados, caso ocorram durante o processamento.

### Fluxo de Trabalho

1. Um arquivo JSON contendo pedidos é carregado no bucket S3.
2. A notificação do S3 aciona a função Lambda.
3. A Lambda baixa o arquivo, processa os pedidos e insere os dados no DynamoDB.
4. Em caso de sucesso, os logs são registrados no CloudWatch Logs.
5. Se ocorrer um erro, ele será registrado nos logs e uma exceção será lançada.

***
