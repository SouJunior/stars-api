# Documentação do Endpoint /volunteers/

Este documento descreve como utilizar o endpoint `/volunteers/` para listar, filtrar e paginar voluntários.

## Endpoint

`GET /volunteers/`

## Descrição

Retorna uma lista de voluntários cadastrados. A lista pode ser paginada utilizando os parâmetros de consulta (query parameters) `skip` e `limit`, e filtrada por `name` e `jobtitle_id`.

## Parâmetros de Consulta (Query Parameters)

| Parâmetro | Tipo | Padrão | Descrição |
| :--- | :--- | :--- | :--- |
| `skip` | `integer` | `0` | O número de registros para pular (offset). Usado para navegar entre páginas. |
| `limit` | `integer` | `100` | O número máximo de registros a serem retornados em uma única requisição. Determina o tamanho da página. |
| `name` | `string` | `null` | Filtra voluntários pelo nome (busca parcial). |
| `jobtitle_id` | `integer` | `null` | Filtra voluntários pelo ID do cargo (job title). |

## Como Calcular a Paginação

Para implementar uma paginação baseada em páginas (Page 1, Page 2, etc.) no frontend, você pode calcular o valor de `skip` da seguinte forma:

```javascript
const pageSize = 20; // Número de itens por página (limit)
const pageNumber = 1; // Página atual (começando em 1)

const skip = (pageNumber - 1) * pageSize;
const limit = pageSize;

// Exemplo de URL gerada:
// /volunteers/?skip=0&limit=20 (Página 1)
// /volunteers/?skip=20&limit=20 (Página 2)
// /volunteers/?skip=40&limit=20 (Página 3)
```

## Exemplos de Requisição

**1. Paginação simples:**

```http
GET /volunteers/?skip=0&limit=10 HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**2. Filtrando por nome:**

```http
GET /volunteers/?name=Maria HTTP/1.1
Host: localhost:8000
Accept: application/json
```

**3. Filtrando por cargo e paginando:**

```http
GET /volunteers/?jobtitle_id=3&skip=0&limit=20 HTTP/1.1
Host: localhost:8000
Accept: application/json
```

## Exemplo de Resposta

O endpoint retorna um array de objetos JSON representando os voluntários.

```json
[
  {
    "name": "João Silva",
    "linkedin": "https://linkedin.com/in/joaosilva",
    "is_active": true,
    "id": 1,
    "jobtitle_id": 5,
    "masked_email": "j***"
  },
  {
    "name": "Maria Oliveira",
    "linkedin": "https://linkedin.com/in/mariaoliveira",
    "is_active": true,
    "id": 2,
    "jobtitle_id": 3,
    "masked_email": "m***"
  }
]
```

## Notas

- Se `skip` não for fornecido, o padrão é 0.
- Se `limit` não for fornecido, o padrão é 100.
- Se `name` ou `jobtitle_id` não forem fornecidos, o filtro não é aplicado.
- O campo `masked_email` retorna o email ofuscado por questões de privacidade.